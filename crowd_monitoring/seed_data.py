import os
import django
import random
from django.contrib.gis.geos import Point,Polygon

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crowd_monitoring.settings')
django.setup()

from monitoring.models import Event, Attendee, Manager, AttendeeLocationLog, ManagerLocationLog

def run_seed(event_name, num_attendees=5000, num_managers=12):
    try:
        event = Event.objects.get(event_name=event_name)
    except Event.DoesNotExist:
        print(f"Error: Event '{event_name}' not found. Create it in the UI first.")
        return

    print(f"Starting seed for: {event.event_name}")


    def get_random_gecw_point():
        boundary_coords = [
            (75.968463, 11.832977),
            (75.969261, 11.836123), 
            (75.971922, 11.835676), 
            (75.971896, 11.831650),
            (75.968463, 11.832977)
        ]
        poly = Polygon(boundary_coords)
        
        min_lng, min_lat, max_lng, max_lat = poly.extent
        
        while True:
            lng = random.uniform(min_lng, max_lng)
            lat = random.uniform(min_lat, max_lat)
            point = Point(lng, lat)
            
            if poly.contains(point):
                return point

    for i in range(num_attendees):
        attendee = Attendee.objects.create(
            event=event,
            name=f"Attendee_{i+1}",
            mobile_no=f"9876543210",
            email_id=f"user{i}@example.com",
            consent_status=True
        )
        AttendeeLocationLog.objects.create(
            attendee=attendee,
            location=get_random_gecw_point()
        )

    for i in range(num_managers):
        manager = Manager.objects.create(
            event=event,
            manager_name=f"Manager_{i+1}",
            manager_role="Security",
            mobile_no=f"9876543210",
            email_id=f"mgr{i}@gecw.ac.in"
        )
        ManagerLocationLog.objects.create(
            manager=manager,
            location=get_random_gecw_point()
        )

    print(f"Successfully added {num_attendees} attendees and {num_managers} managers.")

if __name__ == "__main__":
    run_seed("GECW Tech Fest")