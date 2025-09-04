from django.db import transaction
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .utils import send_activation_email
import qrcode, io, os
from PIL import Image
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from devices.forms import ProfileForm, SignupForm, AssetForm, ElectricalSpecsForm, BESSSpecsForm, InverterSpecsForm, PVModuleSpecsForm, SCCSpecsForm, EnergyMeterSpecsForm
from devices.models import ContentContributor, Asset, APIKey, CommunicationProtocol,  ElectricalSpecs, BESSSpecs, InverterSpecs, PVModuleSpecs, SCCSpecs, EnergyMeterSpecs
from devices.serializers import AssetSerializer

CLASS_TO_FORMS = {
    'HVAC': {
        'title': 'HVAC Specs',
        'forms': ['elec'],  # reuse ElectricalSpecsForm but you’ll hide unused fields in template
    },
    'EVSE': {
        'title': 'EVSE Specs',
        'forms': ['elec'],
    },
    'WATER HEATER': {
        'title': 'Water Heater Specs',
        'forms': ['elec'],
    },
    'WHITE APPLIANCE': {
        'title': 'White Appliance Specs',
        'forms': ['elec'],
    },
    'ENERGY METER': {
        'title': 'Energy Meter Specs',
        'forms': ['meter'],
    },
    'BATTERY SYSTEM': {
        'title': 'BESS + Inverter Specs',
        'forms': ['bess', 'inv'],
    },
    'PV SYSTEM': {
        'title': 'PV Module + Inverter Specs',
        'forms': ['pv', 'inv'],
    },
    'GENSET SYSTEM': {
        'title': 'Genset Electrical Specs',
        'forms': ['elec'],   # your existing ElectricalSpecs already fits genset fields
    },
    'PV & BAT SYSTEM': {
        'title': 'PV + BESS + SCC + Inverter Specs',
        'forms': ['pv', 'bess', 'scc', 'inv'],
    },
    'GENSET & BAT SYSTEM': {
        'title': 'Genset + BESS + Inverter Specs',
        'forms': ['elec', 'bess', 'inv'],
    },
}

SPEC_FORMS = {
    'elec':  (ElectricalSpecs, ElectricalSpecsForm,  'elec_specs',      'elec'),
    'bess':  (BESSSpecs,       BESSSpecsForm,        'bess_specs',      'bess'),
    'inv':   (InverterSpecs,   InverterSpecsForm,    'inverter_specs',  'inv'),
    'pv':    (PVModuleSpecs,   PVModuleSpecsForm,    'pv_module_specs', 'pv'),
    'scc':   (SCCSpecs,        SCCSpecsForm,         'scc_specs',       'scc'),
    'meter': (EnergyMeterSpecs,EnergyMeterSpecsForm, 'meter_specs',     'meter'),
}

def _get_instance(asset, attr_name):
    inst = getattr(asset, attr_name, None)
    if inst is None:
        # legacy fallbacks
        for alt in ('electricalspecs', 'bessspecs'):
            if attr_name in ('elec_specs', 'bess_specs') and hasattr(asset, alt):
                return getattr(asset, alt)
    return inst

def _delete_obsolete_specs(asset, keep_codes):
    """Remove OneToOne specs no longer applicable after a classification change."""
    for code, (_, _, attr, _) in SPEC_FORMS.items():
        if code not in keep_codes:
            inst = _get_instance(asset, attr)
            if inst:
                inst.delete()

def api_qr_view(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    url = request.build_absolute_uri(reverse('asset_api_key_entry', args=[asset.id]))
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Path to your logo (adjust as needed)
    logo_path = os.path.join(settings.BASE_DIR, 'devices', 'static', 'OPENTUNITY_LOGO.png')
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        # Resize logo
        basewidth = img.size[0] // 4  # 1/4th of QR code width
        wpercent = basewidth / float(logo.size[0])
        hsize = int((float(logo.size[1]) * float(wpercent)))
        logo = logo.resize((basewidth, hsize), Image.LANCZOS)
        # Paste logo at center
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        if logo.mode in ('RGBA', 'LA'):
            img.paste(logo, pos, mask=logo)
        else:
            img.paste(logo, pos)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")

def activate(request, uidb64, token):
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (ValueError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "registration/activation_complete.html")
    else:
        return render(request, "registration/activation_invalid.html")

def asset_api_key_entry(request, asset_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    apikey = request.GET.get('apikey')
    if apikey:
        # Validate API key
        if not APIKey.objects.filter(key=apikey, is_active=True).exists():
            return JsonResponse({'detail': 'Invalid or unauthorized API Key.'}, status=401)

        # Return the asset JSON
        asset = get_object_or_404(Asset, pk=asset_id)
        data = AssetSerializer(asset).data
        return JsonResponse(data, status=200)

    # No apikey -> show the HTML form (existing behavior)
    return render(request, 'enter_api_key.html', {'asset_id': asset_id})

@login_required
def profile(request):
    contributor, _ = ContentContributor.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=contributor, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profile updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=contributor, user=request.user)
    return render(request, "profile.html", {"form": form})

@login_required
def dashboard(request):
    # # Pull the 10 most recent assets created by this user
    # recent_assets = (
    #     Asset.objects
    #          .filter(record_contributor__user=request.user)
    #          .order_by('-record_insertion_date')[:10]
    # )
    # return render(request, 'dashboard.html', {
    #     'recent_assets': recent_assets
    qs = (Asset.objects
          .filter(record_contributor__user=request.user)
          .order_by('-record_insertion_date'))

    # per-page (default 50, hard cap 50)
    try:
        per = int(request.GET.get('per', 10))
    except ValueError:
        per = 10
    per = max(1, min(per, 50))

    paginator = Paginator(qs, per)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'dashboard.html', {
        'page_obj': page_obj,       # use this in template
        'per': per,
    })

def _comproto_meta():
    meta = {}
    for cp in CommunicationProtocol.objects.all():
        # cp.type is a JSONField that (per your data model) holds {"supported_com_protocols": [...], ...}
        meta[cp.id] = cp.type or {}
    return meta

@login_required
def add_device(request):
    """
    Add a new device + the required spec subforms (elec/bess/inv/pv/scc/meter).
    - Robustly derives the classification key (TYPE/NAME/str) in UPPERCASE.
    - Binds only the required subforms on POST; others stay unbound/disabled.
    - Always includes all forms in the context with stable prefixes so the template/JS can toggle.
    """
    def _class_key_from_asset_form_valid(asset_form) -> str:
        # Use cleaned_data; when valid this is safest and doesn’t hit the DB twice.
        cls = asset_form.cleaned_data.get("classification")
        if not cls:
            return ""
        for attr in ("type", "name", "label"):
            val = getattr(cls, attr, None)
            if val:
                return str(val).strip().upper()
        return str(cls).strip().upper()

    if request.method == 'POST':
        asset_form = AssetForm(request.POST)

        # If the main form is invalid, render with unbound spec forms.
        # (Your front-end JS will still auto-show the right blocks from the user's selection.)
        if not asset_form.is_valid():
            messages.error(request, "Please correct the errors in the main asset form.")
            return render(request, 'add_device.html', {
                'asset_form': asset_form,
                'elec_form':  ElectricalSpecsForm(prefix='elec'),
                'bess_form':  BESSSpecsForm(prefix='bess'),
                'inv_form':   InverterSpecsForm(prefix='inv'),
                'pv_form':    PVModuleSpecsForm(prefix='pv'),
                'scc_form':   SCCSpecsForm(prefix='scc'),
                'meter_form': EnergyMeterSpecsForm(prefix='meter'),
                'subform_title': 'Specifications',
                'required_forms': [],  # server-side initial state; JS will reveal based on classification select
                'comproto_meta': _comproto_meta(),
            })

        # Main form is valid → determine which spec forms are required from classification
        cls_key = _class_key_from_asset_form_valid(asset_form)
        spec_cfg = CLASS_TO_FORMS.get(cls_key, {'title': 'Specifications', 'forms': []})
        required_codes = set(spec_cfg['forms'])

        # Bind ONLY required forms with POST; keep others unbound so they won’t validate/fail
        elec_form  = ElectricalSpecsForm(request.POST if 'elec'  in required_codes else None, prefix='elec')
        bess_form  = BESSSpecsForm(     request.POST if 'bess'  in required_codes else None, prefix='bess')
        inv_form   = InverterSpecsForm( request.POST if 'inv'   in required_codes else None, prefix='inv')
        pv_form    = PVModuleSpecsForm( request.POST if 'pv'    in required_codes else None, prefix='pv')
        scc_form   = SCCSpecsForm(      request.POST if 'scc'   in required_codes else None, prefix='scc')
        meter_form = EnergyMeterSpecsForm(request.POST if 'meter' in required_codes else None, prefix='meter')

        # Validate only the required forms
        form_ok = True
        errors  = []

        def must_valid(form, label):
            nonlocal form_ok
            if not form.is_valid():
                form_ok = False
                errors.append(label)

        for code in spec_cfg['forms']:
            if   code == 'elec':
                if not elec_form.is_valid():
                    print("ELEC ERRORS:", elec_form.errors.as_json())
                    form_ok = False
                    errors.append('Electrical specs')
            elif code == 'bess':  must_valid(bess_form,  'BESS specs')
            elif code == 'inv':
                if not inv_form.is_valid():
                    # Keep this print for quick debugging during pilots
                    print("INV ERRORS:", inv_form.errors.as_json())
                    form_ok = False
                    errors.append('Inverter specs')
            elif code == 'pv':    must_valid(pv_form,    'PV module specs')
            elif code == 'scc':   must_valid(scc_form,   'SCC specs')
            elif code == 'meter': must_valid(meter_form, 'Energy meter specs')

        if not form_ok:
            messages.error(request, "Please correct the errors in: " + ", ".join(errors))
            # Re-render, keeping bound forms for the required set so field errors show;
            # non-required forms are fresh/unbound to avoid spurious validation.
            return render(request, 'add_device.html', {
                'asset_form': asset_form,
                'elec_form':  elec_form  if 'elec'  in required_codes else ElectricalSpecsForm(prefix='elec'),
                'bess_form':  bess_form  if 'bess'  in required_codes else BESSSpecsForm(prefix='bess'),
                'inv_form':   inv_form   if 'inv'   in required_codes else InverterSpecsForm(prefix='inv'),
                'pv_form':    pv_form    if 'pv'    in required_codes else PVModuleSpecsForm(prefix='pv'),
                'scc_form':   scc_form   if 'scc'   in required_codes else SCCSpecsForm(prefix='scc'),
                'meter_form': meter_form if 'meter' in required_codes else EnergyMeterSpecsForm(prefix='meter'),
                'subform_title': spec_cfg.get('title', 'Specifications'),
                'required_forms': spec_cfg['forms'],
                'comproto_meta': _comproto_meta(),
            })

        # All good → save everything in one transaction
        with transaction.atomic():
            contributor, _ = ContentContributor.objects.get_or_create(user=request.user)
            asset = asset_form.save(commit=False)
            asset.record_contributor = contributor
            asset.save()

            for code in spec_cfg['forms']:
                if   code == 'elec':
                    s = elec_form.save(commit=False);  s.asset = asset; s.save()
                elif code == 'bess':
                    s = bess_form.save(commit=False);  s.asset = asset; s.save()
                elif code == 'inv':
                    # inv_form.clean() should have built nom_dc_voltage_range from Min/Max V
                    s = inv_form.save(commit=False);   s.asset = asset; s.save()
                elif code == 'pv':
                    s = pv_form.save(commit=False);    s.asset = asset; s.save()
                elif code == 'scc':
                    s = scc_form.save(commit=False);   s.asset = asset; s.save()
                elif code == 'meter':
                    s = meter_form.save(commit=False); s.asset = asset; s.save()

        messages.success(request, "🎉 Your device has been added successfully!")
        return redirect('dashboard')

    # GET
    return render(request, 'add_device.html', {
        'asset_form': AssetForm(),
        'elec_form':  ElectricalSpecsForm(prefix='elec'),
        'bess_form':  BESSSpecsForm(prefix='bess'),
        'inv_form':   InverterSpecsForm(prefix='inv'),
        'pv_form':    PVModuleSpecsForm(prefix='pv'),
        'scc_form':   SCCSpecsForm(prefix='scc'),
        'meter_form': EnergyMeterSpecsForm(prefix='meter'),
        'subform_title': 'Specifications',
        'required_forms': [],
        'comproto_meta': _comproto_meta(),
    })

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # 1. Create user but keep inactive
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            # 2. Create ContentContributor as before
            ContentContributor.objects.create(
                user        = user,
                full_name   = form.cleaned_data['full_name'],
                role        = form.cleaned_data['role'],
                eori_number = form.cleaned_data['eori_number'],
            )
            # 3. Send activation email (we’ll implement next)
            send_activation_email(request, user)
            # 4. Instead of login(), show a “check your inbox” page
            return render(request, "registration/activation_send.html", {
                "email": user.email
            })
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def asset_detail(request, pk):
    asset = (
        Asset.objects
        .select_related(
            'record_contributor__user',
            'manufacturer', 'deployment', 'classification',
            'flexibility', 'communication', 'communication_protocol',
            'regulation', 'regulation_response_time_unit',
            'elec_specs', 'bess_specs', 'inverter_specs',
            'pv_module_specs', 'scc_specs', 'meter_specs',
        )
        .get(pk=pk, record_contributor__user=request.user)
    )
    return render(request, 'devices/asset_detail.html', {'asset': asset})

@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    # Enforce ownership
    contributor = getattr(asset, 'record_contributor', None)
    if not contributor or contributor.user != request.user:
        messages.error(request, "You don't have permission to edit this asset.")
        return redirect('dashboard')

    # Determine current classification mapping (for initial GET and on invalid POST)
    current_cls = (asset.classification.type or '').strip().upper()
    current_cfg = CLASS_TO_FORMS.get(current_cls, {'title': 'Specifications', 'forms': []})

    if request.method == 'POST':
        # Bind main form to existing instance
        asset_form = AssetForm(request.POST, instance=asset)

        # Determine target classification from POST (use the bound form if valid later)
        # For a robust approach, we try to get the posted classification's text
        # but since it's a FK, we rely on asset_form.cleaned_data after validation.
        # So first validate the asset_form minimally to read classification.
        if not asset_form.is_valid():
            print("ASSET ERRORS:", asset_form.errors.as_json())
            # Re-render with existing instances + current_cfg
            ctx = _build_edit_context(asset, asset_form, current_cfg)
            messages.error(request, "Please correct the errors in the main asset form.")
            return render(request, 'devices/asset_edit.html', ctx)

        # Now we can read the *new* classification selected by the user
        new_cls = (asset_form.cleaned_data['classification'].type or '').strip().upper()
        spec_cfg = CLASS_TO_FORMS.get(new_cls, {'title': 'Specifications', 'forms': []})

        # Build forms for each spec; bind to existing instance or None, with prefixes
        bound_forms = _build_bound_spec_forms(request, asset)

        # Validate only required forms for the chosen classification
        form_ok, errs = _validate_required_spec_forms(bound_forms, spec_cfg['forms'])

        if not form_ok:
            ctx = _build_edit_context(asset, asset_form, spec_cfg, bound_forms)
            messages.error(request, "Please correct the errors in: " + ", ".join(errs))
            return render(request, 'devices/asset_edit.html', ctx)

        # Save everything atomically
        with transaction.atomic():
            # Save main asset (includes any classification change)
            asset = asset_form.save()

            # Optionally delete obsolete specs if classification changed
            if new_cls != current_cls:
                _delete_obsolete_specs(asset, keep_codes=set(spec_cfg['forms']))

            # Save each required spec form to the correct OneToOne model
            for code in spec_cfg['forms']:
                model_cls, _, attr_name, prefix = SPEC_FORMS[code]
                f = bound_forms[code]
                obj = f.save(commit=False)
                # Attach / reattach OneToOne
                obj.asset = asset
                obj.save()

        messages.success(request, "✅ Asset updated successfully.")
        return redirect('asset_detail', pk=asset.id)

    # GET: render prefilled forms
    else:
        asset_form = AssetForm(instance=asset)
        ctx = _build_edit_context(asset, asset_form, current_cfg)
        return render(request, 'devices/asset_edit.html', ctx)

@login_required
@require_POST
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    contributor = getattr(asset, 'record_contributor', None)
    if not contributor or contributor.user != request.user:
        messages.error(request, "You don't have permission to delete this asset.")
        return redirect('dashboard')

    asset.delete()  # cascades to elec/bess/inverter/pv/scc/meter specs
    messages.success(request, "Asset deleted permanently.")
    return redirect('dashboard')

# ---- helpers used inside asset_edit ----

def _build_bound_spec_forms(request, asset):
    """Return dict of bound forms for all spec types with correct instance/prefix."""
    forms = {}
    for code, (model_cls, form_cls, attr_name, prefix) in SPEC_FORMS.items():
        instance = _get_instance(asset, attr_name)
        forms[code] = form_cls(request.POST, instance=instance, prefix=prefix)
    return forms

def _build_unbound_spec_forms(asset):
    """Return dict of unbound forms (GET) with instance=existing, prefix set."""
    forms = {}
    for code, (model_cls, form_cls, attr_name, prefix) in SPEC_FORMS.items():
        instance = _get_instance(asset, attr_name)
        forms[code] = form_cls(instance=instance, prefix=prefix)
    return forms

def _validate_required_spec_forms(forms_dict, required_codes):
    ok, errs = True, []
    labels = {
        'elec':  'Electrical specs',
        'bess':  'BESS specs',
        'inv':   'Inverter specs',
        'pv':    'PV module specs',
        'scc':   'SCC specs',
        'meter': 'Energy meter specs',
    }
    for code in required_codes:
        f = forms_dict.get(code)
        valid = bool(f and f.is_valid())
        if not valid:
            ok = False
            errs.append(labels.get(code, code))
            try:
                if f:
                    print(f"{code.upper()} ERRORS:", f.errors.as_json())
                    nfe = getattr(f, 'non_field_errors', lambda: [])()
                    if nfe:
                        print(f"{code.upper()} NON_FIELD_ERRORS:", nfe.as_text())
                else:
                    print(f"{code.upper()} ERROR: form missing in forms_dict")
            except Exception as e:
                print(f"{code.upper()} ERROR LOGGING FAILED:", e)
    return ok, errs

def _build_edit_context(asset, asset_form, spec_cfg, bound_forms=None):
    """Prepare template context for GET or invalid POST."""
    if bound_forms is None:
        bound_forms = _build_unbound_spec_forms(asset)

    return {
        'asset_form': asset_form,
        'elec_form':  bound_forms['elec'],
        'bess_form':  bound_forms['bess'],
        'inv_form':   bound_forms['inv'],
        'pv_form':    bound_forms['pv'],
        'scc_form':   bound_forms['scc'],
        'meter_form': bound_forms['meter'],
        'subform_title': spec_cfg.get('title', 'Specifications'),
        'required_forms': spec_cfg.get('forms', []),
        'asset': asset,
    }





