from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class SimulationForm(forms.Form):
    steps = forms.CharField(label='Number of participants', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'eg 600'}))
    pilot = forms.ChoiceField(label='Specific country generation', choices=[('any', 'Any'), ('Austria', 'Austria'), ('Greece', 'Greece'), ('Spain', 'Spain'), ('United Kingdom', 'United Kingdom')], widget=forms.Select(attrs={'class': 'form-control'}))
    age_min = forms.CharField(label='Minimum age', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'eg 30'}))
    age_max = forms.CharField(label='Maximum Age', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'eg 60'}))
    gender = forms.ChoiceField(label='Gender', choices=[('-1', 'Anyone'), ('0', 'Male'), ('1', 'Female'), ('2', 'Non-binary'), ('3', 'Other'), ('4', 'Don’t want to say')], widget=forms.Select(attrs={'class': 'form-control'}))
    charlson = forms.CharField(label='Charlson Comorbidity',required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'eg 5'}))
    bsi = forms.CharField(label='Brief Symptom Inventory-18', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'eg 7'}))
    previous_hm = forms.ChoiceField(label='Previous Homelessness', choices=[('-1', 'Any'), ('1', 'Yes'), ('0', 'No')], widget=forms.Select(attrs={'class': 'form-control'}))
    ethos = forms.ChoiceField(label='ETHOS Category', choices=[
        ('-1', 'Any'), ('0', 'Living rough'), ('1', 'Staying in a night shelter'),
        ('2', 'In accommodation for the homeless: Homeless hostel'),
        ('3', 'In accommodation for the homeless: Temporary accommodation'),
        ('4', 'In accommodation for the homeless: Transitional supported accommodation'),
        ('10', 'Receiving longer-term support (due to homelessness): Supported accommodation for formerly homeless persons'),
        ('11', 'Living in insecure accommodation: Temporarily with family/friends'),
        ('12', 'Living in insecure accommodation: No legal (sub) tenancy'),
        ('18', 'People living in temporary/ non-conventional structures: Non-conventional building')
    ], widget=forms.Select(attrs={'class': 'form-control'}))
