from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Asset, ElectricalSpecs, BESSSpecs, ContentContributor, Units
import json

class JSONTextarea(forms.Textarea):
    def format_value(self, value):
        # if it’s “empty” (None or empty dict/list), render as blank
        if value in (None, {}, [], 'null'):
            return ''
        return super().format_value(value)

class AssetForm(forms.ModelForm):
    # ————— Upward fields (as before) —————
    power_generation      = forms.FloatField(label="Power generation", required=False, initial=0.0)
    power_generation_unit = forms.ModelChoiceField(label="Units", queryset=Units.objects.all(), required=False)
    duration              = forms.FloatField(label="Duration", required=False, initial=0.0)
    duration_unit         = forms.ModelChoiceField(label="Units", queryset=Units.objects.all(), required=False)
    # ————— **Downward** fields —————
    load_reduction        = forms.FloatField(label="Load reduction", required=False, initial=0.0)
    load_reduction_unit   = forms.ModelChoiceField(label="Units", queryset=Units.objects.all(), required=False)
    down_duration         = forms.FloatField(label="Duration", required=False, initial=0.0)
    down_duration_unit    = forms.ModelChoiceField(label="Units", queryset=Units.objects.all(), required=False)
    # ————— Minimum regulation step fields —————
    min_step            = forms.FloatField(label="Step", required=False, initial=0.0)
    min_step_unit       = forms.ModelChoiceField(label="Units", queryset=Units.objects.all(), required=False)
    min_duration        = forms.FloatField(label="Duration", required=False, initial=0.0)
    min_duration_unit   = forms.ModelChoiceField(label="Units", queryset=Units.objects.all(), required=False)
    # ————— Storage temperature fields —————
    storage_temp_min   = forms.FloatField(label="Min temperature", required=False, initial=-10)
    storage_temp_max   = forms.FloatField(label="Max temperature", required=False, initial=60)
    storage_temp_unit  = forms.ModelChoiceField(label="Unit", queryset=Units.objects.all(), required=False)
    # ─── Operating temperature range ───
    op_temp_min    = forms.FloatField(label="Min temperature", required=False, initial=-10)
    op_temp_max    = forms.FloatField(label="Max temperature", required=False, initial=45)
    op_temp_unit   = forms.ModelChoiceField(label="Unit", queryset=Units.objects.all(), required=False)
    # ─── Relative humidity range ───
    rh_min         = forms.FloatField(label="Min humidity", required=False, initial=10.0)
    rh_max         = forms.FloatField(label="Max humidity", required=False, initial=95.0)
    rh_unit        = forms.ModelChoiceField(label="Unit", queryset=Units.objects.all(), required=False)
    # ─── Dimensions ───
    dim_length     = forms.FloatField(label="Length (mm)", required=False, widget=forms.NumberInput(attrs={'placeholder': 'e.g. 200'}),)
    dim_width      = forms.FloatField(label="Width (mm)", required=False, widget=forms.NumberInput(attrs={'placeholder': 'e.g. 150'}),)
    dim_height     = forms.FloatField(label="Height (mm)", required=False, widget=forms.NumberInput(attrs={'placeholder': 'e.g. 100'}),)
    # ─── Weight ───
    wt_value       = forms.FloatField(label="Weight", required=False, widget=forms.NumberInput(attrs={'placeholder': 'e.g. 25.5'}),)
    wt_unit        = forms.ModelChoiceField(label="Unit", queryset=Units.objects.all(), required=False)
    class Meta:
        model = Asset
        exclude = ['record_insertion_date', 'record_contributor']
        widgets = {
            'opentunity_did': forms.HiddenInput(),
            # 'opentunity_did': forms.TextInput(attrs={
            #     'placeholder': 'e.g. 1234-5678-9012-3456',
            # }),
            'gtin': forms.TextInput(attrs={
                'placeholder': 'e.g. 00012345600012',
            }),
            'model_name': forms.TextInput(attrs={
                'placeholder': 'e.g. aroTherm Plus 7kW',
            }),
            'batch_name': forms.TextInput(attrs={
                'placeholder': 'e.g. BN123456789XYZ',
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
                'placeholder': 'e.g. A battery energy storage system adjusting its energy output by discharging 5 MW during peak demand and charging 3 MW during surplus supply, responding dynamically to electricity pricing.',
                'rows': 3,
            }),
            'compliance_checklist': forms.Textarea(attrs={
                'placeholder': 'e.g. \n'
                '* Low Voltage Directive (LVD): 2014/35/EU, compliant with harmonized standards EN IEC 60598-1:2021+A1:2022, EN IEC 60598-2-1:2021, EN 62471:2008. \n'
                '* Electromagnetic Compatibility (EMC) Directive: 2014/30/EU, compliant with harmonized standards EN IEC 55015:2019+A11:2020, EN IEC 61547:2009. \n'
                '* Restriction of Hazardous Substances (RoHS) Directive: 2011/65/EU, compliant with harmonized standard EN IEC 63000:2018. \n'
                '* Ecodesign for light sources and separate control gears: (EU) 2019/2020, compliant with relevant parts of EN IEC 62612:2023, EN IEC 62442-1:2020. \n'
                '* Energy labelling of light sources: (EU) 2019/2015, compliant with relevant parts of EN IEC 62612:2023. \n',
                'rows': 4,
            }),
            'dacq_actuation': forms.Textarea(attrs={
                'placeholder': (
                    'e.g. Go into the settings menu, scroll down to Services, '
                    'then enable the Modbus-TCP service and set_port = 502, '
                    'and set_access = "read_only".'
                ),
                'rows': 3,
            }),
            'devices_attribute': forms.Select(attrs={
                'class': 'form-select'
            }),
            'dacq_attributes': forms.Textarea(attrs={
                'placeholder': (
                    'e.g. Active Power (P), in Watt; '
                    'Temperature (T), in Celsius; '
                    'Voltage Line 1 (V_l1), in Volt; etc.'
                ),
                'rows': 3,
            }),
            'control_actuation': forms.Textarea(attrs={
                'placeholder': (
                    'e.g. Go into the settings menu, scroll down to Services, '
                    'then enable the Modbus-TCP service and set_port = 502, '
                    'and set_access = "write_only".'
                ),
                'rows': 3,
            }),
            'maximum_upward_regulation': forms.HiddenInput(),
            'maximum_downward_regulation': forms.HiddenInput(),
            'minimum_regulation_step': forms.HiddenInput(),
            'ip_rating': forms.TextInput(attrs={
                'placeholder': 'e.g. IP65',
            }),
            'form_factor': forms.TextInput(attrs={
                'placeholder': 'e.g. Rack-mounted',
            }),
            'storage_temperature': forms.HiddenInput(),
            'operating_temperature_range': forms.HiddenInput(),
            'relative_humidity_range': forms.HiddenInput(),
            'dimensions': forms.HiddenInput(),
            'weight': forms.HiddenInput(),
        }
        labels = {
            'gtin': 'GTIN',
            'batch_name': 'Batch Name',
            'model_name': 'Model Name',
        }
        help_texts = {
            'opentunity_did': (
                'A 16-digit unique identifier assigned to each flexibility asset '
                'for tracking, and database management. (optional)'
            ),
            'gtin': (
                'The Global Trade Item Number. This is an identification key used '
                'to identify a trade item. (optional)'
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
                'A unique alphanumeric code assigned by the manufacturer to each '
                'individual device, used for identification, warranty tracking, '
                'and service history management. (optional)'
            ),
            'deployment': (
                'The primary environment where the device is or will be installed, such as '
                'residential, commercial, or industrial settings, determining factors '
                'like usage patterns, power requirements, and installation constraints. '
                '(optional)'
            ),
            'classification': (
                'Refers to the category or type of the device (flexibility asset) '
                'based on its function, value, or usage.'
            ),
            'description': (
                'A brief flexibility asset description that includes details of energy '
                'consumption or production adjustment in response to market signals or '
                'grid requirements. (optional)'
            ),
            'commissioning_date': (
                'Date the device was put into operation. (optional)'
            ),
            'compliance_checklist': (
                "Reference to the specific directives or regulations the product complies with: For example, for products sold in the EU, this would include directives like the Low Voltage Directive (LVD), Electromagnetic Compatibility (EMC) Directive, Radio Equipment Directive (RED), etc. The official title and the official journal reference (if applicable) are usually included.\n"
                "Reference to harmonized standards applied (including their reference number and date of issue): These are European standards that provide a presumption of conformity with the essential requirements of the relevant directives.\n"
                "Reference to other national or international standards and technical specifications applied (if any): This could include ISO standards, national standards, or the manufacturer's own specifications. (optional)"
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
                'activation process of a device. (optional)'
            ),
            'dacq_attributes': (
                'Collection of information about an asset’s sensing data as well as the unit '
                'of retrieved data. (optional)'
            ),
            'control_actuation': (
                'To control an asset over a bus system (e.g. Ethernet) with a specified protocol '
                '(e.g. Modbus TCP), the process involves several steps. Refers to a control '
                'activation process of a device. (optional)'
            ),
            'regulation': (
                'How the asset’s power consumption (output) changes with respect to the input '
                'control signal.'
            ),
            'regulation_response_time_upward': (
                'The time taken by the flexibility asset to react to an upward change in the '
                'control signal and reach a steady-state condition. The accuracy depends on '
                'precision of components. Default is 1sec, if this does not apply, leave empty. (optional)'
            ),
            'regulation_response_time_downward': (
                'The time taken by the flexibility asset to react to a downward change in the '
                'control signal and reach a steady-state condition. The accuracy depends on '
                'precision of components. Default is 1sec, if this does not apply, leave empty. (optional)'
            ),
            'regulation_response_time_unit': (
                'Units of measurement (e.g. “sec”, “min”, etc.). Default is sec, if this does not apply, leave "----". (optional)'
            ),
            'regulation_response_time_accuracy': (
                'Proximity of the mean of measurement results to the true value, expressed as a percentage. Default is 1%, if this does not apply, leave empty. (optional)'
            ),
            'maximum_upward_regulation': (
                'Maximum power generation to meet higher-than-expected demand for a specified amount of time. In case of downward flexibility devices, leave 0.0 by default.'
            ),
            'maximum_downward_regulation': (
                'Maximum load reduction to meet lower-than-expected power supply for a specified amount of time. In case of upward flexibility devices, leave 0.0 by default.'
            ),
            'minimum_regulation_step': (
                'Minimum power generation or load reduction step to meet demand or supply for a specified amount of time. In case it does not apply, leave 0.0 default.'
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate upward‐initials
        upd = getattr(self.instance, 'maximum_upward_regulation', None)
        if isinstance(upd, dict):
            self.fields['power_generation'].initial      = upd.get('power_generation')
            self.fields['power_generation_unit'].initial = upd.get('p_unit')
            self.fields['duration'].initial              = upd.get('duration')
            self.fields['duration_unit'].initial         = upd.get('t_unit')

        # Populate downward‐initials
        dwd = getattr(self.instance, 'maximum_downward_regulation', None)
        if isinstance(dwd, dict):
            self.fields['load_reduction'].initial      = dwd.get('load_reduction')
            self.fields['load_reduction_unit'].initial = dwd.get('p_unit')
            self.fields['down_duration'].initial       = dwd.get('duration')
            self.fields['down_duration_unit'].initial  = dwd.get('t_unit')

        # — initialize minimum step fields if editing an instance —
        mrs = getattr(self.instance, 'minimum_regulation_step', None)
        if isinstance(mrs, dict):
            self.fields['min_step'].initial          = mrs.get('step')
            # note the JSON uses key "s_unit" for the unit symbol
            self.fields['min_step_unit'].initial     = mrs.get('s_unit')
            self.fields['min_duration'].initial      = mrs.get('duration')
            self.fields['min_duration_unit'].initial = mrs.get('t_unit')

        # Initialize storage_temperature if editing:
        st = getattr(self.instance, 'storage_temperature', None)
        if isinstance(st, dict):
            self.fields['storage_temp_min'].initial  = st.get('min')
            self.fields['storage_temp_max'].initial  = st.get('max')
            # we store unit symbol in JSON
            # find the Units object matching that symbol
            unit_symbol = st.get('unit')
            if unit_symbol:
                try:
                    self.fields['storage_temp_unit'].initial = Units.objects.get(symbol=unit_symbol)
                except Units.DoesNotExist:
                    pass

        # operating_temperature_range
        op = getattr(self.instance, 'operating_temperature_range', None)
        if isinstance(op, dict):
            self.fields['op_temp_min'].initial  = op.get('min')
            self.fields['op_temp_max'].initial  = op.get('max')
            # find Units object by symbol
            if op.get('unit'):
                try:
                    self.fields['op_temp_unit'].initial = Units.objects.get(symbol=op['unit'])
                except Units.DoesNotExist:
                    pass

        # relative_humidity_range
        rh = getattr(self.instance, 'relative_humidity_range', None)
        if isinstance(rh, dict):
            self.fields['rh_min'].initial = rh.get('min')
            self.fields['rh_max'].initial = rh.get('max')
            if rh.get('unit'):
                try:
                    self.fields['rh_unit'].initial = Units.objects.get(symbol=rh['unit'])
                except Units.DoesNotExist:
                    pass

        # dimensions
        dim = getattr(self.instance, 'dimensions', None)
        if isinstance(dim, dict):
            self.fields['dim_length'].initial = dim.get('length_mm')
            self.fields['dim_width'].initial  = dim.get('width_mm')
            self.fields['dim_height'].initial = dim.get('height_mm')

        # weight
        wt = getattr(self.instance, 'weight', None)
        if isinstance(wt, dict):
            self.fields['wt_value'].initial = wt.get('weight')
            if wt.get('units'):
                try:
                    self.fields['wt_unit'].initial = Units.objects.get(symbol=wt['units'])
                except Units.DoesNotExist:
                    pass

    def clean(self):
        cleaned = super().clean()

        # Pack upward
        pg  = cleaned.get('power_generation')
        pgu = cleaned.get('power_generation_unit')
        du  = cleaned.get('duration')
        duu = cleaned.get('duration_unit')
        if pg is not None or du is not None:
            cleaned['maximum_upward_regulation'] = {
                'power_generation': pg or 0,
                'p_unit':            pgu.symbol if pgu else None,
                'duration':          du or 0,
                't_unit':            duu.symbol if duu else None,
            }

        # Pack downward
        lr   = cleaned.get('load_reduction')
        lru  = cleaned.get('load_reduction_unit')
        dd   = cleaned.get('down_duration')
        ddu  = cleaned.get('down_duration_unit')
        if lr is not None or dd is not None:
            cleaned['maximum_downward_regulation'] = {
                'load_reduction': lr or 0,
                'p_unit':         lru.symbol if lru else None,
                'duration':       dd or 0,
                't_unit':         ddu.symbol if ddu else None,
            }

        # — pack minimum regulation step —
        step    = cleaned.get('min_step')
        step_u  = cleaned.get('min_step_unit')
        dur     = cleaned.get('min_duration')
        dur_u   = cleaned.get('min_duration_unit')
        if step is not None or dur is not None:
            cleaned['minimum_regulation_step'] = {
                'step':     step or 0,
                's_unit':   step_u.symbol if step_u else None,
                'duration': dur or 0,
                't_unit':   dur_u.symbol if dur_u else None,
            }

        # Pack storage_temperature:
        mn   = cleaned.get('storage_temp_min')
        mx   = cleaned.get('storage_temp_max')
        ut   = cleaned.get('storage_temp_unit')
        if mn is not None or mx is not None:
            cleaned['storage_temperature'] = {
                'min':  mn if mn is not None else 0,
                'max':  mx if mx is not None else 0,
                'unit': ut.symbol if ut else None,
            }

        # pack operating_temperature_range
        mn, mx, ut = (
            cleaned.get('op_temp_min'),
            cleaned.get('op_temp_max'),
            cleaned.get('op_temp_unit'),
        )
        if mn is not None or mx is not None:
            cleaned['operating_temperature_range'] = {
                'min':  mn if mn is not None else 0,
                'max':  mx if mx is not None else 0,
                'unit': ut.symbol if ut else None,
            }

        # pack relative_humidity_range
        rmin, rmax, runit = (
            cleaned.get('rh_min'),
            cleaned.get('rh_max'),
            cleaned.get('rh_unit'),
        )
        if rmin is not None or rmax is not None:
            cleaned['relative_humidity_range'] = {
                'min':  rmin if rmin is not None else 0,
                'max':  rmax if rmax is not None else 0,
                'unit': runit.symbol if runit else None,
            }

        # pack dimensions
        l, w, h = (
            cleaned.get('dim_length'),
            cleaned.get('dim_width'),
            cleaned.get('dim_height'),
        )
        if l is not None or w is not None or h is not None:
            cleaned['dimensions'] = {
                'length_mm': l if l is not None else 0,
                'width_mm':  w if w is not None else 0,
                'height_mm': h if h is not None else 0,
            }

        # pack weight
        val, vunit = (
            cleaned.get('wt_value'),
            cleaned.get('wt_unit'),
        )
        if val is not None:
            cleaned['weight'] = {
                'weight': val,
                'units':  vunit.symbol if vunit else None,
            }

        return cleaned


class ElectricalSpecsForm(forms.ModelForm):
    # ─── Discrete fields for voltage_range_uf ───
    voltage_min = forms.FloatField(label="Min (V)", required=False, initial=0.0)
    voltage_max = forms.FloatField(label="Max (V)", required=False, initial=0.0)
    voltage_acc = forms.FloatField(label="Accuracy (%)", required=False, initial=0.0)

    # ─── Override existing nominal field to set placeholder, help_text, initial ───
    output_current_nominal_uf = forms.FloatField(
        label="Output current nominal",
        required=False,
        initial=0.0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 20.0'}),
        help_text=(
            "Standard continuous current (A) the system delivers under typical "
            "conditions. In case of downward flexibility devices leave 0.0 default."
        )
    )

    # ─── Discrete fields for output_current_max_uf ───
    output_max_curr          = forms.FloatField(label="Max current (A)", required=False, initial=0.0)
    output_max_curr_duration = forms.FloatField(label="Duration (sec)", required=False, initial=0.0)

    # ─── power_output_nominal_uf unpacked ───
    pow_nom_gen_kva   = forms.FloatField(label="Generation rated (kVA)", required=False, initial=0.0)
    pow_nom_gen_kw    = forms.FloatField(label="Generation rated (kW)", required=False, initial=0.0)
    pow_nom_runtime_h = forms.FloatField(label="Generation runtime @100%Load (hours)", required=False, initial=0.0)

    # ─── power_output_max_uf unpacked ───
    pow_max_gen_kva   = forms.FloatField(label="Generation max (kVA)", required=False, initial=0.0)
    pow_max_gen_kw    = forms.FloatField(label="Generation max (kW)", required=False, initial=0.0)
    pow_max_runtime_h = forms.FloatField(label="Generation runtime (hours)", required=False, initial=0.0)

    class Meta:
        model   = ElectricalSpecs
        exclude = ['asset']
        widgets = {
            'phase_configuration':    forms.NumberInput(attrs={'placeholder': 'e.g. 1 or 3'}),
            'frequency':              forms.NumberInput(attrs={'placeholder': 'e.g. 50 or 60'}),
            'voltage_nominal':        forms.NumberInput(attrs={'placeholder': 'e.g. 230'}),
            'voltage_tolerance_df':   forms.NumberInput(attrs={'placeholder': 'e.g. 2.5'}),
            'current_nominal_df':     forms.NumberInput(attrs={'placeholder': 'e.g. 10.0'}),
            'current_min_df':         forms.NumberInput(attrs={'placeholder': 'e.g. 0.5'}),
            'current_max_df':         forms.NumberInput(attrs={'placeholder': 'e.g. 20.0'}),
            'inrush_current_max_df':  forms.NumberInput(attrs={'placeholder': 'e.g. 100.0'}),
            'power_consumption_nominal_df': forms.NumberInput(attrs={'placeholder': 'e.g. 500.0'}),
            'power_consumption_max_df':     forms.NumberInput(attrs={'placeholder': 'e.g. 600.0'}),
            'standby_power_consumption':    forms.NumberInput(attrs={'placeholder': 'e.g. 35.0'}),
            'power_consumption_units': forms.Select(),
            'voltage_regulation_uf':  forms.Select(),
            'voltage_range_uf':       forms.HiddenInput(),
            'output_current_max_uf':  forms.HiddenInput(),
            'power_output_nominal_uf': forms.HiddenInput(),
            'power_output_max_uf':    forms.HiddenInput(),
            'power_factor':           forms.NumberInput(attrs={'placeholder': 'e.g. 0.8'}),
        }
        labels = {
            'voltage_tolerance_df': 'Voltage tolerance',
            'current_nominal_df':   'Current nominal',
            'current_min_df':       'Current min',
            'current_max_df':       'Current max',
            'inrush_current_max_df':'Inrush current',
            'power_consumption_nominal_df': 'Power consumption nominal',
            'power_consumption_max_df':     'Power consumption max',
        }
        help_texts = {
            'phase_configuration': (
                'Refers to number of electrical phases (e.g., single-phase, three-phase).'
            ),
            'frequency': (
                'AC cycle rate (Hz), determining grid compatibility.'
            ),
            'voltage_nominal': (
                'Standard operating voltage (e.g., 110V, 220V).'
            ),
            'voltage_tolerance_df': (
                'Allowable % variation from nominal voltage.'
            ),
            'current_nominal_df': (
                'Operating current (A) under normal conditions.'
            ),
            'current_min_df': (
                'Lowest safe operating current (A).'
            ),
            'current_max_df': (
                'Highest safe operating current (A).'
            ),
            'inrush_current_max_df': (
                'Peak surge current (A) on power-up.'
            ),
            'power_consumption_nominal_df': (
                'RMS power consumed during normal operation.'
            ),
            'power_consumption_max_df': (
                'Max power consumed at peak load.'
            ),
            'standby_power_consumption': (
                'Power used while idle but powered on.'
            ),
            'power_consumption_units': (
                'Units of measurement for power (e.g., W, kW).'
            ),
            'voltage_regulation_uf': (
                'Ability to maintain stable voltage despite variations.'
            ),
            'voltage_range_uf': (
                'Acceptable output voltage limits (e.g., 400V–480V). In case of downward flexibility devices leave 0.0 default.'
            ),
            'output_current_max_uf': (
                'Peak current (A) the system can safely deliver. In case of downward flexibility devices leave 0.0 default.'
            ),
            'power_output_nominal_uf': (
                'Rated power (kVA or kW) under standard conditions.'
            ),
            'power_output_max_uf': (
                'Max power the system can generate at peak demand.'
            ),
            'power_factor': (
                'Ratio of real power (W) to apparent power (VA).'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ─── Unpack voltage_range_uf JSON ───
        vr = getattr(self.instance, 'voltage_range_uf', None)
        if isinstance(vr, dict):
            self.fields['voltage_min'].initial = vr.get('min_volt',    0.0)
            self.fields['voltage_max'].initial = vr.get('max_volt',    0.0)
            self.fields['voltage_acc'].initial = vr.get('accuracy_%',  0.0)

        # ─── Unpack output_current_max_uf JSON ───
        js = getattr(self.instance, 'output_current_max_uf', None)
        if isinstance(js, dict):
            self.fields['output_max_curr'].initial          = js.get('max_curr',          0.0)
            self.fields['output_max_curr_duration'].initial = js.get('max_curr_duration', 0.0)
        # ─── unpack power_output_nominal_uf ───
        pn = getattr(self.instance, 'power_output_nominal_uf', None)
        if isinstance(pn, dict):
            genset = pn.get('genset', {})
            self.fields['pow_nom_gen_kva'].initial   = genset.get('rated_kVA', 0.0)
            self.fields['pow_nom_gen_kw'].initial    = genset.get('rated_kW',  0.0)
            self.fields['pow_nom_runtime_h'].initial = genset.get('runtime_hours@100%Load', 0.0)

        # ─── unpack power_output_max_uf ───
        px = getattr(self.instance, 'power_output_max_uf', None)
        if isinstance(px, dict):
            genset = px.get('genset', {})
            self.fields['pow_max_gen_kva'].initial   = genset.get('max_kVA',          0.0)
            self.fields['pow_max_gen_kw'].initial    = genset.get('max_kW',           0.0)
            self.fields['pow_max_runtime_h'].initial = genset.get('runtime_hours_max', 0.0)

    def clean(self):
        cleaned = super().clean()

        # ─── Repack voltage_range_uf JSON ───
        vmin = cleaned.get('voltage_min')
        vmax = cleaned.get('voltage_max')
        vacc = cleaned.get('voltage_acc')
        if vmin is not None or vmax is not None or vacc is not None:
            cleaned['voltage_range_uf'] = {
                'min_volt':    vmin if vmin is not None else 0.0,
                'max_volt':    vmax if vmax is not None else 0.0,
                'accuracy_%':  vacc if vacc is not None else 0.0,
            }

        # ─── Repack output_current_max_uf JSON ───
        mc   = cleaned.get('output_max_curr')
        mcd  = cleaned.get('output_max_curr_duration')
        if mc is not None or mcd is not None:
            cleaned['output_current_max_uf'] = {
                'max_curr':          mc  or 0.0,
                'max_curr_duration': mcd or 0.0,
            }

        # ─── repack power_output_nominal_uf ───
        nom = {
            'rated_kVA':                cleaned.get('pow_nom_gen_kva')   or 0.0,
            'rated_kW':                 cleaned.get('pow_nom_gen_kw')    or 0.0,
            'runtime_hours@100%Load':   cleaned.get('pow_nom_runtime_h') or 0.0,
        }
        cleaned['power_output_nominal_uf'] = {'genset': nom}

        # ─── repack power_output_max_uf ───
        mx = {
            'max_kVA':             cleaned.get('pow_max_gen_kva')   or 0.0,
            'max_kW':              cleaned.get('pow_max_gen_kw')    or 0.0,
            'runtime_hours_max':   cleaned.get('pow_max_runtime_h') or 0.0,
        }
        cleaned['power_output_max_uf'] = {'genset': mx}

        return cleaned



class BESSSpecsForm(forms.ModelForm):
    # ─── Discrete inputs in place of the JSONFields ───
    voltage_min = forms.FloatField(
        label="Min voltage (V)",
        required=False,
        initial=0.0,
    )
    voltage_max = forms.FloatField(
        label="Max voltage (V)",
        required=False,
        initial=0.0,
    )
    capacity_rated_Ah = forms.FloatField(
        label="Rated capacity (Ah)",
        required=False,
        initial=200,
    )
    capacity_temp_celsius = forms.FloatField(
        label="Temperature (°C)",
        required=False,
        initial=25,
    )
    cycle_count          = forms.IntegerField(
        label="Cycles",
        required=False,
        initial=3000,
        help_text="Total number of charge/discharge cycles before capacity drops below a specified level."
    )
    depth_of_discharge   = forms.FloatField(
        label="Depth of Discharge (%)",
        required=False,
        initial=90.0,
        help_text="Percentage of depth-of-discharge at which cycle life is rated."
    )
    bms = forms.CharField(
        label="BMS",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. Varta EMS VS-Pro2"
        }),
        help_text="Type or model of BMS to control the battery, based on method and measurements."
    )
    state_estimation = forms.CharField(
        label="State_estimation",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. SOC, SOH"
        })
    )
    monitoring = forms.CharField(
        label="Attribute Monitoring",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. Voltage, Current, Temperature"
        })
    )

    class Meta:
        model = BESSSpecs
        exclude = ['asset']
        widgets = {
            'cell_type': forms.Select(),
            'voltage_nominal': forms.NumberInput(attrs={
                'placeholder': 'e.g. 51.2',
            }),
            'voltage_range': forms.HiddenInput(),
            'capacity': forms.HiddenInput(),
            'maximum_charge_current': forms.NumberInput(attrs={
                'placeholder': 'e.g. 70.0',
            }),
            'maximum_discharge_current': forms.NumberInput(attrs={
                'placeholder': 'e.g. 100.0',
            }),
            'cycle_life': forms.HiddenInput(),
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
            'battery_management_system': forms.HiddenInput(),
            'degradation_rate': forms.NumberInput(attrs={
                'placeholder': 'e.g. 1.0',
            }),
        }
        help_texts = {
            'bess_application': (
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vr = getattr(self.instance, 'voltage_range', None)
        if isinstance(vr, dict):
            self.fields['voltage_min'].initial = vr.get('min_volt', 0.0)
            self.fields['voltage_max'].initial = vr.get('max_volt', 0.0)
        cap = getattr(self.instance, 'capacity', None)
        if isinstance(cap, dict):
            self.fields['capacity_rated_Ah'].initial   = cap.get('rated_capacity_Ah', 0.0)
            self.fields['capacity_temp_celsius'].initial = cap.get('temp_celsius', 0.0)
        cl = getattr(self.instance, 'cycle_life', None)
        if isinstance(cl, dict):
            self.fields['cycle_count'].initial        = cl.get('cycles', 0)
            self.fields['depth_of_discharge'].initial = cl.get('dod_%', 0.0)
        raw = getattr(self.instance, "battery_management_system", None)
        if isinstance(raw, dict):
            self.fields["bms"].initial              = raw.get("bms", "")
            # store lists as comma-joined strings
            self.fields["state_estimation"].initial = ", ".join(raw.get("state_estimation", []))
            self.fields["monitoring"].initial       = ", ".join(raw.get("monitoring", []))


    def clean(self):
        cleaned = super().clean()
        vmin = cleaned.get('voltage_min')
        vmax = cleaned.get('voltage_max')
        if vmin is not None or vmax is not None:
            cleaned['voltage_range'] = {
                'min_volt': vmin  or 0.0,
                'max_volt': vmax  or 0.0,
            }

        rcap = cleaned.get('capacity_rated_Ah')
        tcel = cleaned.get('capacity_temp_celsius')
        if rcap is not None or tcel is not None:
            cleaned['capacity'] = {
                'rated_capacity_Ah': rcap         or 0.0,
                'temp_celsius':      tcel        or 0.0,
            }

        cc  = cleaned.get('cycle_count')
        dod = cleaned.get('depth_of_discharge')
        if cc is not None or dod is not None:
            cleaned['cycle_life'] = {
                'cycles':   cc  or 0,
                'dod_%':    dod or 0.0,
            }

        bms   = cleaned.get("bms", "").strip()
        se    = cleaned.get("state_estimation", "")
        mon   = cleaned.get("monitoring", "")

        # split CSV back into lists
        se_list  = [s.strip() for s in se.split(",") if s.strip()]
        mon_list = [m.strip() for m in mon.split(",") if m.strip()]

        # always write back a dict
        cleaned["battery_management_system"] = {
            "bms":               bms,
            "state_estimation":  se_list,
            "monitoring":        mon_list,
        }

        return cleaned

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
