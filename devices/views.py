from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from .forms import SignupForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .utils import send_activation_email


from .forms import AssetForm, ElectricalSpecsForm, BESSSpecsForm
from .models import ContentContributor, Asset

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

@login_required
def dashboard(request):
    # Pull the 10 most recent assets created by this user
    recent_assets = (
        Asset.objects
             .filter(record_contributor__user=request.user)
             .order_by('-record_insertion_date')[:10]
    )
    return render(request, 'dashboard.html', {
        'recent_assets': recent_assets
    })

@login_required
def add_device(request):
    """
    Server‐side enforces:
      - Only BESSSpecs for classification 'Battery'
      - Only ElectricalSpecs otherwise
    Provides user feedback via messages.
    """
    if request.method == 'POST':
        asset_form = AssetForm(request.POST)
        elec_form  = ElectricalSpecsForm(request.POST, prefix='elec')
        bess_form  = BESSSpecsForm(request.POST, prefix='bess')

        # 1) Validate the asset form first
        if not asset_form.is_valid():
            messages.error(request, "Please correct the errors in the main asset form.")
            return render(request, 'add_device.html', {
                'asset_form': asset_form,
                'elec_form':  elec_form,
                'bess_form':  bess_form,
            })

        # Create asset instance (not saved yet) to inspect classification
        asset = asset_form.save(commit=False)
        cls_type = (asset.classification.type or '').strip().upper()

        valid_specs = False

        # 2) Validate exactly the correct specs form
        if cls_type == 'BATTERY':
            # Must use BESS form; electrical must be empty
            if not bess_form.is_valid():
                messages.error(request, "Please correct the errors in the BESS specs form.")
                valid_specs = False
            else:
                valid_specs = True
            # Reject any illegal elec data
            for name in elec_form.fields:
                if f'elec-{name}' in request.POST:
                    elec_form.add_error(None, "Electrical specs must be empty for Battery assets.")
                    valid_specs = False

        else:
            # Must use Electrical form; BESS must be empty
            if not elec_form.is_valid():
                messages.error(request, "Please correct the errors in the Electrical specs form.")
                valid_specs = False
            else:
                valid_specs = True
            for name in bess_form.fields:
                if f'bess-{name}' in request.POST:
                    bess_form.add_error(None, "BESS specs must be empty unless classification is Battery.")
                    valid_specs = False

        if not valid_specs:
            # Re-render with errors on whichever form(s) failed
            return render(request, 'add_device.html', {
                'asset_form': asset_form,
                'elec_form':  elec_form,
                'bess_form':  bess_form,
            })

        # 3) All validation passed → save within one transaction
        with transaction.atomic():
            contributor, _ = ContentContributor.objects.get_or_create(user=request.user)
            asset.record_contributor = contributor
            asset.save()

            if cls_type == 'BATTERY':
                specs = bess_form.save(commit=False)
            else:
                specs = elec_form.save(commit=False)

            specs.asset = asset
            specs.save()

        messages.success(request, "🎉 Your device has been added successfully!")
        return redirect('dashboard')

    else:
        asset_form = AssetForm()
        elec_form  = ElectricalSpecsForm(prefix='elec')
        bess_form  = BESSSpecsForm(prefix='bess')

    return render(request, 'add_device.html', {
        'asset_form': asset_form,
        'elec_form':  elec_form,
        'bess_form':  bess_form,
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
    asset = get_object_or_404(
        Asset,
        pk=pk,
        record_contributor__user=request.user
    )
    return render(request, 'devices/asset_detail.html', {
        'asset': asset
    })

@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(
        Asset,
        pk=pk,
        record_contributor__user=request.user
    )
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, "Asset updated!")
            return redirect('asset_detail', pk=pk)
    else:
        form = AssetForm(instance=asset)

    return render(request, 'devices/asset_edit.html', {
        'form': form,
        'asset': asset
    })



