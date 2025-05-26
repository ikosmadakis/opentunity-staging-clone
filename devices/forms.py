from django import forms
from .models import (
    Asset,
    DataAcquisitionAndControl,
    ElectricalSpecsDownward,
    ElectricalSpecsUpward,
    ElectricalSpecsBESS,
    EnvironmentalSafetySpecs,
    PhysicalSpecs
)

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ['contributor']

class DataAcquisitionForm(forms.ModelForm):
    class Meta:
        model = DataAcquisitionAndControl
        exclude = []

class ElectricalDownwardForm(forms.ModelForm):
    class Meta:
        model = ElectricalSpecsDownward
        exclude = []

class ElectricalUpwardForm(forms.ModelForm):
    class Meta:
        model = ElectricalSpecsUpward
        exclude = []

class ElectricalBESSForm(forms.ModelForm):
    class Meta:
        model = ElectricalSpecsBESS
        exclude = []

class EnvironmentalForm(forms.ModelForm):
    class Meta:
        model = EnvironmentalSafetySpecs
        exclude = []

class PhysicalSpecsForm(forms.ModelForm):
    class Meta:
        model = PhysicalSpecs
        exclude = []
