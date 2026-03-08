from django.test import TestCase
from django.contrib.gis.geos import Point, Polygon
from django.utils import timezone
from .models import Zone, AttendeeLocationLog, Attendee, Event

class CrowdDensityTest(TestCase):
    def setUp(self):
        # 1. Create a parent Event (Required by your ForeignKey in models.py)
        self.event_poly = Polygon(((0, 0), (0, 100), (100, 100), (100, 0), (0, 0)))
        self.event = Event.objects.create(
            event_name="Wayanad Festival",
            location_boundary=self.event_poly,
            event_date=timezone.now().date(),
            event_time=timezone.now().time()
        )

        # 2. Create a specific Zone inside that event
        self.zone_poly = Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
        self.zone = Zone.objects.create(
            event=self.event,
            zone_name="Main Stage", 
            location_boundary=self.zone_poly
        )
        
        # 3. Create an Attendee linked to the event
        self.user = Attendee.objects.create(
            event=self.event,
            name="Akhil Sebastian", 
            mobile_no="+9100000000"
        )

    def test_attendee_in_zone(self):
        """Verify that an attendee inside the polygon is counted correctly."""
        # Log a location INSIDE the polygon (5,5)
        AttendeeLocationLog.objects.create(
            attendee=self.user,
            location=Point(5, 5)
        )
        
        # Perform the spatial lookup using the 'within' filter
        count = AttendeeLocationLog.objects.filter(
            location__within=self.zone.location_boundary
        ).count()
        
        self.assertEqual(count, 1, "The attendee at (5,5) must be inside the Main Stage zone.")

    def test_attendee_outside_zone(self):
        """Verify that an attendee outside the polygon is NOT counted."""
        # Log a location OUTSIDE the polygon (25,25)
        AttendeeLocationLog.objects.create(
            attendee=self.user,
            location=Point(25, 25)
        )
        
        # The count should remain 0 for this specific zone
        count = AttendeeLocationLog.objects.filter(
            location__within=self.zone.location_boundary
        ).count()
        
        self.assertEqual(count, 0, "The attendee at (25,25) should NOT be inside the Main Stage zone.")