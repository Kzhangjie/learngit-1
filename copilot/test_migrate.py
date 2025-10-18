from pprint import pprint

import requests

headers = {
    "X-Cc-Region": "feat_hot_cold",
    "Cookie": "wps_sid=",
    "Host": "lingxi.wps.cn",
}


def print_response(response):
    print("Status Code:", response.status_code)
    print("x-request-id:", response.headers.get("x-request-id"))
    print("Response Body:", response.text)


def migrate_session(session_id):
    url = f"https://120.92.124.158/api/aigc/admin/cc/developer/migrate_data/sessions/{session_id}"
    data = "{}"
    response = requests.post(url, headers=headers, data=data, verify=False)
    print_response(response)


def recovery_session(session_id):
    url = f"https://120.92.124.158/api/aigc/admin/cc/developer/migrate_data/sessions/{session_id}/recovery"
    data = "{}"
    response = requests.post(url, headers=headers, data=data, verify=False)
    print_response(response)


def migrate_date(begin_time="2024-08-11", end_time="2024-08-12"):
    url = f"https://120.92.124.158/api/aigc/admin/cc/developer/migrate_data"
    data = {
        "begin_time": begin_time,
        "end_time": end_time,
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    print_response(response)


def cancel():
    url = f"https://120.92.124.158/api/aigc/admin/cc/developer/migrate_data"
    data = "{}"
    response = requests.delete(url, headers=headers, json=data, verify=False)
    print_response(response)


def download_session(session_id):
    url = f"https://120.92.124.158/api/aigc/admin/cc/developer/migrate_data/sessions/{session_id}"
    data = "{}"
    response = requests.get(url, headers=headers, data=data, verify=False)
    print_response(response)
    url = response.json().get("data")
    if url:
        response = requests.get(url)
        pprint(response.json())
    else:
        print("No data to download.")


# session_id = "8352842156933312"
# migrate_session(session_id)
# download_session(session_id)
# recovery_session(session_id)
cancel()
migrate_date(begin_time="2024-08-09", end_time="2025-01-15")
#
