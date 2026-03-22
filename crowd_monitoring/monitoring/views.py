import json
import os
import csv
import qrcode
import base64
from io import BytesIO
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.gis.geos import GEOSGeometry, Point
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import localtime
from django.contrib import messages
from twilio.rest import Client
from .models import Admin, Event, Zone, Attendee, Manager, AttendeeLocationLog, ManagerLocationLog, Alert, CrowdLog


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
        
    events = Event.objects.all().order_by('-id') # Ordering to show newest first
    
    if request.method == "POST":
        # Handle Event Creation
        if 'create_event' in request.POST:
            name = request.POST.get('name')
            date = request.POST.get('date')
            time = request.POST.get('time')
            boundary_wkt = request.POST.get('boundary')
            
            if name and date and time and boundary_wkt:
                boundary_wkt = "POLYGON ((" + boundary_wkt + "))"
                try:
                    Event.objects.create(
                        event_name=name,
                        event_date=date,
                        event_time=time,
                        location_boundary=GEOSGeometry(boundary_wkt)
                    )
                except Exception as e:
                    print(f"Error creating event: {e}")
            
        # Handle Zone Creation
        elif 'create_zone' in request.POST:
            event_id = request.POST.get('event_id')
            zone_name = request.POST.get('zone_name')
            zone_boundary_wkt = request.POST.get('zone_boundary')
            
            if event_id and zone_name and zone_boundary_wkt:
                zone_boundary_wkt = "POLYGON ((" + zone_boundary_wkt + "))"
                try:
                    event = get_object_or_404(Event, id=event_id)
                    Zone.objects.create(
                        event=event,
                        zone_name=zone_name,
                        location_boundary=GEOSGeometry(zone_boundary_wkt)
                    )
                except Exception as e:
                    print(f"Error creating zone: {e}")

        # Handle Event Deletion
        elif 'delete_event' in request.POST:
            event_id = request.POST.get('event_id')            
            if event_id:
                event = get_object_or_404(Event, id=event_id)
                event.delete()
            
        return redirect('event_list')

    return render(request, 'event_list.html', {'events': events})

def dashboard(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
    event = get_object_or_404(Event, id=event_id)
    
    zones = event.zones.all()
    for zone in zones:
        # Check how many attendee points are inside this zone's polygon
        count = AttendeeLocationLog.objects.filter(
            location__within=zone.location_boundary
        ).count()
        
        # Save the new count to the database
        zone.current_count = count
        zone.save()
         
    # Fetching logs for the heatmap dots
    attendee_logs = AttendeeLocationLog.objects.filter(attendee__event=event)
    manager_logs = ManagerLocationLog.objects.filter(manager__event=event)

    active_attendees_count = attendee_logs.count()
    active_managers_count = manager_logs.count()
    map_data = []
    for log in attendee_logs:
        map_data.append({'lat': log.location.y, 'lng': log.location.x, 'role': 'attendee'})
    for log in manager_logs:
        map_data.append({'lat': log.location.y, 'lng': log.location.x, 'role': 'manager'})

    context = {
        'event': event,
        'total_attendees': active_attendees_count,
        'total_managers': active_managers_count,
        'zones': event.zones.all(),
        'map_data_json': json.dumps(map_data),
    }
    return render(request, 'dashboard.html', context)



def send_alerts(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
    # Fetch the specific event
    event = get_object_or_404(Event, id=event_id)
    zones = event.zones.all()
    
    if request.method == "POST":
        zone_id = request.POST.get('zone')
        recipient_type = request.POST.get('recipient_type')
        message_text = request.POST.get('message')
        
        selected_zone = get_object_or_404(Zone, id=zone_id)
        cutoff = timezone.now() - timedelta(minutes=5)
        
        # Twilio setup,account details are stored in .env file
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')

        client = Client(account_sid, auth_token)
        # Filter active people ONLY in the selected zone of THIS event
        recipients = []
        if recipient_type == 'attendee':
            logs = AttendeeLocationLog.objects.filter(
                attendee__event=event,
                log_timestamp__gte=cutoff,
                location__within=selected_zone.location_boundary
            ).select_related('attendee').distinct('attendee')
            recipients = [log.attendee.mobile_no for log in logs]
        else:
            logs = ManagerLocationLog.objects.filter(
                manager__event=event,
                log_timestamp__gte=cutoff,
                location__within=selected_zone.location_boundary
            ).select_related('manager').distinct('manager')
            recipients = [log.manager.mobile_no for log in logs]

        # Send and Log
        success_count = 0
        for phone in recipients:
            try:
                client.messages.create(
                    body=f"\n{event.event_name} ALERT \n ZONE : {selected_zone.zone_name}: \n\n{message_text}",
                    from_=twilio_number,
                    to=phone 
                )
                success_count += 1
            except Exception as e:
                print(f"Error sending to {phone}: {e}")

        Alert.objects.create(zone=selected_zone, recipient_type=recipient_type, alert_message=message_text)
        messages.success(request, f"Alert sent to {success_count} recipients!")
        return redirect('send_alerts', event_id=event_id)

    return render(request, 'alerts.html', {'event': event, 'zones': zones})

def event_analytics(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
    
    event = get_object_or_404(Event, id=event_id)
    zones = event.zones.all()
    
    all_logs = CrowdLog.objects.filter(event=event).order_by('timestamp')
    
    # Extract unique timestamps for the X-Axis (formatted as HH:MM)
    time_labels = list(dict.fromkeys([localtime(log.timestamp).strftime('%H:%M') for log in all_logs]))

    total_logs = all_logs.filter(zone__isnull=True)
    total_data = [log.person_count for log in total_logs]

    zone_datasets = []
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', "#8CF405FF", "#F405ECFF"] 
    
    for index, zone in enumerate(zones):
        z_logs = all_logs.filter(zone=zone)
        zone_datasets.append({
            'label': zone.zone_name,
            'data': [log.person_count for log in z_logs],
            'borderColor': colors[index % len(colors)],
            'backgroundColor': colors[index % len(colors)],
            'fill': False,
            'tension': 0.3 # Adds a slight curve to the lines
        })

    context = {
        'event': event,
        'time_labels': json.dumps(time_labels),
        'total_data': json.dumps(total_data),
        'zone_datasets': json.dumps(zone_datasets),
    }
    
    return render(request, 'analytics.html', context)

def export_event_analytics_csv(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
        
    event = get_object_or_404(Event, id=event_id)
    
    # Create the HttpResponse object with the appropriate CSV headers.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{event.event_name.replace(" ", "_")}_Analytics.csv"'},
    )


    writer = csv.writer(response)
    
    writer.writerow(['Date', 'Time', 'Event Name', 'Zone Name', 'Person Count'])

    logs = CrowdLog.objects.filter(event=event).order_by('timestamp')

    # Write data rows
    for log in logs:
        date_str = localtime(log.timestamp).strftime('%Y-%m-%d')
        time_str = localtime(log.timestamp).strftime('%H:%M:%S')
        
        # If zone is None, label it as 'Total Event Crowd'
        zone_name = log.zone.zone_name if log.zone else "Total Event Crowd"
        
        writer.writerow([date_str, time_str, event.event_name, zone_name, log.person_count])

    return response


def get_events_api(request):
    events = Event.objects.all().values('id', 'event_name')
    
    return JsonResponse(list(events), safe=False)
    
@csrf_exempt
def register_attendee_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event = get_object_or_404(Event, id=data.get('event_id'))
            
            attendee = Attendee.objects.create(
                event = event,
                name = data.get('name'),
                mobile_no = "+91" + data.get('phone'),
                email_id = data.get('email'),
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
            location = Point(float(data.get('lng')), float(data.get('lat')))
            AttendeeLocationLog.objects.update_or_create(
                attendee=attendee,
                defaults={'location': location}
            )
            return JsonResponse({'status': 'updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
@csrf_exempt
def register_manager_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event = get_object_or_404(Event, id=data.get('event_id'))
            
            manager = Manager.objects.create(
                event = event,
                manager_name = data.get('manager_name'),
                manager_role = data.get('manager_role'),
                mobile_no = "+91" + data.get('mobile_no'), 
                email_id = data.get('email_id')
            )
            return JsonResponse({'status': 'success', 'manager_id': manager.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def update_manager_location_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            manager = get_object_or_404(Manager, id=data.get('manager_id'))
            
            location = Point(float(data.get('lng')), float(data.get('lat')))
            
            ManagerLocationLog.objects.update_or_create(
                manager=manager,
                defaults={'location': location}
            )
            return JsonResponse({'status': 'updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        

def generate_qr_base64(data):
    """Generates a QR code and returns it as a base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def invite_share(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('admin_login')
        
    event = get_object_or_404(Event, id=event_id)
    
    attendee_link = "https://github.com/akhil-codec/CrowdDense/blob/main/APK/Attendee_Registration_App/Attendee_Registration.apk"
    manager_link = "https://github.com/akhil-codec/CrowdDense/blob/main/APK/Manager_Registration_App/Manager_Registration.apk"
    
    context = {
        'event': event,
        'attendee_link': attendee_link,
        'manager_link': manager_link,
        'attendee_qr': generate_qr_base64(attendee_link),
        'manager_qr': generate_qr_base64(manager_link),
    }
    
    return render(request, 'invite.html', context)