from django.db import models
from django.contrib.auth.models import User

class License(models.Model):
    CATEGORY_CHOICES = [
        ('Partner', 'Partner'),
        ('Customer', 'Customer'),
        ('Academia', 'Academia'),
    ]
    
    DEPLOYMENT_TYPE_CHOICES = [
        ('SaaS', 'SaaS'),
        ('PaaS', 'PaaS'),
        ('On Premises', 'On Premises'),
    ]
    
    LICENSE_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    INSTANCE_CHOICES = [
        ('Partner', 'Partner'),
        ('Sense', 'Sense'),
        ('Datalabs', 'Datalabs'),
        ('Inspire', 'Inspire'),
    ]
    
    LICENSE_CATEGORY_CHOICES = [
        ('Sponsored', 'Sponsored'),
        ('Free', 'Free'),
        ('Paid', 'Paid'),

    ]

    LICENSE_PROVIDED_CHOICES = [
        ('Platform','Platform'),
        ('Rubisight-Designer','Rubisight-Designer'),
        ('Rubisight-Designer+Rubisight-viewer','Rubisight-Designer+Rubisight-viewer'),
        ('Rubiflow+Rubisight-Designer+Rubisight-viewer','Rubiflow+Rubisight-Designer+Rubisight-viewer'),
        ]
    
    company_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    deployment_type = models.CharField(max_length=50, choices=DEPLOYMENT_TYPE_CHOICES)
    tenant_name = models.CharField(max_length=255)
    license_status = models.CharField(max_length=50, choices=LICENSE_STATUS_CHOICES)
    license_category = models.CharField(max_length=50, choices=LICENSE_CATEGORY_CHOICES,default='Free')
    license_valid_from = models.DateField()
    license_valid_till = models.DateField()
    assigned_license_quantity = models.IntegerField()
    approved_by = models.CharField(max_length=255)
    account_manager = models.CharField(max_length=255)
    tenant_contact = models.CharField(max_length=255,default='Please Update the Contact details')
    instance = models.CharField(max_length=50, choices=INSTANCE_CHOICES)
    license_provided = models.CharField(choices=LICENSE_PROVIDED_CHOICES,default='Rubiflow+Rubisight-Designer+Rubisight-viewer')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.company_name} - {self.tenant_name}"

class TenantUser(models.Model):
    license = models.ForeignKey(License, related_name='users', on_delete=models.CASCADE)
    user_email = models.EmailField()

    def __str__(self):
        return self.user_email
    
    
class LicenseModule(models.Model):
    MODULE_CHOICES = [
        ('Rubiflow', 'Rubiflow'),
        ('Rubisight-Designer', 'Rubisight-Designer'),
        ('Rubistudio', 'Rubistudio'),
        ('Rubisight-Viewer', 'Rubisight-Viewer'),
        
    ]
    
    license = models.ForeignKey(License, related_name='modules', on_delete=models.CASCADE)
    module_name = models.CharField(max_length=50, choices=MODULE_CHOICES)
    quantity = models.IntegerField(default='0')

    def __str__(self):
        return f"{self.module_name} - {self.quantity} units"
