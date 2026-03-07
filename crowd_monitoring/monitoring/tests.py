from django.test import TestCase

# Create your tests here.
from django.contrib.gis.geos import Point, Polygon
from .models import Zone, AttendeeLocationLog, Attendee

class CrowdDensityTest(TestCase):
    def setUp(self):
        # 1. Create a sample Zone (A square polygon)
        self.poly = Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
        self.zone = Zone.objects.create(zone_name="Main Stage", location_boundary=self.poly)
        
        # 2. Create an Attendee
        self.user = Attendee.objects.create(name="Akhil", mobile_no="+9100000000")

    def test_attendee_in_zone(self):
        # 3. Log a location INSIDE the polygon (5,5)
        AttendeeLocationLog.objects.create(
            attendee=self.user,
            location=Point(5, 5)
        )
        
        # 4. Assert: Check if the logic counts them correctly
        # This simulates your dashboard query
        count = AttendeeLocationLog.objects.filter(location__within=self.zone.location_boundary).count()
        self.assertEqual(count, 1)