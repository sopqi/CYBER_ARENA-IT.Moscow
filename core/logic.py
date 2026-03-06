import datetime
from django.utils import timezone


def generate_available_slots(user_schedule, pc_bookings):
    if user_schedule is None:
        user_schedule = []

    now = timezone.localtime(timezone.now())
    end_of_day = now.replace(hour=18, minute=0, second=0, microsecond=0)

    lessons = []
    for item in user_schedule:
        try:
            start = timezone.make_aware(
                datetime.datetime.combine(now.date(), datetime.datetime.strptime(item['start'], "%H:%M").time()))
            end = timezone.make_aware(
                datetime.datetime.combine(now.date(), datetime.datetime.strptime(item['end'], "%H:%M").time()))
            lessons.append({'start': start, 'end': end})
        except:
            continue
    lessons.sort(key=lambda x: x['start'])

    free_windows = []

    if lessons and now < lessons[0]['start']:
        free_windows.append({'start': now, 'end': lessons[0]['start'], 'type': 'window'})

    for i in range(len(lessons) - 1):
        gap_start = lessons[i]['end']
        gap_end = lessons[i + 1]['start']
        if gap_end > now and gap_end > gap_start:

            diff = (gap_end - gap_start).total_seconds() / 60
            if diff > 5:
                free_windows.append({
                    'start': max(gap_start, now),
                    'end': gap_end,
                    'type': 'break' if diff <= 45 else 'window'
                })

    last_lesson_end = lessons[-1]['end'] if lessons else now
    if last_lesson_end < end_of_day:
        free_windows.append({
            'start': max(last_lesson_end, now),
            'end': end_of_day,
            'type': 'after_classes'
        })

    final_slots = []
    for window in free_windows:
        win_start = window['start']
        win_end = window['end']

        if window['type'] == 'break':
            final_slots.append(create_slot_dict(win_start, win_end, is_break=True))
        else:
            temp_start = win_start
            while temp_start + datetime.timedelta(minutes=30) <= win_end:
                temp_end = temp_start + datetime.timedelta(hours=1)
                if temp_end > win_end:
                    temp_end = win_end

                final_slots.append(create_slot_dict(temp_start, temp_end))
                temp_start = temp_end

    valid_slots = []
    for slot in final_slots:
        slot_start = timezone.make_aware(datetime.datetime.strptime(slot['start_value'], "%Y-%m-%dT%H:%M"))
        slot_end = timezone.make_aware(datetime.datetime.strptime(slot['end_value'], "%Y-%m-%dT%H:%M"))

        conflict = False
        for b in pc_bookings:
            if slot_start < b.end_time and slot_end > b.start_time:
                conflict = True
                break
        if not conflict:
            valid_slots.append(slot)

    return valid_slots


def create_slot_dict(start, end, is_break=False):
    duration = int((end - start).total_seconds() / 60)
    label = "ПЕРЕМЕНА" if is_break else "СЕАНС"
    return {
        'start_value': start.strftime("%Y-%m-%dT%H:%M"),
        'end_value': end.strftime("%Y-%m-%dT%H:%M"),
        'display': f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
        'info': f"{label} ({duration} мин)"
    }