from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Asset, ElectricalSpecs, BESSSpecs, ContentContributor

class JSONTextarea(forms.Textarea):
    def format_value(self, value):
        # if it’s “empty” (None or empty dict/list), render as blank
        if value in (None, {}, [], 'null'):
            return ''
        return super().format_value(value)

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ['record_insertion_date', 'record_contributor']
        widgets = {
            'opentunity_did': forms.TextInput(attrs={
                'placeholder': 'e.g. 1234-5678-9012-3456',
            }),
            'gtin': forms.TextInput(attrs={
                'placeholder': 'e.g. 00012345600012',
            }),
            'model_name': forms.TextInput(attrs={
                'placeholder': 'e.g. aroTherm Plus 7kW',
            }),
            'batch_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Batch #2024-05',
            }),
            'serial_number': forms.TextInput(attrs={
                'placeholder': 'e.g. SN123456789XYZ',
            }),
            'commissioning_date': forms.DateInput(attrs={
                'placeholder': 'e.g. 2024-05-18',
                'type': 'date',
            }),
            'release_year': forms.NumberInput(attrs={
                'placeholder': 'e.g. 2024',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Short description of flexibility (optional)',
                'rows': 3,
            }),
            'certifications': JSONTextarea(attrs={
                'placeholder': 'e.g. {"std": ["CE", "IEC 62109", "UL 1741"]}',
                'rows': 3,
            }),
            'dacq_actuation': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"action": "Go into the settings menu, scroll down to Services, '
                    'and then enable the Modbus-TCP service", "set_port": 502, "set_access": "read_only"}'
                ),
                'rows': 3,
            }),
            'dacq_attributes': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"sens_data": {"Active Power": ["W", "SI"], '
                    '"Temperature": ["Celsius", "SI"], "Voltage Line 1": ["V", "SI"]}}'
                ),
                'rows': 3,
            }),
            'control_actuation': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"action": "Go into the settings menu, scroll down to Services, '
                    'and then enable the Modbus-TCP service", "set_port": 502, "set_access": "write_only"}'
                ),
                'rows': 3,
            }),
            'regulation_response_time_accuracy': JSONTextarea(attrs={
                'placeholder': (
                    'e.g.  {"resp_time_accuracy": 5.5, "units": "%"}'
                ),
                'rows': 3,
            }),
            'maximum_upward_regulation': JSONTextarea(attrs={
                'placeholder': (
                    'e.g.  {"power_generation": 5000, "p_unit": "W", "duration":15, "t_unit": "min"}'
                ),
                'rows': 3,
            }),
            'maximum_downward_regulation': JSONTextarea(attrs={
                'placeholder': (
                    'e.g.   {"load_reduction": 5000, "p_unit": "W", "duration":15, "t_unit": "min"}'
                ),
                'rows': 3,
            }),
            'minimum_regulation_step': JSONTextarea(attrs={
                'placeholder': (
                    'e.g.   {"step": 1000, "s_unit": "W", "duration":15, "t_unit": "min"}'
                ),
                'rows': 3,
            }),
            'ip_rating': forms.TextInput(attrs={
                'placeholder': 'e.g. IP65',
            }),
            'form_factor': forms.TextInput(attrs={
                'placeholder': 'e.g. Rack-mounted',
            }),
            'storage_temperature': JSONTextarea(attrs={
                'placeholder': 'e.g. {"min":-20,"max":60,"unit":"°C"}',
                'rows': 2,
            }),
            'operating_temperature_range': JSONTextarea(attrs={
                'placeholder': 'e.g. {"min":-10,"max":50,"unit":"°C"}',
                'rows': 2,
            }),
            'relative_humidity_range': JSONTextarea(attrs={
                'placeholder': 'e.g. {"min":10,"max":90,"unit":"%"}',
                'rows': 2,
            }),
            'dimensions': JSONTextarea(attrs={
                'placeholder': 'e.g. {"length_mm":300,"width_mm":150,"height_mm":200}',
                'rows': 2,
            }),
            'weight': JSONTextarea(attrs={
                'placeholder': 'e.g. {"weight": 5.4, "units": "kg"}',
                'rows': 2,
            }),
        }

        help_texts = {
            'opentunity_did': (
                'A 16-digit unique identifier assigned to each flexibility asset '
                'for tracking, and database management. (optional)'
            ),
            'manufacturer': (
                'The Brand or name of the company that designed and produced the '
                'flexibility asset, helping identify its origin and ensuring proper '
                'warranty, support, and service.'
            ),
            'model_name': (
                'The specific designation and version assigned by the manufacturer '
                'to identify a particular model of the flexible asset, distinguishing '
                'it from other models with different features or capabilities.'
            ),
            'batch_name': (
                'The specific batch name or number assigned by the manufacturer to a '
                'particular batch of a certain flexible asset model, distinguishing it '
                'from other batches. (optional)'
            ),
            'serial_number': (
                'A unique alphanumeric code (or barcode) assigned by the manufacturer '
                'to each individual device, used for identification, warranty tracking, '
                'and service history management. (optional)'
            ),
            'deployment': (
                'The primary environment where the device is installed, such as '
                'residential, commercial, or industrial settings, determining factors '
                'like usage patterns, power requirements, and installation constraints. '
                '(optional)'
            ),
            'classification': (
                'Refers to the category or type of flexibility asset based on its function, '
                'value, or usage—such as HVAC, EV, BESS, Water Heaters, White Appliances, '
                'Smart Devices, Dispatchable Generation units, etc.—which helps in asset '
                'management and classification. (optional)'
            ),
            'description': (
                'A brief flexibility asset description that includes details of energy '
                'consumption or production adjustment in response to market signals or '
                'grid requirements. (optional)'
            ),
            'commissioning_date': (
                'Date the device was put into operation. (optional)'
            ),
            'certifications': (
                'List of certifications and standards that may now or in the future, '
                'directly or indirectly, assess and validate the flexibility potential of '
                'various assets. (optional)'
            ),
            'release_year': (
                'Year of market introduction of the flexible asset. (optional)'
            ),
            'flexibility': (
                'Description of the ability to increase energy generation (e.g. Upward '
                'Flexibility for Generators, Dispatchable RES, etc.) or to reduce energy '
                'consumption (e.g. Downward Flexibility for White Appliances, etc.) to meet '
                'higher-than-expected demand or absorb excess supply. In case of BESS both '
                'types apply.'
            ),
            'communication': (
                'Refers to the physical (and logical) bus system that allows multiple devices '
                'to communicate with each other, including the hardware (wires, connectors, etc.) '
                'and the rules for how data is transmitted over the bus.'
            ),
            'communication_protocol': (
                'Refers to the protocol for communication with the flexibility asset. It defines '
                'how data is formatted, transmitted, and interpreted, ensuring that devices on a '
                'bus system can understand each other.'
            ),
            'dacq_actuation': (
                'To retrieve data of an asset over a bus system (e.g. Ethernet) with a specified '
                'protocol (e.g. Modbus TCP), the process involves several steps. Refers to a DACQ '
                'activation process of a device.'
            ),
            'dacq_attributes': (
                'Collection of information about an asset’s sensing data as well as the unit '
                'and unit system of retrieved data.'
            ),
            'control_actuation': (
                'To control an asset over a bus system (e.g. Ethernet) with a specified protocol '
                '(e.g. Modbus TCP), the process involves several steps. Refers to a control '
                'activation process of a device.'
            ),
            'regulation': (
                'How the asset’s power consumption (output) changes with respect to the input '
                'control signal.'
            ),
            'regulation_response_time_upward': (
                'The time taken by the flexibility asset to react to an upward change in the '
                'control signal and reach a steady-state condition. The accuracy depends on '
                'precision of components.'
            ),
            'regulation_response_time_downward': (
                'The time taken by the flexibility asset to react to a downward change in the '
                'control signal and reach a steady-state condition. The accuracy depends on '
                'precision of components.'
            ),
            'regulation_response_time_unit': (
                'Units of measurement (e.g. “sec”, “min”, etc.).'
            ),
            'regulation_response_time_accuracy': (
                'Proximity of the mean of measurement results to the true value, expressed as a percentage.'
            ),
            'maximum_upward_regulation': (
                'Maximum power generation to meet higher-than-expected demand for a specified amount of time.'
            ),
            'maximum_downward_regulation': (
                'Maximum load reduction to meet lower-than-expected power supply for a specified amount of time.'
            ),
            'minimum_regulation_step': (
                'Minimum power generation or load reduction step to meet demand or supply for a specified amount of time.'
            ),
            'ip_rating': (
                'Ingress Protection Rating: a standard used to define the level of protection a device has against dust and water ingress, '
                'expressed as two digits where the first digit indicates dust protection and the second indicates water resistance. (optional)'
            ),
            'storage_temperature': (
                'Range of temperatures (e.g. –20°C to 60°C) within which a device or component can be safely stored without risk of damage '
                'or degradation to performance or lifespan. (optional)'
            ),
            'operating_temperature_range': (
                'Range of temperatures (e.g. –10°C to 50°C) within which a device or system can function effectively and safely without '
                'performance degradation or risk of failure. (optional)'
            ),
            'relative_humidity_range': (
                'Acceptable range of humidity levels (e.g. 10% to 90%) within which a device can operate or be stored without risk of '
                'corrosion, electrical malfunction, or other environmental damage. (optional)'
            ),
            'dimensions': (
                'Measurable size of a device, typically expressed in length, width, and height (e.g. 300 mm × 150 mm × 200 mm), which impacts '
                'installation, compatibility, and space requirements. (optional)'
            ),
            'weight': (
                'Total mass of the device (e.g. 5 kg), influencing portability, handling, and structural requirements for installation or transportation. (optional)'
            ),
            'form_factor': (
                'Shape, size, unit count, and design configuration (e.g. rack-mounted, wall-mounted, or portable) that determines how the device '
                'fits into its intended system setup. (optional)'
            ),
        }


class ElectricalSpecsForm(forms.ModelForm):
    class Meta:
        model = ElectricalSpecs
        exclude = ['asset']
        widgets = {
            'phase_configuration': forms.NumberInput(attrs={
                'placeholder': 'e.g. 1 or 3',
            }),
            'frequency': forms.NumberInput(attrs={
                'placeholder': 'e.g. 50 or 60',
            }),
            'voltage_nominal': forms.NumberInput(attrs={
                'placeholder': 'e.g. 230',
            }),
            'voltage_tolerance_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 2.5',
            }),
            'current_nominal_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 10.0',
            }),
            'current_min_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 0.5',
            }),
            'current_max_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 20.0',
            }),
            'inrush_current_max_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 100.0',
            }),
            'power_consumption_nominal_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 500.0',
            }),
            'power_consumption_max_df': forms.NumberInput(attrs={
                'placeholder': 'e.g. 600.0',
            }),
            'standby_power_consumption': forms.NumberInput(attrs={
                'placeholder': 'e.g. 35.0',
            }),
            'power_consumption_units': forms.Select(),
            'voltage_regulation_uf': forms.NumberInput(attrs={
                'placeholder': 'e.g. 3.5',
            }),
            'voltage_range_uf': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"min_volt":400.0,"max_volt":480.0,"accuracy_%":1.25}'
                ),
                'rows': 3,
            }),
            'output_current_nominal_uf': forms.NumberInput(attrs={
                'placeholder': 'e.g. 20.0',
            }),
            'output_current_max_uf': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"max_curr":100.0,"max_curr_duration":10,"mcd_unit":"msec"}'
                ),
                'rows': 3,
            }),
            'power_output_nominal_uf': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {'
                    '"genset":{"rated_kVA":5.6,"rated_kW":4.5,"runtime_hours@100%Load":12.5},'
                    '"fuelcell":{"rated_kVA":276,"rated_kW":250,"runtime_hours@100%Load":1000}'
                    '}'
                ),
                'rows': 4,
            }),
            'power_output_max_uf': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {'
                    '"genset":{"max_kVA":6.5,"max_kW":5.2,"runtime_hours_max":12.5},'
                    '"fuelcell":{"max_kVA":276,"max_kW":250,"runtime_hours_max":1000}'
                    '}'
                ),
                'rows': 4,
            }),
            'power_factor': forms.NumberInput(attrs={
                'placeholder': 'e.g. 0.8',
            }),
        }
        help_texts = {
            'phase_configuration': (
                'Refers to the number of electrical phases (e.g., single-phase, three-phase) '
                'in a device’s power supply, affecting performance and compatibility.'
            ),
            'frequency': (
                'The rate at which AC cycles (Hz), determining grid compatibility.'
            ),
            'voltage_nominal': (
                'The standard operating voltage level (e.g., 110V, 220V) for the device.'
            ),
            'voltage_tolerance_df': (
                'Allowable % variation from nominal voltage within which the device operates safely.'
            ),
            'current_nominal_df': (
                'Operating current (A) the device draws under normal conditions.'
            ),
            'current_min_df': (
                'Lowest current level required for the device to operate (A).'
            ),
            'current_max_df': (
                'Highest safe operating current (A) to avoid damage.'
            ),
            'inrush_current_max_df': (
                'Peak surge current (A) drawn when the device first powers on.'
            ),
            'power_consumption_nominal_df': (
                'RMS power (W) consumed during normal operation.'
            ),
            'power_consumption_max_df': (
                'Maximum power (W) consumed during peak operation.'
            ),
            'standby_power_consumption': (
                'Power (W) used while idle but powered on.'
            ),
            'power_consumption_units': (
                'Units of measurement for power (e.g., W, kW).'
            ),
            'voltage_regulation_uf': (
                'Ability to maintain stable output voltage despite input or load changes.'
            ),
            'voltage_range_uf': (
                'Acceptable output voltage limits (e.g., 400V–480V).'
            ),
            'output_current_nominal_uf': (
                'Standard continuous current (A) the system delivers under typical conditions.'
            ),
            'output_current_max_uf': (
                'Peak current (A) the system can safely deliver.'
            ),
            'power_output_nominal_uf': (
                'Rated power (kVA or kW) generated under standard conditions.'
            ),
            'power_output_max_uf': (
                'Maximum power the system can generate during peak demand.'
            ),
            'power_factor': (
                'Ratio of real power (W) to apparent power (VA).'
            ),
        }


class BESSSpecsForm(forms.ModelForm):
    class Meta:
        model = BESSSpecs
        exclude = ['asset']
        widgets = {
            'application': forms.TextInput(attrs={
                'placeholder': 'e.g. Stationary Off-Grid',
            }),
            'cell_type': forms.Select(),
            'voltage_nominal': forms.NumberInput(attrs={
                'placeholder': 'e.g. 51.2',
            }),
            'voltage_range': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"min_volt":44,"max_volt":54}'
                ),
                'rows': 3,
            }),
            'capacity': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"rated_capacity_Ah":100.0,"temp_celsius":20}'
                ),
                'rows': 3,
            }),
            'maximum_charge_current': forms.NumberInput(attrs={
                'placeholder': 'e.g. 70.0',
            }),
            'maximum_discharge_current': forms.NumberInput(attrs={
                'placeholder': 'e.g. 100.0',
            }),
            'cycle_life': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"cycles":6000,"dod_%":90}'
                ),
                'rows': 3,
            }),
            'energy_rating_nominal': forms.NumberInput(attrs={
                'placeholder': 'e.g. 5.12',
            }),
            'energy_rating_nominal_units': forms.Select(),
            'energy_rating_usable': forms.NumberInput(attrs={
                'placeholder': 'e.g. 4.92',
            }),
            'energy_rating_usable_units': forms.Select(),
            'c_rate': forms.TextInput(attrs={
                'placeholder': 'e.g. 1C',
            }),
            'round_trip_efficiency': forms.NumberInput(attrs={
                'placeholder': 'e.g. 91.5',
            }),
            'battery_management_system': JSONTextarea(attrs={
                'placeholder': (
                    'e.g. {"bms":"Varta EMS VS-Pro 2","state_estimation":["SOC","SOH"],'
                    '"monitoring":["Voltage","Current","Temperature"]}'
                ),
                'rows': 4,
            }),
            'degradation_rate': forms.NumberInput(attrs={
                'placeholder': 'e.g. 1.0',
            }),
        }
        help_texts = {
            'application': (
                'Describes the intended use case (e.g. grid stabilization, renewable energy integration, backup power, peak shaving).'
            ),
            'cell_type': (
                'Specific electrochemical composition of the battery cells (e.g. lithium-ion, lead-acid).'
            ),
            'voltage_nominal': (
                'Standard operating voltage of the battery system (e.g. 48V, 400V).'
            ),
            'voltage_range': (
                'Allowable operating voltage range (e.g. 44V–54V).'
            ),
            'capacity': (
                'Rated electrical charge storage capacity (Ah) of the battery at a specified temperature.'
            ),
            'maximum_charge_current': (
                'Highest current (A) a battery can safely accept during charging.'
            ),
            'maximum_discharge_current': (
                'Highest current (A) the battery can deliver during discharge.'
            ),
            'cycle_life': (
                'Total number of charge/discharge cycles before capacity drops below a specified level.'
            ),
            'energy_rating_nominal': (
                'Rated energy storage (kWh) under standard conditions.'
            ),
            'energy_rating_nominal_units': (
                'Units of measurement for nominal energy (e.g. kWh).'
            ),
            'energy_rating_usable': (
                'Usable energy (kWh) deliverable under standard conditions.'
            ),
            'energy_rating_usable_units': (
                'Units of measurement for usable energy (e.g. kWh).'
            ),
            'c_rate': (
                'Charge/discharge rate relative to nominal capacity (e.g. 1C).'
            ),
            'round_trip_efficiency': (
                'Percentage of energy retained after a full charge/discharge cycle.'
            ),
            'battery_management_system': (
                'Details of the battery management system (BMS) and its monitoring features.'
            ),
            'degradation_rate': (
                'Rate at which battery capacity/performance declines over time.'
            ),
        }

class SignupForm(UserCreationForm):
    email       = forms.EmailField(
                      required=True,
                      label="Email address"
                  )
    full_name   = forms.CharField(
                     required=False,
                     max_length=150,
                     label="Full name (optional)"
                  )
    role        = forms.ChoiceField(
                     required=True,
                     choices=ContentContributor.ROLE_CHOICES,
                     label="Your role"
                  )
    eori_number = forms.CharField(
                     required=False,
                     max_length=30,
                     label="EORI number (optional)"
                  )

    class Meta:
        model  = User
        fields = [
            "username",
            "email",
            "full_name",
            "role",
            "eori_number",
            "password1",
            "password2",
        ]
    def clean(self):
        cleaned = super().clean()
        role  = cleaned.get("role", "")
        eori  = cleaned.get("eori_number", "").strip()
        if role == "MANUFACTURER" and not eori:
            self.add_error(
              "eori_number",
              "EORI number is required for Manufacturer / Economic Operator"
            )
        return cleaned

    def save(self, commit=True):
        # Ensure email gets saved onto the User model
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
