from django.db import models

# Create your models here.
from django.db import models

from django.contrib.gis.db import models # Use the GIS version of models!
from django.utils import timezone

class Admin(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100) # In production, use Django's built-in User model for security
    contact_no = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class Event(models.Model):
    event_name = models.CharField(max_length=200)
    # Replaces 'Location boundary' with a Polygon for the entire festival area
    location_boundary = models.PolygonField() 
    current_count = models.IntegerField(default=0)
    event_date = models.DateField(default=timezone.now)
    event_time = models.TimeField(default=timezone.now)
    def __str__(self):
        return self.event_name

class Zone(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='zones') #
    zone_name = models.CharField(max_length=100)
    # Replaces 'Location boundary' with a PolygonField for specific areas (e.g., Stage A)
    location_boundary = models.PolygonField()
    current_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.zone_name} ({self.event.event_name})"

class Attendee(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    name = models.CharField(max_length=100)
    no_of_accompanies = models.IntegerField(default=0)
    mobile_no = models.CharField(max_length=15)
    email_id = models.EmailField(default="example123@gmail.com")
    consent_status = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Manager(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='managers')
    manager_name = models.CharField(max_length=100)
    manager_role = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15)
    email_id = models.EmailField()

    def __str__(self):
        return self.manager_name

class AttendeeLocationLog(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE)
    # Replaces 'Latitude' and 'Longitude' with a single PointField
    location = models.PointField() 
    log_timestamp = models.DateTimeField(auto_now_add=True)

class ManagerLocationLog(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
    # Replaces 'Latitude' and 'Longitude' with a single PointField
    location = models.PointField()
    log_timestamp = models.DateTimeField(auto_now_add=True)

class Alert(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    recipient_type = models.CharField(max_length=50) # e.g., 'Admin', 'Manager'
    alert_message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)