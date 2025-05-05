import requests
import concurrent.futures
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------
# API Configuration
# ----------------------------
AUTH_URL = "http://101.101.63.49/api/authenticate"
DELETE_URL = "http://101.101.63.49/api/devices"
# ----------------------------
# Function to get bearer token
# ----------------------------
def get_auth_token():
    headers = {"Content-Type" : "application/x-www-form-urlencoded", 'Authorization': "Basic dmNlbTpmcmVlQGMkMSE="}
    data = {"grant_type": "password", "username": "perf_test", "password": "vC3m.123!"}

    response = requests.post(AUTH_URL, headers=headers, data=data, verify=False)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Authentication failed! Status Code: {response.status_code}")
        exit(1)

# ----------------------------
# Function to delete a single device
# ----------------------------
def delete_device(device_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{DELETE_URL}/{device_id}"

    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 204:
        print(f"{device_id} ---- deleted")
    else:
        print(f"{device_id} ---- failed (Status Code: {response.status_code})")

# ----------------------------
# Function to generate device IDs and delete them
# ----------------------------
def delete_devices(token, user_range):
    prefix = "1878D4-vSpeed-NUC-simulator-BOT"
    base_ranges = [0, 25000, 52141]

    all_device_ids = []

    for base in base_ranges:
        start = base
        end = base + int(user_range)
        device_ids = [f"{prefix}{num:06d}" for num in range(start, end + 1)]
        all_device_ids.extend(device_ids)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda device_id: delete_device(device_id, token), all_device_ids)

# ----------------------------
# Main Execution
# ----------------------------
token = get_auth_token()
user_input = input("Enter the range : ")

if user_input.isdigit():
    delete_devices(token, int(user_input))
else:
    print("Invalid input.")
