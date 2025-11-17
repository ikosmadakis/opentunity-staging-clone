# devices/serializers.py
from rest_framework import serializers
from django.apps import apps
from django.forms.models import model_to_dict

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    # Nice labels for common relations (kept defensive)
    manufacturer = serializers.SerializerMethodField()
    deployment = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    flexibility = serializers.SerializerMethodField()
    communication = serializers.SerializerMethodField()
    communication_protocol = serializers.SerializerMethodField()
    regulation = serializers.SerializerMethodField()
    regulation_response_time_unit = serializers.SerializerMethodField()

    # Specs blocks — always present in the output, null if the model/record is absent
    inverter_specs = serializers.SerializerMethodField()
    bess_specs = serializers.SerializerMethodField()
    electrical_specs = serializers.SerializerMethodField()
    energy_meter_specs = serializers.SerializerMethodField()
    pv_module_specs = serializers.SerializerMethodField()
    scc_specs = serializers.SerializerMethodField()

    # ---- label getters (defensive: return None if relation missing) ----
    def get_manufacturer(self, obj):
        m = getattr(obj, "manufacturer", None)
        return getattr(m, "name", None) if m else None

    def get_deployment(self, obj):
        d = getattr(obj, "deployment", None)
        # adjust to your actual field name; common is "primary_environment"
        return getattr(d, "primary_environment", None) if d else None

    def get_classification(self, obj):
        c = getattr(obj, "classification", None)
        return getattr(c, "type", None) if c else None

    def get_flexibility(self, obj):
        f = getattr(obj, "flexibility", None)
        return getattr(f, "type", None) if f else None

    def get_communication(self, obj):
        c = getattr(obj, "communication", None)
        return getattr(c, "type", None) if c else None

    def get_communication_protocol(self, obj):
        p = getattr(obj, "communication_protocol", None)
        return getattr(p, "type", None) if p else None

    def get_regulation(self, obj):
        r = getattr(obj, "regulation", None)
        return getattr(r, "type", None) if r else None

    def get_regulation_response_time_unit(self, obj):
        u = getattr(obj, "regulation_response_time_unit", None)
        return getattr(u, "symbol", None) if u else None

    # ---- generic helpers for specs ----
    def _serialize_first_spec(self, model_name: str, asset: Asset):
        """
        Try to fetch the first specs row for this asset from devices.<model_name>.
        If the model or row doesn't exist, return None.
        Otherwise return a dict of ALL DB fields for that row.
        """
        try:
            Model = apps.get_model("devices", model_name)
        except Exception:
            Model = None

        if not Model:
            return None

        try:
            spec = Model.objects.filter(asset=asset).first()
        except Exception:
            spec = None

        if not spec:
            return None

        try:
            data = model_to_dict(spec)
            # Drop back-reference to asset to avoid noise/recursion
            data.pop("asset", None)
            return data
        except Exception:
            return None

    def get_inverter_specs(self, obj):
        return self._serialize_first_spec("InverterSpecs", obj)

    def get_bess_specs(self, obj):
        return self._serialize_first_spec("BessSpecs", obj)

    def get_electrical_specs(self, obj):
        return self._serialize_first_spec("ElectricalSpecs", obj)

    def get_energy_meter_specs(self, obj):
        return self._serialize_first_spec("EnergyMeterSpecs", obj)

    def get_pv_module_specs(self, obj):
        return self._serialize_first_spec("PVModuleSpecs", obj)

    def get_scc_specs(self, obj):
        return self._serialize_first_spec("SccSpecs", obj)

    class Meta:
        model = Asset
        fields = "__all__"


class EOAssetIngestSerializer(serializers.Serializer):
    # Top-level mandatory fields
    manufacturer   = serializers.CharField(max_length=255)
    vendor         = serializers.CharField(max_length=255)
    model_name     = serializers.CharField(max_length=255)
    classification = serializers.CharField(max_length=255)
    flexibility    = serializers.CharField(max_length=255)
    regulation     = serializers.CharField(max_length=255)

    # Communication blocks (JSON)
    communication          = serializers.JSONField()
    communication_protocol = serializers.JSONField()

    # Optional spec blocks, required per-class by validation rules
    electrical_specs   = serializers.JSONField(required=False)
    bess_specs         = serializers.JSONField(required=False)
    inverter_specs     = serializers.JSONField(required=False)
    pv_module_specs    = serializers.JSONField(required=False)
    scc_specs          = serializers.JSONField(required=False)
    energy_meter_specs = serializers.JSONField(required=False)
    modbus_register_map = serializers.JSONField(required=False)

    # EO-specific
    eo_organisation = serializers.CharField(max_length=255)
    description     = serializers.CharField(allow_blank=True, required=False)

    # ---- Class-based rules ----
    CLASS_REQUIRED_BLOCKS = {
        # Downstream you can tweak these if you want stricter/looser rules
        "HVAC":             ["electrical_specs"],
        "EVSE":             ["electrical_specs"],
        "WATER HEATER":     ["electrical_specs"],
        "WHITE APPLIANCE":  ["electrical_specs"],
        "ENERGY METER":     ["energy_meter_specs"],
        "BATTERY SYSTEM":   ["bess_specs", "inverter_specs"],
        "PV SYSTEM":        ["pv_module_specs", "inverter_specs"],
        "PV & BAT SYSTEM":  ["pv_module_specs", "bess_specs", "scc_specs", "inverter_specs"],
        "GENSET SYSTEM":    ["electrical_specs"],
        "GENSET & BAT SYSTEM": ["electrical_specs", "bess_specs", "inverter_specs"],
    }

    ENERGY_CLASS_REQUIRED_FOR = {
        "HVAC",
        "EVSE",
        "WATER HEATER",
        "WHITE APPLIANCE",
    }

    MODBUS_PROTOCOLS = {"MODBUS TCP", "MODBUS RTU"}

    def validate(self, data):
        errors = {}

        # --- Normalize classification ---
        raw_class = (data.get("classification") or "").strip()
        classification = raw_class.upper()
        data["classification"] = raw_class  # keep original; use upper for rules

        # --- (a) Classification must be one of the known types ---
        known_classes = set(self.CLASS_REQUIRED_BLOCKS.keys())
        if classification not in known_classes:
            errors["classification"] = [
                f"Unsupported classification '{raw_class}'. "
                f"Expected one of: {sorted(known_classes)}"
            ]

        # --- (b) Class-based mandatory spec blocks ---
        if classification in self.CLASS_REQUIRED_BLOCKS:
            missing_blocks = []
            for block in self.CLASS_REQUIRED_BLOCKS[classification]:
                block_value = data.get(block)
                if block_value is None or block_value == {}:
                    missing_blocks.append(block)
            if missing_blocks:
                errors["class_specs"] = [
                    f"For classification '{raw_class}', the following "
                    f"spec blocks are mandatory but missing or empty: {missing_blocks}"
                ]

        # --- (c) Modbus conditional requirement ---
        proto = data.get("communication_protocol") or {}
        supported = proto.get("supported_com_protocols") or []
        supported_upper = {str(p).upper() for p in supported}
        requires_modbus = bool(self.MODBUS_PROTOCOLS & supported_upper)
        if requires_modbus:
            mr = data.get("modbus_register_map")
            if mr is None or mr == {}:
                errors["modbus_register_map"] = [
                    "modbus_register_map is mandatory when communication_protocol "
                    "includes MODBUS TCP or MODBUS RTU."
                ]

        # --- (d) Energy class mandatory for some classifications ---
        if classification in self.ENERGY_CLASS_REQUIRED_FOR:
            elec = data.get("electrical_specs") or {}
            energy_class = elec.get("energy_class")
            if not energy_class:
                errors["energy_class"] = [
                    "electrical_specs.energy_class is mandatory for "
                    f"classifications: {sorted(self.ENERGY_CLASS_REQUIRED_FOR)}"
                ]

        if errors:
            raise serializers.ValidationError(errors)

        return data
