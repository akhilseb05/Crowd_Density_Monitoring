from django.contrib import admin
from .models import Admin, Attendee, AttendeeLocationLog, Manager, ManagerLocationLog, Zone, Event, Alert, CrowdLog 
# Register your models here.
admin.site.register(Admin)
admin.site.register(Attendee)
admin.site.register(AttendeeLocationLog)
admin.site.register(Manager)
admin.site.register(ManagerLocationLog)
admin.site.register(Zone)
admin.site.register(Event)
admin.site.register(Alert)
admin.site.register(CrowdLog)
