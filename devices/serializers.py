from rest_framework import serializers
from .models import Asset

class AssetSerializer(serializers.ModelSerializer):
    manufacturer = serializers.SerializerMethodField()
    deployment = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    flexibility = serializers.SerializerMethodField()
    communication = serializers.SerializerMethodField()
    communication_protocol = serializers.SerializerMethodField()
    regulation = serializers.SerializerMethodField()
    regulation_response_time_unit = serializers.SerializerMethodField()
    record_contributor_username = serializers.SerializerMethodField()

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

    def get_record_contributor_username(self, obj):
        # Assuming record_contributor is a FK to a profile with user field
        # Adjust if your model is different!
        if obj.record_contributor and hasattr(obj.record_contributor, 'user'):
            return obj.record_contributor.user.username
        # If it's a direct FK to User, then just:
        # return obj.record_contributor.username
        return None

    class Meta:
        model = Asset
        fields = '__all__'
