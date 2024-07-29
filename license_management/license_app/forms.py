from django import forms
from .models import License, TenantUser,LicenseModule

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = [
            'company_name', 'category', 'deployment_type', 'tenant_name', 'license_status', 'category',
            'license_valid_from', 'license_valid_till', 'assigned_license_quantity', 
            'approved_by', 'account_manager', 'instance','license_provided','tenant_contact'
        ]
        widgets = {
            'license_valid_from': forms.DateInput(attrs={'type': 'date'}),
            'license_valid_till': forms.DateInput(attrs={'type': 'date'}),
        }

class TenantUserForm(forms.ModelForm):
    class Meta:
        model = TenantUser
        fields = ['user_email']
        
TenantUserFormSet = forms.inlineformset_factory(License, TenantUser, form=TenantUserForm, extra=1)

class BulkTenantUserForm(forms.Form):
    user_emails = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Enter user emails separated by commas',
        'rows': 3
    }))
    
class LicenseModuleForm(forms.ModelForm):
    class Meta:
        model = LicenseModule
        fields = ['module_name', 'quantity']

LicenseModuleFormSet = forms.inlineformset_factory(License, LicenseModule, form=LicenseModuleForm, extra=1)



class BulkImportForm(forms.Form):
    csv_file = forms.FileField()

class UserSearchForm(forms.Form):
    tenant_name = forms.CharField(max_length=255, required=False, label='Tenant Name')
    username = forms.CharField(max_length=255, required=False, label='Username')