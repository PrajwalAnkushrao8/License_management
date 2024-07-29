# license_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import License, TenantUser

@receiver(post_save, sender=TenantUser)
def update_assigned_license_quantity(sender, instance, **kwargs):
    # Get the related License object
    license_instance = instance.license
    
    # Calculate the total quantity of modules
    total_quantity = TenantUser.objects.filter(license=license_instance).aggregate(sum('quantity'))['quantity__sum'] or 0
    
    # Update the Assigned License Quantity field
    license_instance.assigned_license_quantity = total_quantity
    license_instance.save()
