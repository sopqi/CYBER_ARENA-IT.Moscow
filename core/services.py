import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_TOKEN = "mgk_live_j5lukmrzolrpbzlktyssxtk26ffzgjx7iqexo6f3gvbw3nas36ka"
BASE_URL = "https://api.mgkeit.space/api/v1"

DAYS_MAP = {
    0: "Понедельник", 1: "Вторник", 2: "Среда",
    3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"
}

#небошой обход типа крутые
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_groups_by_building(building_name):
    url = f"{BASE_URL}/groups"

    payload = {
        "building": building_name,
        "total": 100,
        "limit": 500,
        "offset": 0,
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            groups_raw = data.get("groups", [])
            clean_groups = [i.split()[0] for i in groups_raw]
            return sorted(list(set(clean_groups)))

        print(f"API error groups: {response.status_code} - {response.text}")
        return []

    except Exception as e:
        print(f"connection error group: {e}")
        return []


def get_student_schedule(group_name, date_obj):
    url = f"{BASE_URL}/timetable"
    weekday_index = date_obj.weekday()
    if weekday_index == 6:
        return []

    payload = {
        "limit": 500,
        "offset": 0,
        "group": group_name
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=15, verify=False)
        print(response.json())
        print(group_name)
        if response.status_code != 200:
            print(f"API error timetable: {response.text}")
            return []

        json_response = response.json()
        busy_slots = []

        for day_data in json_response.get('data', []):
            if day_data.get('day_index') == weekday_index:
                for unit in day_data.get('units', []):
                    start_time = unit.get('start')
                    end_time = unit.get('end')
                    if start_time and end_time:
                        busy_slots.append({'start': start_time, 'end': end_time})
        return busy_slots

    except Exception as e:
        print(f"ошибка в парсинге расписания: {e}")
        return