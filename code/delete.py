import requests
import concurrent.futures

# API URL
DELETE_URL = "http://101.101.63.49/api/devices"

# Function to get auth token
def get_auth_token():
    url = "http://101.101.63.49/api/authenticate"
    headers = {"Content-Type" : "application/x-www-form-urlencoded", 'Authorization': "Basic dmNlbTpmcmVlQGMkMSE="}
    data = {"grant_type": "password", "username": "perf_test", "password": "vC3m.123!"}

    response = requests.post(url, headers=headers, data=data, verify=False)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Authentication failed! Status Code: {response.status_code}, Response: {response.text}")
        exit(1)

# Function to delete a single device
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
        print(f"{device_id} ---- failed (Status Code: {response.status_code}, Response: {response.text})")

# Function to delete devices using threading (no max_workers specified)
def delete_devices(token, start_range, end_range):
    prefix = "1878D4-vSpeed-NUC-simulator-BOT"
    start_num = int(start_range)
    end_num = int(end_range)

    device_ids = [f"{prefix}{num:06d}" for num in range(start_num, end_num + 1)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda device_id: delete_device(device_id, token), device_ids)

# Get token
token = get_auth_token()

# Example: User inputs 45 → Deletes from BOT000000 to BOT000045
start_input = 50000              #input("enter the start device number")
end_input = 500004                  #input("enter the end device number")
#input("Enter the range ... ")
delete_devices(token, start_input, end_input)














































































# import requests
# import urllib3
# import concurrent.futures

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DEL_URL = "http://101.101.63.49/api/devices"

# def get_auth_token():
#     url = "http://101.101.63.49/api/authenticate"
#     headers = {"Content-Type" : "application/x-www-form-urlencoded", 'Authorization': "Basic dmNlbTpmcmVlQGMkMSE="}
#     data = {"grant_type": "password", "username": "perf_test", "password": "vC3m.123!"}

#     response = requests.post(url, headers=headers, data=data, verify=False)

#     if response.status_code == 200:
#         token = response.json().get("access_token", "")
#         return token
#     else:
#         print(f"Failed to get token, status code: {response.status_code}")
#         exit(1)


# def delete_devices(token, end_range):
#     headers = {"Authorization": f"Bearer {token}",
#                "Content-Type": "application/json"
#     }
#     url = f"{DEL_URL}/{device_id}"
    
        



#     response = requests.delete( url, headers=headers, verify=False)
#     if response.status_code == 204:
#         print(f"Device {device_id} deleted successfully")       
#     else:
#         print(f"Failed to delete device {device_id}, status code: {response.status_code}")

# def delete_devices(token, end_range):
#     prefix = "1878D4-vSpeed-NUC-simulator-BOT"
#     start_num = 0
#     end_num = int(end_range)
#     device_id = [f"{prefix}{num:06d}"  for num in range(start_num, end_num + 1)]

#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         executor.map(lambda device_id: delete_device(device_id, token), device_id)

                  
# token = get_auth_token()

# user_input = input("enter the end number ..  ")

# delete_devices(token, user_input)
        

