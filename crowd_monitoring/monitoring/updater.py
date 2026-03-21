# your_app/updater.py
import os
from datetime import timedelta
from django.utils import timezone
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events

def auto_check_density_and_alert():
    # Keep imports inside the function so migrations don't crash
    from .models import Zone, AttendeeLocationLog, ManagerLocationLog, Alert

    now = timezone.now()
    cutoff = now - timedelta(minutes=5)  
    DENSITY_THRESHOLD = 0.02
    COOLDOWN_MINUTES = 5
    DUMMY_NUMBER = "9876543210"
    
    AttendeeLocationLog.objects.filter(log_timestamp__lt=cutoff).delete()
    ManagerLocationLog.objects.filter(log_timestamp__lt=cutoff).delete()
    
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
    client = Client(account_sid, auth_token)

    now = timezone.now()
    cutoff = now - timedelta(minutes=COOLDOWN_MINUTES)
    
    for zone in Zone.objects.all():
        if Alert.objects.filter(zone=zone, timestamp__gte=cutoff).exists():
            continue

        attendee_logs = AttendeeLocationLog.objects.filter(
            log_timestamp__gte=cutoff,
            location__within=zone.location_boundary
        ).select_related('attendee').distinct('attendee')
        
        manager_logs = ManagerLocationLog.objects.filter(
            log_timestamp__gte=cutoff,
            location__within=zone.location_boundary
        ).select_related('manager').distinct('manager')
        
        attendee_phones = [log.attendee.mobile_no for log in attendee_logs]
        manager_phones = [log.manager.mobile_no for log in manager_logs]
        
        total_people = len(attendee_phones) + len(manager_phones)
        if total_people == 0:
            continue
        print(total_people)
        try:
            area_sq_meters = zone.location_boundary.transform(3857, clone=True).area
        except Exception as e:
            print(f"Spatial transform error: {e}")
            continue

        if area_sq_meters > 0 and (total_people / area_sq_meters) > DENSITY_THRESHOLD:
            message_text = f"EMERGENCY: High crowd density in {zone.zone_name}."
            all_phones = attendee_phones + manager_phones
            
            sms_sent = 0
            for phone in all_phones:
                if phone == DUMMY_NUMBER: continue
                try:
                    client.messages.create(body=message_text, from_=twilio_number, to=phone)
                    sms_sent += 1
                except Exception as e:
                    print(f"Twilio Error: {e}")
            
            Alert.objects.create(zone=zone, recipient_type='automated', alert_message=message_text)
            print(f"Alert logged for {zone.zone_name}. SMS sent: {sms_sent}")



def record_crowd_data():
    from .models import Event, Zone, CrowdLog, AttendeeLocationLog, ManagerLocationLog
    
    now = timezone.now()
    cutoff = now - timedelta(minutes=5)
    
    for event in Event.objects.all():
        total_attendees = AttendeeLocationLog.objects.filter(
            log_timestamp__gte=cutoff,
            location__within=event.location_boundary
        ).values('attendee').distinct().count()
        
        total_managers = ManagerLocationLog.objects.filter(
            log_timestamp__gte=cutoff,
            location__within=event.location_boundary
        ).values('manager').distinct().count()
        
        CrowdLog.objects.create(
            event=event,
            zone=None, 
            person_count=(total_attendees + total_managers),
            timestamp=now
        )
        
        for zone in event.zones.all():
            zone_attendees = AttendeeLocationLog.objects.filter(
                log_timestamp__gte=cutoff,
                location__within=zone.location_boundary
            ).values('attendee').distinct().count()
            
            zone_managers = ManagerLocationLog.objects.filter(
                log_timestamp__gte=cutoff,
                location__within=zone.location_boundary
            ).values('manager').distinct().count()
            
            CrowdLog.objects.create(
                event=event,
                zone=zone,
                person_count=(zone_attendees + zone_managers),
                timestamp=now
            )
            


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        auto_check_density_and_alert,
        trigger="interval",
        minutes=1,
        id="density_check",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.add_job(
        record_crowd_data,
        trigger="interval",
        minutes=10, 
        id="analytics_logger",
        max_instances=1,
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()