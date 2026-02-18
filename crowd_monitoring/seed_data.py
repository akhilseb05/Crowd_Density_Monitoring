import os
import django
import random
from django.contrib.gis.geos import Point

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crowd_monitoring.settings')
django.setup()

from monitoring.models import Event, Attendee, Manager, AttendeeLocationLog, ManagerLocationLog

def run_seed(event_name, num_attendees=100, num_managers=12):
    # 2. Get the target Event
    try:
        event = Event.objects.get(event_name=event_name)
    except Event.DoesNotExist:
        print(f"Error: Event '{event_name}' not found. Create it in the UI first.")
        return

    print(f"Starting seed for: {event.event_name}")

    # 3. Define GEC Wayanad coordinate bounds for random generation
    # Longitude: 76.0125 to 76.0155 | Latitude: 11.8875 to 11.8905
    def get_random_gecw_point():
        lng = random.uniform(76.0285, 76.0315)
        lat = random.uniform(11.8030, 11.8060)
        return Point(lng, lat)

    # 4. Create Attendees and Logs
    for i in range(num_attendees):
        attendee = Attendee.objects.create(
            event=event,
            name=f"Attendee_{i+1}",
            mobile_no=f"90000000{i:02d}",
            email_id=f"user{i}@example.com",
            consent_status=True
        )
        # Create a location log for the heatmap
        AttendeeLocationLog.objects.create(
            attendee=attendee,
            location=get_random_gecw_point()
        )

    # 5. Create Managers and Logs
    for i in range(num_managers):
        manager = Manager.objects.create(
            event=event,
            manager_name=f"Manager_{i+1}",
            manager_role="Security",
            mobile_no=f"80000000{i:02d}",
            email_id=f"mgr{i}@gecw.ac.in"
        )
        # Create a location log for the heatmap
        ManagerLocationLog.objects.create(
            manager=manager,
            location=get_random_gecw_point()
        )

    print(f"Successfully added {num_attendees} attendees and {num_managers} managers.")

if __name__ == "__main__":
    # Change "GECW Fest" to the exact name of the event you created in the UI
    run_seed("Valiyoorkavu Festival")