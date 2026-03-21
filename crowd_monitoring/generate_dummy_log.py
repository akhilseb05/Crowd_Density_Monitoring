import os
import django
from datetime import timedelta
import random

# 1. Setup Django environment (Replace 'crowd_monitoring' with your actual project folder name if different)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crowd_monitoring.settings')
django.setup()

from django.utils import timezone
# Replace 'your_app_name' with the name of the app containing your models (e.g., 'myapp.models')
from monitoring.models import Event, Zone, CrowdLog 

def populate_dummy_data():
    event_name = "GECW Tech Fest"
    zone_names = ["Open Stage", "Stage 2", "Auditorium", "Main Ground"]

    # 2. Fetch the Event (Make sure you created this in your dashboard already!)
    try:
        event = Event.objects.get(event_name=event_name)
    except Event.DoesNotExist:
        print(f"Error: Could not find an event named '{event_name}'. Please create it in the UI first.")
        return

    # 3. Fetch or warn about Zones
    zones = []
    for z_name in zone_names:
        try:
            zone = Zone.objects.get(event=event, zone_name=z_name)
            zones.append(zone)
        except Zone.DoesNotExist:
            print(f"Error: Zone '{z_name}' not found for this event. Create it in the UI first.")
            return

    # 4. Clear old logs so you don't stack data if you run this multiple times
    CrowdLog.objects.filter(event=event).delete()
    print(" Cleared old logs...")

    # 5. Setup Time Range (8:00 AM to 6:00 PM today)
    now = timezone.now()
    start_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
    
    current_time = start_time
    interval = timedelta(minutes=30) # Generate data every 30 mins

    print("Generating new crowd data...")

    # 6. Loop through the day
    while current_time <= end_time:
        total_event_crowd = 0
        hour = current_time.hour

        # Determine a realistic "Crowd Multiplier" based on the time of day
        if hour < 10:
            multiplier = 0.2  # Morning, slow start
        elif hour < 13:
            multiplier = 0.6  # Noon, getting busy
        elif hour < 16:
            multiplier = 1.0  # Peak hours!
        else:
            multiplier = 0.4  # Evening, winding down

        # Generate data for each Zone
        for zone in zones:
            # Randomize the base count, then apply the time-of-day multiplier
            base_capacity = random.randint(100, 500)
            
            # Add some extra randomness so the lines aren't identical
            variation = random.uniform(0.8, 1.2) 
            
            zone_count = int(base_capacity * multiplier * variation)
            total_event_crowd += zone_count

            # Save the Zone Log
            CrowdLog.objects.create(
                event=event,
                zone=zone,
                person_count=zone_count,
                timestamp=current_time
            )

        # Save the Total Event Log (zone=None)
        CrowdLog.objects.create(
            event=event,
            zone=None, # None signifies this is the total count
            person_count=total_event_crowd,
            timestamp=current_time
        )

        current_time += interval

    print(f"Successfully generated dummy data for {event_name}!")

if __name__ == "__main__":
    populate_dummy_data()