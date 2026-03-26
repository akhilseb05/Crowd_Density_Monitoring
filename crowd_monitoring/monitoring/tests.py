from django.test import TestCase
from django.contrib.gis.geos import Point, Polygon
from django.utils import timezone
import json
from django.urls import reverse
import base64
from django.test import SimpleTestCase
from unittest.mock import patch
from .views import generate_qr_base64
from .models import Zone, AttendeeLocationLog, Attendee, Event, Admin

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

class AdvancedCrowdDensityTest(TestCase):
    def setUp(self):
        self.event_poly = Polygon(((0, 0), (0, 100), (100, 100), (100, 0), (0, 0)))
        self.event = Event.objects.create(
            event_name="Wayanad Festival",
            location_boundary=self.event_poly,
            event_date=timezone.now().date(),
            event_time=timezone.now().time()
        )

        # Create two distinct zones
        self.zone_a = Zone.objects.create(
            event=self.event,
            zone_name="Main Stage", 
            location_boundary=Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
        )
        self.zone_b = Zone.objects.create(
            event=self.event,
            zone_name="Food Court", 
            location_boundary=Polygon(((20, 20), (20, 30), (30, 30), (30, 20), (20, 20)))
        )
        
        self.user1 = Attendee.objects.create(event=self.event, name="User One", mobile_no="+9100000001")
        self.user2 = Attendee.objects.create(event=self.event, name="User Two", mobile_no="+9100000002")

    def test_multiple_zones_isolation(self):
        """Ensure counting attendees in one zone doesn't bleed into another."""
        AttendeeLocationLog.objects.create(attendee=self.user1, location=Point(5, 5))   # In Zone A
        AttendeeLocationLog.objects.create(attendee=self.user2, location=Point(25, 25)) # In Zone B
        
        count_a = AttendeeLocationLog.objects.filter(location__within=self.zone_a.location_boundary).count()
        count_b = AttendeeLocationLog.objects.filter(location__within=self.zone_b.location_boundary).count()
        
        self.assertEqual(count_a, 1)
        self.assertEqual(count_b, 1)

    def test_point_on_boundary(self):
        """Check behavior when an attendee is exactly on the polygon boundary line."""
        # Point (10, 5) is exactly on the right edge of Zone A
        AttendeeLocationLog.objects.create(attendee=self.user1, location=Point(10, 5))
        
        # Note: 'within' strictly requires being inside. 'intersects' includes boundaries.
        # This test ensures you know exactly how your chosen spatial lookup behaves.
        count_within = AttendeeLocationLog.objects.filter(location__within=self.zone_a.location_boundary).count()
        count_intersects = AttendeeLocationLog.objects.filter(location__intersects=self.zone_a.location_boundary).count()
        
        self.assertEqual(count_within, 0, "Point on boundary is not 'within'")
        self.assertEqual(count_intersects, 1, "Point on boundary 'intersects'")


class ApiEndpointTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            event_name="Tech Fest",
            location_boundary=Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0))),
            event_date=timezone.now().date(),
            event_time=timezone.now().time()
        )

    def test_register_attendee_api_success(self):
        """Test the attendee registration API with valid JSON payload."""
        payload = {
            "event_id": self.event.id,
            "name": "Test User",
            "phone": "9876543210",
            "email": "test@example.com",
            "accompanies": 2
        }
        

        response = self.client.post(
            reverse('register_api'), 
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(Attendee.objects.count(), 1)
        
        # Verify the phone number was formatted correctly with +91
        attendee = Attendee.objects.first()
        self.assertEqual(attendee.mobile_no, "+919876543210")

    def test_update_location_api(self):
        """Test that the API successfully creates/updates a location log."""
        attendee = Attendee.objects.create(
            event=self.event, name="Tracker User", mobile_no="+919999999999"
        )
        
        payload = {
            "attendee_id": attendee.id,
            "lat": 10.5,
            "lng": 76.2
        }
        
        response = self.client.post(
            reverse('update_location_api'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AttendeeLocationLog.objects.count(), 1)
        
        log = AttendeeLocationLog.objects.first()
        # Verify X and Y mapped correctly to Lng and Lat
        self.assertEqual(log.location.x, 76.2)
        self.assertEqual(log.location.y, 10.5)

class AdminAuthTests(TestCase):
    def setUp(self):
        self.admin = Admin.objects.create(
            name="superadmin",
            password="securepassword123",
            contact_no="1234567890"
        )

    def test_admin_login_success(self):
        """Test successful login sets session variables."""
        response = self.client.post(reverse('admin_login'), {
            'name': 'superadmin',
            'password': 'securepassword123'
        })
        
        # Should redirect to event_list on success
        self.assertRedirects(response, reverse('event_list'))
        self.assertEqual(self.client.session.get('admin_id'), self.admin.id)

    def test_admin_login_failure(self):
        """Test incorrect credentials prevent login."""
        response = self.client.post(reverse('admin_login'), {
            'name': 'superadmin',
            'password': 'wrongpassword'
        })
        
        # Should stay on the login page (200 OK)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('admin_id', self.client.session)

    def test_protected_view_redirect(self):
        """Test that accessing a protected view without session redirects to login."""
        # Attempt to access event_list without logging in
        response = self.client.get(reverse('event_list'))
        self.assertRedirects(response, reverse('admin_login'))


class UtilityFunctionTests(SimpleTestCase):
    def test_generate_qr_base64_returns_valid_string(self):
        """Test that the QR generator returns a valid base64 string."""
        test_url = "https://example.com/invite"
        
        # Call the function
        result = generate_qr_base64(test_url)
        
        # 1. Check that it returns a string
        self.assertIsInstance(result, str)
        
        # 2. Check that the string is actually valid base64
        try:
            # If this fails, it will throw an exception and fail the test
            decoded_bytes = base64.b64decode(result)
            self.assertTrue(len(decoded_bytes) > 0)
        except Exception:
            self.fail("generate_qr_base64 did not return a valid base64 encoded string.")

class AlertSystemTests(TestCase):
    def setUp(self):
        # 1. Set up an Admin session so we can access the view
        self.admin = Admin.objects.create(name="admin", password="pass", contact_no="123")
        session = self.client.session
        session['admin_id'] = self.admin.id
        session.save()

        # 2. Set up the Event and Zone
        self.event = Event.objects.create(
            event_name="Wayanad Festival",
            location_boundary=Polygon(((0, 0), (0, 100), (100, 100), (100, 0), (0, 0))),
            event_date=timezone.now().date(),
            event_time=timezone.now().time()
        )
        self.zone = Zone.objects.create(
            event=self.event,
            zone_name="Main Stage", 
            location_boundary=Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
        )
        
        # 3. Create an Attendee standing INSIDE the zone
        self.attendee = Attendee.objects.create(
            event=self.event, name="Akhil", mobile_no="+919988776655"
        )
        AttendeeLocationLog.objects.create(
            attendee=self.attendee, location=Point(5, 5) # Inside Main Stage
        )

    # Patch the Twilio Client where it is IMPORTED in your views.py
    @patch('monitoring.views.Client') 
    def test_send_alerts_twilio_mock(self, mock_twilio_client):
        """Test that sending an alert triggers the Twilio client correctly without sending a real SMS."""
        
        # Setup the mock to return a dummy message object
        mock_messages = mock_twilio_client.return_value.messages
        mock_messages.create.return_value.sid = "SMXXXXX"

        # The payload simulating the admin filling out the alert form
        payload = {
            'zone': self.zone.id,
            'recipient_type': 'attendee',
            'message': 'Please move to the exits.'
        }

        # Fire the request!
        # Assuming your URL is something like /event/<id>/alerts/
        response = self.client.post(reverse('send_alerts', args=[self.event.id]), data=payload)

        # 1. Verify the view processed successfully (should redirect back to the alerts page)
        self.assertEqual(response.status_code, 302)

        # 2. CRITICAL: Verify Twilio was actually called!
        self.assertTrue(mock_messages.create.called)

        # 3. Verify Twilio was called with the correct phone number and message
        # We extract the arguments passed to the mock Twilio client
        call_kwargs = mock_messages.create.call_args.kwargs
        
        self.assertEqual(call_kwargs['to'], "+919988776655")
        self.assertIn("Please move to the exits.", call_kwargs['body'])
        self.assertIn("Wayanad Festival", call_kwargs['body'])

