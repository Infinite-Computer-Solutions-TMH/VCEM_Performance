import requests
import json
import yaml
from rich.console import Console
import pandas as pd
import urllib3

console = Console()

def load_config(file_path="cfg.yaml"):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

# Generate device IDs from the YAML configuration
def generate_device_ids(api_config):
    prefix = api_config["devices"]["prefix"]
    device_ids = []
    for range_info in api_config["devices"]["ranges"]:
        start = range_info["start"]
        end = range_info["end"]
        device_ids.extend([f"{prefix}{num:06d}" for num in range(start, end + 1)])
    return device_ids

def authenticate(api_config):
    url = api_config["authenticate"]["url"]
    headers = api_config["authenticate"]["headers"]
    data = api_config["authenticate"]["payload"]
    response = requests.post(url, headers=headers, data=data, verify=False)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        console.print(f"[red]Authentication failed: {response.status_code}[/red]")
        return None
    
def get_parameters_values(device, auth_token, api_config, metrics):
    url = api_config["gpv"]["url"].format(device_id=device)
    headers = {**api_config["gpv"]["headers"], "Authorization": f"Bearer {auth_token}"}
    payload = json.dumps(api_config["gpv"]["payload"])
    response = requests.post(url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        print(f"GPV for {device} done")
        return response.json()
    else:
        console.print(f"[red]GPV failed for device {device}: {response.status_code}[/red]")

def set_parameters_values(device, auth_token, api_config, metrics):
    url = api_config["spv"]["url"].format(device_id=device)
    headers = {**api_config["spv"]["headers"], "Authorization": f"Bearer {auth_token}"}
    payload = json.dumps(api_config["spv"]["payload"])
    response = requests.post(url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        print(f" SPV for {device} done")
        return response.json()
    else:
        console.print(f"[red]spv failed for device {device}: {response.status_code}[/red]")

def extract_value_from_response(response):
    if response and "result" in response:
        for item in response["result"]:
            if "value" in item:
                return item["value"]
    return "N/A"

def process_device(device, auth_token, api_config, data_list, session):
    inititial_response = get_parameters_values(device, auth_token, api_config, session)
    if inititial_response is None:
        return
    if not set_parameters_values(device, auth_token, api_config, session):
        return
    
    final_response = get_parameters_values(device, auth_token, api_config, session)
    if final_response is None:
        return
    
    initial_value = extract_value_from_response(inititial_response)
    final_value = extract_value_from_response(final_response)

    data_list.append({
        "device": device,
        "initial_value": initial_value,
        "final_value": final_value
    })


config = load_config()
auth_token = authenticate(config)

if auth_token:
    devices = generate_device_ids(config)
    data_list = []

    with requests.Session() as session:
        for device in devices:
            process_device(device, auth_token, config, data_list, session)

    df = pd.DataFrame(data_list)

    excel_filename = "parameter_change.xlsx"
    df.to_excel(excel_filename, index=False, engine="openpyxl")

    console.print("[green]All operations completed")
else:
    console.print("[red]Authentication failed[/red]")






































































# import requests
# import json
# import yaml
# from rich.console import Console
# import urllib3

# console = Console()

# def load_config(file_path="cfg.yaml"):
#     with open(file_path, "r") as file:
#         return yaml.safe_load(file)
    
# def generate_device_ids(api_config):
#     prefix = api_config["devices"]["prefix"]
#     device_ids = []
#     for range_info in api_config["devices"]["ranges"]:
#         start = range_info["start"]
#         end = range_info["end"]
#         device_ids.extend([f"{prefix}{num:06d}" for num in range(start, end + 1)])
#     return device_ids

# def authenticate(api_config):
#     url = api_config["authenticate"]["url"]
#     headers = api_config["authenticate"]["headers"]
#     data = api_config["authenticate"]["payload"]
#     response = requests.post(url, headers=headers, data=data, verify=False)
#     if response.status_code == 200:
#         return response.json().get("access_token")
#     else:
#         console.print(f"[red]Authentication failed: {response.status_code}[/red]")
#         return None
    
# def get_parameters_values(device, auth_token, api_config, metrics):
#     url = api_config["gpv"]["url"].format(device_id=device)
#     headers = {**api_config["gpv"]["headers"], "Authorization": f"Bearer {auth_token}"}
#     payload = json.dumps(api_config["gpv"]["payload"])
#     response = requests.post(url, headers=headers, data=payload, verify=False)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         console.print(f"[red]GPV failed: {response.status_code}[/red]")

# def set_parameters_values(device, auth_token, api_config, metrics):
#     url = api_config["spv"]["url"].format(device_id=device)
#     headers = {**api_config["spv"]["headers"], "Authorization": f"Bearer {auth_token}"}
#     payload = json.dumps(api_config["spv"]["payload"])
#     response = requests.post(url, headers=headers, data=payload, verify=False)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         console.print(f"[red]spv failed: {response.status_code}[/red]")

# def process_device(device, auth_token, api_config, decument, session):
#     inititial_response = get_parameters_values(device, auth_token, api_config, session)
#     if inititial_response is None:
#         return
#     if not set_parameters_values(device, auth_token, api_config, session):
#         return
    
#     final_response = get_parameters_values(device, auth_token, api_config, session)
#     if final_response is None:
#         return
    
#     document.write(f"Device: {device}\n")
#     document.write(f"Initial Response: {json.dumps(inititial_response, indent=4)}\n")
#     document.write(f"Final Response: {json.dumps(inititial_response, indent=4)}\n")

#     print(f"Device: {device}\n")
#     print(f"Initial Response: {json.dumps(inititial_response, indent=4)}\n")
#     print(f"Final Response: {json.dumps(inititial_response, indent=4)}\n")

# config = load_config()
# auth_token = authenticate(config)

# if auth_token:
#     devices = generate_device_ids(config)
#     with open("parameter_change.txt", "w") as document:
#         with requests.Session() as session:
#             for device in devices:
#                 process_device(device, auth_token, config, document, session)
#     console.print("[green]All operations completed")
# else:
#     console.print("[red]Authentication failed[/red]")

