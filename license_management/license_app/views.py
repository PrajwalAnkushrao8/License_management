from datetime import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import LicenseForm, LicenseModuleFormSet, TenantUserFormSet, BulkImportForm,  UserSearchForm, BulkTenantUserForm
from .models import License,TenantUser
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
import csv


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
        module_formset = LicenseModuleFormSet(request.POST)
        bulk_user_form = BulkTenantUserForm(request.POST)

        if form.is_valid() and module_formset.is_valid() and bulk_user_form.is_valid():
            license_obj = form.save(commit=False)
            license_obj.submitted_by = request.user
            license_obj.save()

            # Save the module formset with the new license instance
            module_formset.instance = license_obj
            module_formset.save()

            user_emails = bulk_user_form.cleaned_data['user_emails']
            for email in user_emails.split(','):
                TenantUser.objects.create(license=license_obj, user_email=email.strip())

            return redirect('home')
        else:
            # Print errors if any
            print("License Form Errors:", form.errors)
            print("Bulk User Form Errors:", bulk_user_form.errors)
            print("Module Formset Errors:", module_formset.errors)
    else:
        form = LicenseForm()
        module_formset = LicenseModuleFormSet()
        bulk_user_form = BulkTenantUserForm()

    return render(request, 'license_app/add_license.html', {'form': form, 'module_formset': module_formset, 'bulk_user_form': bulk_user_form})



@login_required
def bulk_import_view(request):
    if request.method == 'POST':
        form = BulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            try:
              
                csv_data = csv_file.read()
                # print("Raw CSV Data:", csv_data[:1000])  

                # Attempt to decode with UTF-8 first, fallback to ISO-8859-1 if needed
                try:
                    decoded_csv_data = csv_data.decode('utf-8').splitlines()
                except UnicodeDecodeError:
                    decoded_csv_data = csv_data.decode('ISO-8859-1').splitlines()

               
                # print("Decoded CSV Data:", decoded_csv_data[:5]) 

                reader = csv.DictReader(decoded_csv_data)
                for row in reader:
                    # print("Processing row:", row)  

                    # Convert date strings to datetime.date objects
                    try:
                        license_valid_from = datetime.strptime(row['License Valid from'], '%d-%m-%Y').date()
                        license_valid_till = datetime.strptime(row['License Valid till'], '%d-%m-%Y').date()
                    except ValueError:
                        messages.error(request, f'Invalid date format in row: {row}')
                        continue  # Skip this row

                    # Create License object
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
                
                messages.success(request, 'Bulk import was successful.')
                return redirect('home')
            except Exception as e:
                import traceback
                messages.error(request, f'Error processing file: {e}')
                print(traceback.format_exc())
        else:
            # print(form.errors)  
            messages.error(request, 'Form is not valid.')
    
    return render(request, 'license_app/bulk_import.html', {'form': BulkImportForm()})



@login_required
def edit_license_view(request, pk):
    license_instance = get_object_or_404(License, pk=pk)
    if request.method == 'POST':
        form = LicenseForm(request.POST, instance=license_instance)
        formset = TenantUserFormSet(request.POST, instance=license_instance)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('home')
    else:
        form = LicenseForm(instance=license_instance)
        formset = TenantUserFormSet(instance=license_instance)
    return render(request, 'license_app/edit_license.html', {'form': form, 'formset': formset})

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
