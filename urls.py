from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    # Dashboard (Weekly Hours)
    path('', views.dashboard, name='dashboard'),

    # Edit hours for a day
    path('hours/edit/', views.edit_hours, name='edit_hours'),

    # Special Days
    path('special-days/', views.special_days, name='special_days'),
    path('special-days/add/', views.add_special_day, name='add_special_day'),
    path('special-days/<uuid:pk>/edit/', views.edit_special_day, name='edit_special_day'),
    path('special-days/<uuid:pk>/delete/', views.delete_special_day, name='delete_special_day'),

    # Is Open Now API
    path('api/is-open/', views.is_open_now, name='is_open_now'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
]
