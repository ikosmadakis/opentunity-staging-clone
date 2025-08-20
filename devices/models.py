from django.db import models
from django.contrib.auth.models import User
import secrets

class APIKey(models.Model):
    key = models.CharField(max_length=40, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def generate_key():
        return secrets.token_hex(20)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.key

class BessApplication(models.Model):
    application_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Human-readable name of the BESS application"
    )
    def __str__(self): return self.application_name

class DevicesAttributes(models.Model):
    attribute = models.CharField(max_length=255, unique=True)
    def __str__(self): return self.attribute

class Manufacturer(models.Model):
    name = models.TextField()
    def __str__(self): return self.name

class Deployment(models.Model):
    primary_environment = models.TextField()
    def __str__(self): return self.primary_environment

class Classification(models.Model):
    type = models.TextField()
    def __str__(self): return self.type

class Flexibility(models.Model):
    type = models.TextField()
    def __str__(self): return self.type

class Communication(models.Model):
    type  = models.JSONField()
    specs = models.TextField(blank=True, null=True)
    def __str__(self): return str(self.type)

class CommunicationProtocol(models.Model):
    type  = models.JSONField()
    specs = models.TextField(blank=True, null=True)
    def __str__(self): return str(self.type)

class Regulation(models.Model):
    type  = models.TextField()
    specs = models.TextField(blank=True, null=True)
    def __str__(self): return self.type

class Units(models.Model):
    name   = models.TextField()
    symbol = models.TextField()
    def __str__(self): return self.symbol

class CellType(models.Model):
    name = models.TextField()
    def __str__(self): return self.name

class ContentContributor(models.Model):
    ROLE_CHOICES = [
        ('END_USER',      'End-User / Asset-Owner'),
        ('MANUFACTURER',  'Manufacturer / Economic Operator'),
        ('INDEPENDENT',   'Independent Content Contributor'),
    ]

    user         = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name    = models.CharField(max_length=150, blank=True)
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES)
    eori_number  = models.CharField(
                     max_length=30,
                     blank=True,
                     help_text="Your EU EORI number, e.g. GB123456789000"
                   )
    relation     = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.full_name or self.user.username

class Asset(models.Model):
    opentunity_did            = models.TextField(blank=True, null=True)
    record_contributor        = models.ForeignKey(ContentContributor, on_delete=models.PROTECT)
    record_insertion_date     = models.DateTimeField(auto_now_add=True)
    manufacturer              = models.ForeignKey(Manufacturer, on_delete=models.PROTECT)
    gtin                      = models.CharField(max_length=14, blank=True, null=True)
    model_name                = models.TextField()
    batch_name                = models.TextField(blank=True, null=True)
    serial_number             = models.TextField(verbose_name="Serial Number", blank=True, null=True)
    deployment                = models.ForeignKey(Deployment, on_delete=models.PROTECT, blank=True, null=True)
    classification            = models.ForeignKey(Classification, on_delete=models.PROTECT)
    description               = models.TextField(blank=True, null=True)
    commissioning_date        = models.DateTimeField(blank=True, null=True)
    compliance_checklist      = models.TextField(blank=True, null=True, verbose_name="List of Applicable Directives, Regulations, and Standards")
    release_year              = models.IntegerField(blank=True, null=True)
    flexibility               = models.ForeignKey(Flexibility, on_delete=models.PROTECT)
    communication             = models.ForeignKey(Communication, on_delete=models.PROTECT)
    communication_protocol    = models.ForeignKey(CommunicationProtocol, on_delete=models.PROTECT)
    dacq_actuation            = models.TextField(blank=True, null=True, verbose_name="Data Acquisition Actuation")
    devices_attribute         = models.ForeignKey(DevicesAttributes, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Available Attributes")
    dacq_attributes           = models.TextField(blank=True, null=True, verbose_name="Monitored Attributes")
    control_actuation         = models.TextField(blank=True, null=True, verbose_name="Control Actuation")
    regulation                = models.ForeignKey(Regulation, on_delete=models.PROTECT)
    regulation_response_time_upward   = models.FloatField(blank=True, null=True, default=1 )
    regulation_response_time_downward = models.FloatField(blank=True, null=True, default=1)
    regulation_response_time_unit     = models.ForeignKey(Units, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    regulation_response_time_accuracy = models.FloatField(blank=True, null=True, default=1)
    maximum_upward_regulation         = models.JSONField(blank=True, null=True)
    maximum_downward_regulation       = models.JSONField(blank=True, null=True)
    minimum_regulation_step           = models.JSONField(blank=True, null=True)
    ip_rating                         = models.TextField(blank=True, null=True)
    storage_temperature               = models.JSONField(blank=True, null=True)
    operating_temperature_range       = models.JSONField(blank=True, null=True)
    relative_humidity_range           = models.JSONField(blank=True, null=True)
    dimensions                        = models.JSONField(blank=True, null=True)
    weight                            = models.JSONField(blank=True, null=True)
    form_factor                       = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.model_name} ({self.opentunity_did or self.id})"

class VoltageRegulationOption(models.Model):
    """Lookup table for voltage regulation: Yes / No / Not Sure."""
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Voltage Regulation Option"
        verbose_name_plural = "Voltage Regulation Options"


class ElectricalSpecs(models.Model):
    asset                         = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='elec_specs')
    phase_configuration           = models.IntegerField()
    frequency                     = models.IntegerField()
    voltage_nominal               = models.IntegerField()
    voltage_tolerance_df          = models.FloatField()
    current_nominal_df            = models.FloatField()
    current_min_df                = models.FloatField()
    current_max_df                = models.FloatField()
    inrush_current_max_df         = models.FloatField()
    power_consumption_nominal_df  = models.FloatField()
    power_consumption_max_df      = models.FloatField()
    standby_power_consumption     = models.FloatField()
    power_consumption_units       = models.ForeignKey(Units, on_delete=models.PROTECT)
    voltage_regulation_uf         = models.ForeignKey(VoltageRegulationOption, on_delete=models.PROTECT, verbose_name="Voltage regulation")
    voltage_range_uf              = models.JSONField(blank=True, null=True)
    output_current_nominal_uf     = models.FloatField()
    output_current_max_uf         = models.JSONField(blank=True, null=True)
    power_output_nominal_uf       = models.JSONField(blank=True, null=True)
    power_output_max_uf           = models.JSONField(blank=True, null=True)
    power_factor                  = models.FloatField()

    def __str__(self):
        return f"Electrical Specs for Asset {self.asset.id}"

class BESSSpecs(models.Model):
    asset                        = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='bess_specs')
    bess_application             = models.ForeignKey(BessApplication, on_delete=models.PROTECT, verbose_name="Application", blank=True, null=True)
    cell_type                    = models.ForeignKey(CellType, on_delete=models.PROTECT)
    voltage_nominal              = models.FloatField()
    voltage_range                = models.JSONField(blank=True, null=True)
    capacity                     = models.JSONField(blank=True, null=True)
    maximum_charge_current       = models.FloatField()
    maximum_discharge_current    = models.FloatField()
    cycle_life                   = models.JSONField(blank=True, null=True)
    energy_rating_nominal        = models.FloatField()
    energy_rating_nominal_units  = models.ForeignKey(Units, on_delete=models.PROTECT, related_name='+')
    energy_rating_usable         = models.FloatField()
    energy_rating_usable_units   = models.ForeignKey(Units, on_delete=models.PROTECT, related_name='+')
    c_rate                       = models.TextField()
    round_trip_efficiency        = models.FloatField()
    battery_management_system    = models.JSONField(blank=True, null=True)
    degradation_rate             = models.FloatField()

    def __str__(self):
        return f"BESS Specs for Asset {self.asset.id}"


class InverterSpecs(models.Model):
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE, related_name='inverter_specs')

    # new mandatory integer fields
    max_apparent_feed_in_power_kva = models.IntegerField()
    nominal_active_power_kw        = models.IntegerField()
    peak_active_power_kw           = models.IntegerField()

    # existing/misc
    phase_configuration            = models.IntegerField()
    frequency                      = models.FloatField()
    standby_power_consumption      = models.FloatField()

    # changed: dc current renamed and required
    max_nominal_dc_current_a       = models.FloatField()

    # changed: dc nominal voltage -> JSON
    nom_dc_voltage_range           = models.JSONField()

    # optional AC values (Float, optional)
    nominal_ac_voltage_l1          = models.FloatField(null=True, blank=True)
    nominal_ac_voltage_l2          = models.FloatField(null=True, blank=True)
    nominal_ac_voltage_l3          = models.FloatField(null=True, blank=True)
    nominal_ac_current_l1          = models.FloatField(null=True, blank=True)
    nominal_ac_current_l2          = models.FloatField(null=True, blank=True)
    nominal_ac_current_l3          = models.FloatField(null=True, blank=True)

    power_factor                   = models.FloatField()


class PVModuleSpecs(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='pv_module_specs')

    application = models.TextField(blank=True, null=True)  # optional label you listed
    module_type = models.TextField(blank=True, null=True)
    module_name = models.TextField(blank=True, null=True)

    voc = models.FloatField(blank=True, null=True)    # open-circuit
    isc = models.FloatField(blank=True, null=True)    # short-circuit
    vmpp = models.FloatField(blank=True, null=True)
    impp = models.FloatField(blank=True, null=True)

    temp_coef_pmax = models.FloatField(blank=True, null=True)   # %/°C
    temp_coef_voc  = models.FloatField(blank=True, null=True)   # %/°C or V/°C (you choose)
    temp_coef_isc  = models.FloatField(blank=True, null=True)   # %/°C
    noct = models.FloatField(blank=True, null=True)             # °C
    quantity = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"PV Module Specs for Asset {self.asset_id}"

class SCCSpecs(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='scc_specs')

    model_name = models.TextField(blank=True, null=True)
    voltage_input  = models.FloatField(blank=True, null=True)
    current_input  = models.FloatField(blank=True, null=True)
    voltage_output = models.FloatField(blank=True, null=True)
    current_output = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"SCC Specs for Asset {self.asset_id}"

class EnergyMeterSpecs(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='meter_specs')

    phase_configuration = models.IntegerField(blank=True, null=True)
    frequency = models.IntegerField(blank=True, null=True)
    voltage_nominal = models.IntegerField(blank=True, null=True)
    voltage_tolerance_df = models.FloatField(blank=True, null=True)
    current_nominal_df = models.FloatField(blank=True, null=True)
    current_min_df = models.FloatField(blank=True, null=True)
    current_max_df = models.FloatField(blank=True, null=True)

    standby_power_consumption = models.FloatField(blank=True, null=True)
    power_consumption_nominal_df = models.FloatField(blank=True, null=True)
    power_consumption_units = models.ForeignKey(Units, on_delete=models.PROTECT, blank=True, null=True)

    accuracy_class = models.CharField(max_length=50, blank=True, null=True)  # e.g. Class 0.2S, 0.5, 1

    def __str__(self):
        return f"Energy Meter Specs for Asset {self.asset_id}"

