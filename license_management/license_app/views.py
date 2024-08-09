from ast import Module
from datetime import datetime
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import LicenseForm, LicenseModuleFormSet, ModuleQuantityForm, TenantUserFormSet, BulkImportForm,  UserSearchForm, BulkTenantUserForm
from .models import License, LicenseModule,TenantUser
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
import csv
from django.db import transaction
from . import views

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'license_app/login.html', {'form': form})

@login_required
def home_view(request):
    licenses = License.objects.filter(submitted_by=request.user)
    return render(request, 'license_app/home.html', {'licenses': licenses})

@login_required
def add_license_view(request):
    if request.method == 'POST':
        form = LicenseForm(request.POST)
        module_form = ModuleQuantityForm(request.POST)
        bulk_user_form = BulkTenantUserForm(request.POST)

        if form.is_valid() and module_form.is_valid() and bulk_user_form.is_valid():
            license_obj = form.save(commit=False)
            license_obj.submitted_by = request.user
            license_obj.save()

            # Save module quantities
            for field in module_form:
                module_name = field.label
                quantity = module_form.cleaned_data[field.name]
                if quantity > 0:
                    LicenseModule.objects.create(
                        license=license_obj,
                        module_name=module_name,
                        quantity=quantity
                    )

            # Handle tenant user emails
            user_emails = bulk_user_form.cleaned_data['user_emails']
            for email in user_emails.split(','):
                TenantUser.objects.create(license=license_obj, user_email=email.strip())

            return redirect('home')
    else:
        form = LicenseForm()
        module_form = ModuleQuantityForm()
        bulk_user_form = BulkTenantUserForm()

    return render(request, 'license_app/add_license.html', {
        'form': form,
        'module_form': module_form,
        'bulk_user_form': bulk_user_form
    })




@login_required
def bulk_import_view(request):
    if request.method == 'POST':
        form = BulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            try:
                csv_data = csv_file.read()

                try:
                    decoded_csv_data = csv_data.decode('utf-8').splitlines()
                except UnicodeDecodeError:
                    decoded_csv_data = csv_data.decode('ISO-8859-1').splitlines()

                reader = csv.DictReader(decoded_csv_data)
                for row in reader:
                    try:
                        license_valid_from = datetime.strptime(row['License Valid from'], '%d-%m-%Y').date()
                        license_valid_till = datetime.strptime(row['License Valid till'], '%d-%m-%Y').date()
                    except ValueError:
                        messages.error(request, f'Invalid date format in row: {row}')
                        continue

                    try:
                        license_obj = License(
                            company_name=row['Company Name'],
                            category=row['Category'],
                            deployment_type=row['Deployment Type'],
                            tenant_name=row['Tenant Name'],
                            license_status=row['License Status'],
                            license_category=row['License Category'],
                            license_valid_from=license_valid_from,
                            license_valid_till=license_valid_till,
                            assigned_license_quantity=row['Assigned License quantity'],
                            approved_by=row['Approved by'],
                            account_manager=row['Account Manager'],
                            license_provided=row['License Provided'],
                            instance=row['Instance'],
                            submitted_by=request.user
                        )
                        license_obj.save()
                    except Exception as e:
                        print(f'Error saving license: {e}')
                        continue

                    user_emails = row['User list'].split(',')
                    for email in user_emails:
                        try:
                            TenantUser.objects.create(license=license_obj, user_email=email.strip())
                        except Exception as e:
                            print(f'Error creating TenantUser: {e}')

                    # Handle module quantities
                    for module_name in ['Rubisight-Designer', 'Rubistudio', 'Rubisight-Viewer', 'RubiFlow', 'News Analysis', 'Admin', 'Rubithings']:
                        quantity_field = f'quantity_{module_name}'
                        quantity = row.get(quantity_field, '0').strip()
                        if quantity == '':
                            quantity = 0
                        else:
                            try:
                                quantity = int(quantity)
                            except ValueError:
                                quantity = 0

                        LicenseModule.objects.create(
                            license=license_obj,
                            module_name=module_name,
                            quantity=quantity
                        )

                messages.success(request, 'Bulk import was successful.')
                return redirect('home')
            except Exception as e:
                import traceback
                messages.error(request, f'Error processing file: {e}')
                print(traceback.format_exc())
        else:
            messages.error(request, 'Form is not valid.')

    return render(request, 'license_app/bulk_import.html', {'form': BulkImportForm()})



@login_required
def edit_license_view(request, pk):
    license_obj = get_object_or_404(License, pk=pk)
    
    if request.method == 'POST':
        form = LicenseForm(request.POST, instance=license_obj)
        module_form = ModuleQuantityForm(request.POST)
        bulk_user_form = BulkTenantUserForm(request.POST)

        if form.is_valid() and module_form.is_valid() and bulk_user_form.is_valid():
            license_obj = form.save(commit=False)
            license_obj.save()

            # Save module quantities
            LicenseModule.objects.filter(license=license_obj).delete()
            for field in module_form:
                module_name = field.label
                quantity = module_form.cleaned_data[field.name]
                if quantity > 0:
                    LicenseModule.objects.create(
                        license=license_obj,
                        module_name=module_name,
                        quantity=quantity
                    )

            # Handle tenant user emails
            TenantUser.objects.filter(license=license_obj).delete()
            user_emails = bulk_user_form.cleaned_data['user_emails']
            for email in user_emails.split(','):
                TenantUser.objects.create(license=license_obj, user_email=email.strip())

            return redirect('home')
    else:
        form = LicenseForm(instance=license_obj)
        
        # Initialize module_form with existing module quantities
        module_quantities = LicenseModule.objects.filter(license=license_obj)
        print("Module quantities:", module_quantities)
        initial_data = {module.module_name: module.quantity for module in module_quantities}
        print("Initial data:", initial_data)
        module_form = ModuleQuantityForm(initial=initial_data)
        print("module_form:", module_form)
        # Initialize bulk_user_form with existing tenant user emails
        tenant_users = TenantUser.objects.filter(license=license_obj)
        initial_emails = ','.join([user.user_email for user in tenant_users])
        bulk_user_form = BulkTenantUserForm(initial={'user_emails': initial_emails})

    return render(request, 'license_app/edit_license.html', {
        'form': form,
        'module_form': module_form,
        'bulk_user_form': bulk_user_form,
        'license_obj': license_obj
    })

    
@login_required
def delete_license_view(request, pk):
    license_obj = get_object_or_404(License, pk=pk, submitted_by=request.user)
    if request.method == 'POST':
        license_obj.delete()
        return redirect('home')
    return render(request, 'license_app/delete_license_confirm.html', {'license': license_obj})

@login_required
def search_view(request):
    form = UserSearchForm(request.GET or None)
    search_results = []

    if form.is_valid():
        tenant_name = form.cleaned_data.get('tenant_name')
        username = form.cleaned_data.get('username')

        
        # print(f'Searching for Tenant Name: "{tenant_name}", Username: "{username}"')

        # Build the query filter
        query_filter = {}
        if tenant_name:
            query_filter['license__tenant_name__icontains'] = tenant_name
        if username:
            query_filter['user_email__icontains'] = username

        # Execute the query
        search_results = TenantUser.objects.filter(**query_filter)

        # More debug print statements
        print(f'Found {len(search_results)} results.')
        for result in search_results:
            print(f'User Email: {result.user_email}, Tenant Name: {result.license.tenant_name}')

    return render(request, 'license_app/search_results.html', {
        'form': form,
        'search_results': search_results,
    })



@login_required
def export_tenant_data(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tenant_data.csv"'

    writer = csv.writer(response)
    
    # Get all unique module names
    all_modules = LicenseModule.objects.values_list('module_name', flat=True).distinct()
    
    # Write the header row
    header = [
        'Company Name', 'Category', 'Deployment Type', 'Tenant Name', 'License Status',
        'License Valid From', 'License Valid Till', 'Assigned License Quantity',
        'Approved By', 'Account Manager', 'Tenant Contact', 'Instance', 'License Provided'
    ]
    
    header.extend(all_modules)
    writer.writerow(header)
    
    # Get all licenses with their related modules
    licenses = License.objects.all().prefetch_related('modules')

    for license in licenses:
        # Prepare a row for the current license
        row = [
            license.company_name, license.category, license.deployment_type, license.tenant_name,
            license.license_status, license.license_valid_from, license.license_valid_till,
            license.assigned_license_quantity, license.approved_by, license.account_manager,
            license.tenant_contact, license.instance, license.license_provided
        ]
        
        # Dictionary for quick lookup of module quantities
        module_quantities = {module.module_name: module.quantity for module in license.modules.all()}
        
        # Add quantities for each module in the header
        for module_name in all_modules:
            row.append(module_quantities.get(module_name, 0))
        
        writer.writerow(row)

    return response
