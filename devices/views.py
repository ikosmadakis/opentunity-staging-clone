from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import (
    AssetForm,
    DataAcquisitionForm,
    ElectricalDownwardForm,
    ElectricalUpwardForm,
    ElectricalBESSForm,
    EnvironmentalForm,
    PhysicalSpecsForm
)

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def add_device(request):
    if request.method == 'POST':
        asset_form = AssetForm(request.POST)
        data_form = DataAcquisitionForm(request.POST)
        down_form = ElectricalDownwardForm(request.POST)
        up_form = ElectricalUpwardForm(request.POST)
        bess_form = ElectricalBESSForm(request.POST)
        env_form = EnvironmentalForm(request.POST)
        phys_form = PhysicalSpecsForm(request.POST)

        if all([f.is_valid() for f in [
            asset_form, data_form, down_form, up_form, bess_form, env_form, phys_form
        ]]):
            asset = asset_form.save(commit=False)
            asset.contributor = request.user
            asset.save()

            # Link all child forms to the main asset
            data = data_form.save(commit=False)
            data.main_asset = asset
            data.save()

            down = down_form.save(commit=False)
            down.main_asset = asset
            down.save()

            up = up_form.save(commit=False)
            up.main_asset = asset
            up.save()

            bess = bess_form.save(commit=False)
            bess.main_asset = asset
            bess.save()

            env = env_form.save(commit=False)
            env.main_asset = asset
            env.save()

            phys = phys_form.save(commit=False)
            phys.main_asset = asset
            phys.save()

            return redirect('dashboard')
    else:
        asset_form = AssetForm()
        data_form = DataAcquisitionForm()
        down_form = ElectricalDownwardForm()
        up_form = ElectricalUpwardForm()
        bess_form = ElectricalBESSForm()
        env_form = EnvironmentalForm()
        phys_form = PhysicalSpecsForm()

    return render(request, 'add_device.html', {
        'asset_form': asset_form,
        'data_form': data_form,
        'down_form': down_form,
        'up_form': up_form,
        'bess_form': bess_form,
        'env_form': env_form,
        'phys_form': phys_form,
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
