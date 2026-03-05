import datetime
from django.utils import timezone

def generate_available_slots(user_schedule, pc_bookings):
    if user_schedule is None:
        user_schedule =[]

    now = timezone.localtime(timezone.now())
    slots =[]
    end_of_day = now.replace(hour=18, minute =00, second=0, microsecond=0)
    current_hour = now.replace(minute=0, second=0, microsecond=0)

    if now.minute > 0:
        current_hour += datetime.timedelta(hours=1)

    current_slot_start = current_hour

    while current_slot_start < end_of_day:
        current_slot_end = current_slot_start + datetime.timedelta(hours=1)
        is_conflict = False
#проверка идут ли пары
        for lesson in user_schedule:
            try:
                l_start_time = datetime.datetime.strptime(lesson['start'], "%H:%M").time()
                l_end_time = datetime.datetime.strptime(lesson['end'], "%H:%M").time()
                l_start = timezone.make_aware(datetime.datetime.combine(now.date(), l_start_time))
                l_end = timezone.make_aware(datetime.datetime.combine(now.date(), l_end_time))

                if current_slot_start < l_end and current_slot_end > l_start:
                    is_conflict = True
                    break

            except ValueError:
                continue

#проверка броней
        if not is_conflict:
            for booking in pc_bookings:
                if current_slot_start < booking.end_time and current_slot_end > booking.start_time:
                    is_conflict = True
                    break

        if not is_conflict:
            slots.append({
                'start_value': current_slot_start.strftime("%Y-%m-%dT%H:%M"),
                'end_value': current_slot_end.strftime("%Y-%m-%dT%H:%M"),
                'display': f"{current_slot_start.strftime('%H:%M')} - {current_slot_end.strftime('%H:%M')}"
            })

        current_slot_start = current_slot_end

    return slots