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
