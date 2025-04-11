
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignupForm, LoginForm, SimulationForm
from typing import Optional
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import os


from base.microsimulation import intervention_effect

def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

# login page
def user_login(request):
    logout(request)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Invalid username or password")
    else:

        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

def check_ages(age_min: Optional[int], age_max: Optional[int]) -> tuple:
    if not age_min:
        age_min = 0
    if not age_max:
        age_max = 115
    return age_min, age_max

@login_required(login_url='login')
def procesado_simulacion(request):
    if request.method == 'POST':
        form = SimulationForm(request.POST)
        if form.is_valid():
            pilot = form.cleaned_data['pilot']
            steps_ = form.cleaned_data['steps']
            age_min = form.cleaned_data['age_min']
            age_max = form.cleaned_data['age_max']
            gender_ = form.cleaned_data['gender']
            previous_hm_ = form.cleaned_data['previous_hm']
            ethos_ = form.cleaned_data['ethos']
            charlson_ = form.cleaned_data['charlson']

            steps = int(steps_)
            gender = int(gender_)
            previous_hm = int(previous_hm_)
            ethos = int(ethos_)
            charlson = int(charlson_) if charlson_.isnumeric() else None

            if gender == -1:
                gender = None
            if previous_hm == -1:
                previous_hm = None
            if ethos == -1:
                ethos = None
            if pilot == 'any':
                pilot = None

            age_min = int(age_min) if age_min and age_min.isnumeric() else None
            age_max = int(age_max) if age_max and age_max.isnumeric() else None
            ages = check_ages(age_min, age_max)

        aggregated_data = intervention_effect(steps=steps, pilot=pilot, ages=ages, gender=gender, ethos=ethos,
                                         previous_homeless=previous_hm, charlson=charlson)

        if aggregated_data is None:
            return render(request, 'error.html')

        else:
            images_dir = os.path.join('static', 'features')
            images = [f'/static/features/{img}' for img in os.listdir(images_dir) if
                      img.endswith(('png', 'jpg', 'jpeg'))]

            simHealth, simSocial, adherence, rest_variables = aggregated_data

            simHealth = dict(simHealth)
            simSocial = dict(simSocial)
            adherence = dict(adherence)
            rest_variables = dict(rest_variables)

            return render(request, 'results.html',
                          {'simHealth': simHealth, 'simSocial': simSocial, 'adherence': adherence, 'rest_variables': rest_variables,
                           'images': images})
    else:
        form = SimulationForm()
        return render(request, 'index.html', {'form': form})
