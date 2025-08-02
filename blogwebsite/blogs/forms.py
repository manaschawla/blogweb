# forms.py
from django import forms
from .models import Custom_user,SubscriptionPlan,UserSubscription

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Custom_user
        fields = ['profile_picture', 'first_name', 'last_name', 'mobile_number',
                  'alternate_mobile_number', 'email', 'country', 'state', 'city', 'pincode']
        
class SubscriptionSelectForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=SubscriptionPlan.objects.filter(is_active=True))

