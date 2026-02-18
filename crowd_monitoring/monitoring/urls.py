from django.urls import path
from . import views

urlpatterns = [
    # The home page for your app (shows the list of events and the 'Add' form)
    path('', views.event_list, name='event_list'),
    
    # The dashboard page for a specific event (uses the Event ID)
    # The <int:event_id> part passes the ID to the dashboard view
    path('event/<int:event_id>/dashboard/', views.dashboard, name='dashboard'),
    path('app/', views.attendee_app, name='attendee_app'),
    path('api/register-attendee/', views.register_attendee_api, name='register_api'),
    path('api/update-location/', views.update_location_api, name='update_location_api'),
]