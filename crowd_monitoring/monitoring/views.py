import json
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.gis.geos import GEOSGeometry, Point
from django.views.decorators.csrf import csrf_exempt
from .models import Admin, Event, Zone, Attendee, Manager, AttendeeLocationLog, ManagerLocationLog


def admin_login(request):
    if request.method == "POST":
        admin_name = request.POST.get('name')
        admin_password = request.POST.get('password')
        
        # Verify credentials against your Admin model
        try:
            admin_user = Admin.objects.get(name=admin_name, password=admin_password)
            request.session['admin_id'] = admin_user.id
            request.session['admin_name'] = admin_user.name
            return redirect('event_list')
        except Admin.DoesNotExist:
            messages.error(request, "Invalid Name or Password")
            
    return render(request, 'admin_login.html')

def admin_logout(request):
    """Clears the admin session and redirects to the login page."""
    request.session.flush()
    return redirect('admin_login')

def event_list(request):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
    events = Event.objects.all()
    
    if request.method == "POST":
        # Check which form was submitted
        if 'create_event' in request.POST:
            name = request.POST.get('name')
            date = request.POST.get('date')
            time = request.POST.get('time')
            boundary_wkt = request.POST.get('boundary')
            boundary_wkt = "POLYGON ((" + boundary_wkt + "))"
            # Validation to prevent IntegrityError (null values)
            if name and date and time and boundary_wkt:
                try:
                    Event.objects.create(
                        event_name=name,
                        event_date=date,
                        event_time=time,
                        location_boundary=GEOSGeometry(boundary_wkt)
                    )
                except Exception as e:
                    print(f"Error creating event: {e}")
            
        elif 'create_zone' in request.POST:
            event_id = request.POST.get('event_id')
            zone_name = request.POST.get('zone_name')
            zone_boundary_wkt = request.POST.get('zone_boundary')
            zone_boundary_wkt = "POLYGON ((" + zone_boundary_wkt + "))"
            if event_id and zone_name and zone_boundary_wkt:
                try:
                    event = get_object_or_404(Event, id=event_id)
                    Zone.objects.create(
                        event=event,
                        zone_name=zone_name,
                        location_boundary=GEOSGeometry(zone_boundary_wkt)
                    )
                except Exception as e:
                    print(f"Error creating zone: {e}")
            
        return redirect('event_list')

    return render(request, 'event_list.html', {'events': events})

def dashboard(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
    event = get_object_or_404(Event, id=event_id)
    
    zones = event.zones.all()
    for zone in zones:
        # Check how many attendee points are inside this zone's polygon
        # 'location__within' is the GeoDjango spatial filter
        count = AttendeeLocationLog.objects.filter(
            location__within=zone.location_boundary
        ).count()
        
        # Save the new count to the database
        zone.current_count = count
        zone.save()
         
    # Fetching logs for the heatmap dots
    attendee_logs = AttendeeLocationLog.objects.filter(attendee__event=event)
    manager_logs = ManagerLocationLog.objects.filter(manager__event=event)
    
    map_data = []
    for log in attendee_logs:
        map_data.append({'lat': log.location.y, 'lng': log.location.x, 'role': 'attendee'})
    for log in manager_logs:
        map_data.append({'lat': log.location.y, 'lng': log.location.x, 'role': 'manager'})

    context = {
        'event': event,
        'total_attendees': event.attendees.count(),
        'total_managers': event.managers.count(),
        'zones': event.zones.all(),
        'map_data_json': json.dumps(map_data),
    }
    return render(request, 'dashboard.html', context)

def attendee_app(request):
    # Fetch all events so the user can choose one in the dropdown
    all_events = Event.objects.all() 
    return render(request, 'attendee_app.html', {'events': all_events})


# # API to register the user
# @csrf_exempt
# def register_attendee_api(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         event_obj = get_object_or_404(Event, id=data.get('event_id'))
#         attendee = Attendee.objects.create(
#             name=data.get('name'),
#             mobile_no=data.get('phone'),
#             event=event_obj,
#             consent_status = True,
#             no_of_accompanies = 1,
#             email_id = "sui123@gmail.com"
#         )
#         return JsonResponse({'status': 'success', 'attendee_id': attendee.id})

# # API to receive GPS updates
# @csrf_exempt
# def update_location_api(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         attendee = get_object_or_404(Attendee, id=data.get('attendee_id'))
#         # Note: Point(longitude, latitude)
#         location = Point(float(data.get('lng')), float(data.get('lat')))
#         AttendeeLocationLog.objects.update_or_create(
#             attendee=attendee,
#             defaults={'location': location}
#         )
#         return JsonResponse({'status': 'updated'})

def get_events_api(request):
    """Returns a list of all events so the Android Spinner can show them."""
    events = Event.objects.all().values('id', 'event_name')
    
    # You must convert the QuerySet to a list and return it as a JsonResponse
    return JsonResponse(list(events), safe=False)
    
@csrf_exempt
def register_attendee_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event = get_object_or_404(Event, id=data.get('event_id'))
            
            attendee = Attendee.objects.create(
                event=event,
                name=data.get('name'),
                mobile_no=data.get('phone'),
                email_id=data.get('email'),
                consent_status = True,
                no_of_accompanies=int(data.get('accompanies', 0))
            )
            return JsonResponse({'status': 'success', 'attendee_id': attendee.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def update_location_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attendee = get_object_or_404(Attendee, id=data.get('attendee_id'))
            # Note: Point(longitude, latitude)
            location = Point(float(data.get('lng')), float(data.get('lat')))
            AttendeeLocationLog.objects.update_or_create(
                attendee=attendee,
                defaults={'location': location}
            )
            return JsonResponse({'status': 'updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)