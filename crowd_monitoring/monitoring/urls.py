from django.urls import path
from . import views

urlpatterns = [
    # The home page for your app (shows the list of events and the 'Add' form)
    path('', views.event_list, name='event_list'),
    path('admin-login', views.admin_login, name='admin_login'),
    path('admin-logout', views.admin_logout, name='admin_logout'),
    # The dashboard page for a specific event (uses the Event ID)
    path('event/<int:event_id>/dashboard/', views.dashboard, name='dashboard'),
    path('event/<int:event_id>/alerts/', views.send_alerts, name='send_alerts'),
    path('api/get-events/', views.get_events_api, name='get_events_api'),
    path('api/register-attendee/', views.register_attendee_api, name='register_api'),
    path('api/update-location/', views.update_location_api, name='update_location_api'),
]