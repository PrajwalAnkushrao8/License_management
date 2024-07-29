from django.urls import path
from .views import login_view, home_view, add_license_view, bulk_import_view, delete_license_view, edit_license_view, search_view
from django.contrib.auth import views as auth_views

urlpatterns = [
   
    path('login/', login_view, name='login'),
    path('', home_view, name='home'),
    path('add/', add_license_view, name='add_license'),
    path('bulk_import/', bulk_import_view, name='bulk_import'),
    path('delete/<int:pk>/', delete_license_view, name='delete_license'),
    path('edit/<int:pk>/', edit_license_view, name='edit_license'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  
    path('search_users/', search_view, name='search_users'),
]