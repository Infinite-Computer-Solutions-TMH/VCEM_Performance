import requests
import yaml
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from rich.console import Console
from rich.table import Table
import influxdb_client
from influxdb_client import Point
import urllib3
from influxdb_client.client.write_api import SYNCHRONOUS, WritePrecision

# Disable SSL warnings 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup console for rich output
console = Console()

# InfluxDB Configuration
INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "APIcall"
INFLUXDB_ORG = "vz"
# INFLUXDB_TOKEN = "9sVTy3SbqK-K80yVQyG4Am2Kooz42FXsf9zSCY_nq4pkncvuyBSKiNibjtBEJQ1Mwy6ZCka6v31dGwHEuI3q1Q=="
# INFLUXDB_TOKEN = "fW9j0X-s2VbmOoMLfDur2TG45PB37EAV2HIb0QsuaFRzM2cdVs8T7FmqrIBuVzLxrvYSocHMzk8VgbFoCEu3dA=="
INFLUXDB_TOKEN = "WI0juhVVA9dQAEzoJbWlenQyi1hyerYYc3oZQHlVsw0MI1mIYL8WwbIvacUhxIscu93w0tJLS3Br0d6zm5_kEg=="

# Initialize InfluxDB Client
influx_client = influxdb_client.InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# -----------------------
# Record metrics to InfluxDB
# -----------------------
def record_metrics(measurement, fields, tags=None):
    point = Point(measurement)
    for key, value in fields.items():
        point.field(key, value)
    if tags:
        for key, value in tags.items():
            point.tag(key, value)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

# -----------------------
# Load YAML config
# -----------------------
def load_config(file_path="cfg.yaml"):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

# -----------------------
# Generate device IDs from base ranges
# -----------------------
def generate_device_ids(user_count, prefix="BOT"):
    base_ranges = [0, 25000, 50000]  # You can change this list as needed
    device_ids = []
    for base in base_ranges:
        start = base
        end = base + user_count
        device_ids.extend([f"{prefix}{num:06d}" for num in range(start, end + 1)])
    return device_ids

# -----------------------
# Authenticate and return token
# -----------------------
def authenticate(api_config):
    console.print("\nAuthenticating...")
    url = api_config["authenticate"]["url"]
    headers = api_config["authenticate"]["headers"]
    data = api_config["authenticate"]["payload"]
    response = requests.post(url, headers=headers, data=data, verify=False)
    if response.status_code == 200:
        token = response.json().get("access_token")
        if token:
            console.print("Authentication successful!")
            return token
    console.print(f"Authentication failed! Status: {response.status_code}")
    return None

# -----------------------
# Perform API request and track metrics
# -----------------------
def perform_api_request(url, headers, payload, device, action_type, metrics):
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload, verify=False)
    latency = time.time() - start_time
    first_byte_time = response.elapsed.total_seconds()
    response_time = latency

    table = Table(title=f"{action_type} - {device}")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Status Code", str(response.status_code))
    table.add_row("Latency (sec)", f"{latency:.4f}")
    table.add_row("First Byte Time (sec)", f"{first_byte_time:.4f}")
    table.add_row("Response Time (sec)", f"{response_time:.4f}")
    console.print(table)

    fields = {"status_code": response.status_code}
    if response.status_code == 200:
        metrics['latency'].append(latency)
        metrics['first_byte_time'].append(first_byte_time)
        metrics['response_time'].append(response_time)
        fields.update({
            "latency": latency,
            "first_byte_time": first_byte_time,
            "response_time": response_time
        })

    record_metrics(action_type.lower(), fields, tags={"device_id": device})
    return response.status_code

# -----------------------
# GPV API call
# -----------------------
def get_parameters_values(device, auth_token, api_config, metrics, api_call_counter):
    url = api_config["gpv"]["url"].format(device_id=device)
    headers = {**api_config["gpv"]["headers"], "Authorization": f"Bearer {auth_token}"}
    payload = api_config["gpv"]["payload"]
    status = perform_api_request(url, headers, payload, device, "GPV", metrics)
    api_call_counter += 1

    if api_call_counter >= 100:
        console.print("[yellow]Re-authenticating after 100 API calls...[/yellow]")
        auth_token = authenticate(api_config)
        if not auth_token:
            return None, 0, status
        api_call_counter = 0

    return auth_token, api_call_counter, status

# -----------------------
# SPV API call
# -----------------------
def set_parameters_values(device, auth_token, api_config, metrics, api_call_counter):
    url = api_config["spv"]["url"].format(device_id=device)
    headers = {**api_config["spv"]["headers"], "Authorization": f"Bearer {auth_token}"}
    payload = api_config["spv"]["payload"]
    status = perform_api_request(url, headers, payload, device, "SPV", metrics)
    api_call_counter += 1

    if api_call_counter >= 100:
        console.print("[yellow]Re-authenticating after 100 API calls...[/yellow]")
        auth_token = authenticate(api_config)
        if not auth_token:
            return None, 0, status
        api_call_counter = 0

    return auth_token, api_call_counter, status

# -----------------------
# Average calculation
# -----------------------
def calculate_averages(metrics):
    avg_response_time = sum(metrics['response_time']) / len(metrics['response_time']) if metrics['response_time'] else 0
    avg_latency = sum(metrics['latency']) / len(metrics['latency']) if metrics['latency'] else 0
    avg_first_byte_time = sum(metrics['first_byte_time']) / len(metrics['first_byte_time']) if metrics['first_byte_time'] else 0

    console.print(f"\n[bold green]Average Response Time (sec): {avg_response_time:.4f}[/bold green]")
    console.print(f"[bold green]Average Latency (sec): {avg_latency:.4f}[/bold green]")
    console.print(f"[bold green]Average First Byte Time (sec): {avg_first_byte_time:.4f}[/bold green]")

# -----------------------
# Main API logic
# -----------------------
def execute_api_operations(api_config, auth_token, device_count):
    start_time = time.time()

    devices = generate_device_ids(device_count)
    api_config["devices"] = [{"device_id": d} for d in devices]

    metrics = {'latency': [], 'first_byte_time': [], 'response_time': []}
    api_call_counter = 0
    device_counter = 0
    device_error_counter = 0
    total_api_calls = 0
    error_api_calls = 0

    with ThreadPoolExecutor() as executor:
        def process_device(device):
            nonlocal auth_token, api_call_counter, device_counter
            nonlocal device_error_counter, total_api_calls, error_api_calls

            gpv_status = None
            spv_status = None

            if "gpv" in api_config:
                total_api_calls += 1
                auth_token, api_call_counter, gpv_status = get_parameters_values(device["device_id"], auth_token, api_config, metrics, api_call_counter)
                if not auth_token: return
                if gpv_status != 200:
                    error_api_calls += 1

            if "spv" in api_config:
                total_api_calls += 1
                auth_token, api_call_counter, spv_status = set_parameters_values(device["device_id"], auth_token, api_config, metrics, api_call_counter)
                if not auth_token: return
                if spv_status != 200:
                    error_api_calls += 1

            device_counter += 1
            if (gpv_status and gpv_status != 200) or (spv_status and spv_status != 200):
                device_error_counter += 1

        executor.map(process_device, api_config["devices"])

    total_time = time.time() - start_time
    calculate_averages(metrics)

    console.print(f"[bold cyan]Total Devices Processed: {device_counter}[/bold cyan]")
    console.print(f"[bold red]Total Devices with Errors: {device_error_counter}[/bold red]")
    console.print(f"[bold magenta]Total API Calls Made: {total_api_calls}[/bold magenta]")
    console.print(f"[bold red]Total API Call Errors: {error_api_calls}[/bold red]")
    console.print(f"[bold yellow]Total Time Taken: {total_time:.2f} seconds[/bold yellow]")

    record_metrics("device_count", {
        "total_devices": device_counter,
        "errors": device_error_counter,
        "api_calls": total_api_calls,
        "api_call_errors": error_api_calls
    })

# -----------------------
# Entry point
# -----------------------
user_input = input("Enter device range : ")
if not user_input.isdigit():
    console.print("[red]Invalid input. Please enter a number.[/red]")
    exit()

device_count = int(user_input)
config = load_config()
auth_token = authenticate(config)

if auth_token:
    execute_api_operations(config, auth_token, device_count)
else:
    console.print("Authentication failed. Exiting...")

