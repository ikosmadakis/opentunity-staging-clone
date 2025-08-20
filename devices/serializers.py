from rest_framework import serializers
from .models import Asset, InverterSpecs


class InverterSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InverterSpecs
        fields = [
            'max_apparent_feed_in_power_kva',
            'nominal_active_power_kw',
            'peak_active_power_kw',
            'phase_configuration',
            'frequency',
            'standby_power_consumption',
            'voltage_ac_l1_nom',
            'voltage_ac_l2_nom',
            'voltage_ac_l3_nom',
            'current_ac_l1_nom',
            'current_ac_l2_nom',
            'current_ac_l3_nom',
            'nom_dc_voltage_range',
            'max_nominal_dc_current_a',
            'power_factor',
        ]


class AssetSerializer(serializers.ModelSerializer):
    manufacturer = serializers.SerializerMethodField()
    deployment = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    flexibility = serializers.SerializerMethodField()
    communication = serializers.SerializerMethodField()
    communication_protocol = serializers.SerializerMethodField()
    regulation = serializers.SerializerMethodField()
    regulation_response_time_unit = serializers.SerializerMethodField()

    # Nested inverter specs (read-only)
    inverter_specs = InverterSpecsSerializer(read_only=True)

    def get_manufacturer(self, obj):
        return obj.manufacturer.name if obj.manufacturer else None

    def get_deployment(self, obj):
        return obj.deployment.primary_environment if obj.deployment else None

    def get_classification(self, obj):
        return obj.classification.type if obj.classification else None

    def get_flexibility(self, obj):
        return obj.flexibility.type if obj.flexibility else None

    def get_communication(self, obj):
        return obj.communication.type if obj.communication else None

    def get_communication_protocol(self, obj):
        return obj.communication_protocol.type if obj.communication_protocol else None

    def get_regulation(self, obj):
        return obj.regulation.type if obj.regulation else None

    def get_regulation_response_time_unit(self, obj):
        return obj.regulation_response_time_unit.symbol if obj.regulation_response_time_unit else None

    class Meta:
        model = Asset
        fields = '__all__'
