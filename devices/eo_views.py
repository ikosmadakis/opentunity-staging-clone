from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from devices.auth import APIKeyAuthentication
from devices.models import (
    Asset,
    Manufacturer,
    Classification,
    Flexibility,
    Communication,
    CommunicationProtocol,
    Regulation,
    ContentContributor,
    ElectricalSpecs,
    BESSSpecs,
    InverterSpecs,
    PVModuleSpecs,
    SCCSpecs,
    EnergyMeterSpecs,
    Units,
    VoltageRegulationOption,
)
from devices.serializers import EOAssetIngestSerializer


class EOAssetIngestView(APIView):
    """
    POST /api/eo/assets/

    Create a new Asset (and its specs) from an Economic Operator payload.
    Auth: Api-Key (MANUFACTURER role required).
    """
    authentication_classes = [APIKeyAuthentication]
    
    # --- helper to resolve Units FK from id or symbol/name ---
    def _resolve_units_id(self, value, default_symbol="W"):
        """
        Accepts:
          - int  -> primary key of Units
          - str  -> tries Units.symbol / Units.name (case-insensitive)
          - None -> use default_symbol (e.g. 'W')

        Returns a valid Units.pk, or raises ValidationError if none can be found.
        """
        # If EO already sends an integer that matches an existing Units row
        if isinstance(value, int):
            if Units.objects.filter(pk=value).exists():
                return value

        # If EO sends a string symbol/name (e.g. "W")
        if isinstance(value, str) and value.strip():
            s = value.strip()
            u = (Units.objects.filter(symbol__iexact=s).first()
                 or Units.objects.filter(name__iexact=s).first())
            if u:
                return u.pk

        # Fallback: try default symbol (e.g. "W")
        if default_symbol:
            u = (Units.objects.filter(symbol__iexact=default_symbol).first()
                 or Units.objects.filter(name__iexact=default_symbol).first())
            if u:
                return u.pk

        # Absolute last resort: first Units row
        u = Units.objects.first()
        if u:
            return u.pk

        # If we reach here, Units table is empty -> configuration error
        raise ValidationError({
            "electrical_specs": [
                "Cannot resolve power_consumption_units: no matching Units found "
                "and no default available."
            ]
        })

    def post(self, request, *args, **kwargs):
        # Keep a copy of the raw JSON so we don't lose keys
        raw_payload = request.data

        # --- 1) Auth & role gate ---
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return Response({"detail": "Authentication required."},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            contributor = ContentContributor.objects.get(user=user)
        except ContentContributor.DoesNotExist:
            return Response({"detail": "Content contributor profile not found."},
                            status=status.HTTP_403_FORBIDDEN)

        if contributor.role != "MANUFACTURER":
            return Response(
                {"detail": "Only MANUFACTURER / Economic Operator contributors "
                           "may use this EO ingestion endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # --- 2) Validate payload shape & rules ---
        serializer = EOAssetIngestSerializer(data=raw_payload)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # --- 3) Create asset + specs atomically ---
        with transaction.atomic():
            asset = self._create_asset_and_specs(contributor, data, raw_payload)

        return Response(
            {
                "id": asset.id,
                "opentunity_did": asset.opentunity_did,
                "message": "Asset created via EO API ingestion.",
            },
            status=status.HTTP_201_CREATED,
        )

    # -----------------------------------------------------------
    # Helper: create Asset + all dependent specs given validated data
    # -----------------------------------------------------------
    def _create_asset_and_specs(
        self,
        contributor: ContentContributor,
        data: dict,
        raw_payload: dict,
    ) -> Asset:
        # --- FKs from basic strings / JSON blocks ---
        manufacturer, _ = Manufacturer.objects.get_or_create(
            name=data["manufacturer"].strip()
        )

        classification, _ = Classification.objects.get_or_create(
            type=data["classification"].strip()
        )

        flexibility, _ = Flexibility.objects.get_or_create(
            type=data["flexibility"].strip()
        )

        regulation, _ = Regulation.objects.get_or_create(
            type=data["regulation"].strip()
        )

        communication, _ = Communication.objects.get_or_create(
            type=data["communication"]
        )

        communication_protocol, _ = CommunicationProtocol.objects.get_or_create(
            type=data["communication_protocol"]
        )

        # --- description enrichment (rule e) ---
        base_desc = (data.get("description") or "").strip()
        eo_org = (data.get("eo_organisation") or "").strip()

        extra_lines = ["created via EO API ingestion"]
        if eo_org:
            extra_lines.append(f"EO organisation: {eo_org}")

        combined_desc = base_desc
        if extra_lines:
            suffix = "\n\n" + "\n".join(extra_lines)
            combined_desc = (combined_desc + suffix) if combined_desc else suffix.lstrip()

        # --- Asset creation (core fields) ---
        asset = Asset.objects.create(
            record_contributor=contributor,
            manufacturer=manufacturer,
            classification=classification,
            flexibility=flexibility,
            communication=communication,
            communication_protocol=communication_protocol,
            regulation=regulation,
            model_name=data["model_name"].strip(),
            vendor=(data.get("vendor") or "").strip() or None,
            description=combined_desc,
            record_insertion_date=timezone.now(),
        )

        # --- Optional asset-level fields copied from raw EO JSON ---
        # Text-like fields
        text_fields = [
            "dacq_actuation",
            "dacq_attributes",
            "control_actuation",
            "form_factor",
            "dpp_url",
            "gtin",
            "eprel_url",
            "compliance_checklist",
        ]
        for field in text_fields:
            if field in raw_payload and raw_payload[field] not in (None, ""):
                setattr(asset, field, raw_payload[field])

        # Floats
        float_fields = [
            "regulation_response_time_upward",
            "regulation_response_time_downward",
            "regulation_response_time_accuracy",
        ]
        for field in float_fields:
            if field in raw_payload and raw_payload[field] is not None:
                setattr(asset, field, raw_payload[field])

        # release_year (int-ish)
        if "release_year" in raw_payload and raw_payload["release_year"] not in (None, ""):
            asset.release_year = raw_payload["release_year"]

        # JSON-like fields
        json_fields = [
            "maximum_upward_regulation",
            "maximum_downward_regulation",
            "minimum_regulation_step",
            "ip_rating",
            "storage_temperature",
            "operating_temperature_range",
            "relative_humidity_range",
            "dimensions",
            "weight",
        ]
        for field in json_fields:
            if field in raw_payload and raw_payload[field] is not None:
                setattr(asset, field, raw_payload[field])

        # regulation_response_time_unit is a FK to Units; we expect an ID
        rrt_unit_val = raw_payload.get("regulation_response_time_unit")
        if rrt_unit_val is not None:
            # Expecting integer ID from EO; map via *_id
            asset.regulation_response_time_unit_id = rrt_unit_val

        # Persist asset-level extras
        asset.save()

        # ------------------------------------------------------------------
        # Specs creation based on what the EO actually sent
        # ------------------------------------------------------------------
        def _clean_payload(payload: dict) -> dict:
            payload = dict(payload or {})
            payload.pop("id", None)
            payload.pop("asset", None)
            return payload

        # === ElectricalSpecs ===
        # ElectricalSpecs – use RAW payload so we preserve EO’s extra fields
        elec_payload = dict(raw_payload.get("electrical_specs") or {})
        if elec_payload:
            # Remove internal fields that must NOT be passed through
            elec_payload.pop("id", None)
            elec_payload.pop("asset", None)

            # Take a shallow copy to build kwargs safely
            elec_kwargs = dict(elec_payload)

            # --- voltage_regulation_uf (FK to VoltageRegulationOption) ---
            vro = elec_kwargs.pop("voltage_regulation_uf", None)
            if vro is not None:
                if isinstance(vro, int):
                    # EO sends a raw FK id
                    elec_kwargs["voltage_regulation_uf_id"] = vro
                elif isinstance(vro, str) and vro.strip():
                    opt = VoltageRegulationOption.objects.filter(
                        name__iexact=vro.strip()
                    ).first()
                    if opt:
                        elec_kwargs["voltage_regulation_uf"] = opt
                    # else: leave unset; model default / admin can fix later

            # --- power_consumption_units (FK to Units) ---
            # EO can send:
            #   "power_consumption_units": 6     -> Units pk
            #   "power_consumption_units": "W"   -> Units.symbol/name
            pcu_raw = elec_kwargs.pop("power_consumption_units", None)
            pcu_id = self._resolve_units_id(pcu_raw, default_symbol="W")
            elec_kwargs["power_consumption_units_id"] = pcu_id

            # Finally create the ElectricalSpecs row
            ElectricalSpecs.objects.create(
                asset=asset,
                **elec_kwargs,
            )


        # === BESS specs ===
        bess_payload = raw_payload.get("bess_specs") or {}
        if bess_payload:
            BESSSpecs.objects.create(
                asset=asset,
                voltage_nominal=bess_payload.get("voltage_nominal"),
                maximum_charge_current=bess_payload.get("maximum_charge_current"),
                maximum_discharge_current=bess_payload.get("maximum_discharge_current"),
                energy_rating_nominal=bess_payload.get("energy_rating_nominal"),
                energy_rating_usable=bess_payload.get("energy_rating_usable"),
                round_trip_efficiency=bess_payload.get("round_trip_efficiency"),

                # Units / FK IDs:
                energy_rating_nominal_units_id=bess_payload.get("energy_rating_nominal_units"),
                energy_rating_usable_units_id=bess_payload.get("energy_rating_usable_units"),
                cell_type_id=bess_payload.get("cell_type"),
                bess_application_id=bess_payload.get("bess_application"),

                # JSON blocks:
                voltage_range=bess_payload.get("voltage_range"),
                capacity=bess_payload.get("capacity"),
                cycle_life=bess_payload.get("cycle_life"),
                battery_management_system=bess_payload.get("battery_management_system"),
                degradation_rate=bess_payload.get("degradation_rate"),
            )

        # === Inverter specs ===
        inv_payload = raw_payload.get("inverter_specs") or {}
        if inv_payload:
            InverterSpecs.objects.create(
                asset=asset,
                **_clean_payload(inv_payload),
            )

        # === PV module specs ===
        pv_payload = raw_payload.get("pv_module_specs") or {}
        if pv_payload:
            PVModuleSpecs.objects.create(
                asset=asset,
                **_clean_payload(pv_payload),
            )

        # === SCC specs ===
        scc_payload = raw_payload.get("scc_specs") or {}
        if scc_payload:
            SCCSpecs.objects.create(
                asset=asset,
                **_clean_payload(scc_payload),
            )

        # === Energy meter specs ===
        meter_payload = raw_payload.get("energy_meter_specs") or {}
        if meter_payload:
            EnergyMeterSpecs.objects.create(
                asset=asset,
                **_clean_payload(meter_payload),
            )

        # === Modbus register map stored directly on Asset ===
        modbus_payload = raw_payload.get("modbus_register_map")
        if modbus_payload:
            asset.modbus_register_map = modbus_payload
            asset.save(update_fields=["modbus_register_map"])

        return asset
