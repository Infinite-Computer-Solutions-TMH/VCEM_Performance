import time
import requests
import yaml
import urllib3
from rich.console import Console
from rich.table import Table
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import concurrent.futures
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import threading


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#for rich output
console = Console()


INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "python"
INFLUXDB_ORG = "vz"
INFLUXDB_TOKEN = "fW9j0X-s2VbmOoMLfDur2TG45PB37EAV2HIb0QsuaFRzM2cdVs8T7FmqrIBuVzLxrvYSocHMzk8VgbFoCEu3dA=="


influx_client = influxdb_client.InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

request_counter = 0
counter_lock = threading.Lock()


def record_metrics(measurement, fields, tags=None):
    point = influxdb_client.Point(measurement)

    if tags:
        for key, value in tags.items():
            point.tag(key, value)

    for key, value in fields.items():
        point.field(key, value)

    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)    

def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)[0]
    

#function to authenticate and fetch the token
def authenticate(api_config):
    

    # console.print ("\n[bold cyan]Authenticating ...")

    url = api_config["authenticate"]["url"]
    payload = api_config['authenticate']['payload']
    headers = api_config['authenticate']['headers']
    
    start_time = time.time()
    response = requests.post(url, headers=headers, data=payload, verify=False)
    response_time = time.time() - start_time


    # table = Table(title="Bearer Token for authentication")
    # table.add_column("Field", style="bold cyan")
    # table.add_column("Value", style="bold green")
    # table.add_row("Bearer Token", str(response.json().get("access_token", "")))
    # table.add_row("Status Code", str(response.status_code))
    # table.add_row("Response Time (sec)", f"{response_time:.4f}")
    # console.print(table)
    
    if response.status_code == 200:
        token = response.json().get("access_token", "")
        record_metrics("api_authentication", {"response_time": response_time, "status": response.status_code})
        return token
    else:
        console.print(f"[red] Authentication failed with status code {response.status_code}")
        return None

    
def get_device_data(device):
    global request_counter, auth_token
    thread_id = threading.get_ident()

    with counter_lock:
        request_counter += 1

    #console.print(f"\n[bold yellow]Fetching data for {device['device_id']} ...[/bold yellow]")

    url = device["url"]
    headers = {**device["headers"], "Authorization": f"Bearer {auth_token}"}

    start_time = time.time()
    response = requests.get(url ,headers=headers, verify=False, timeout=5)
    latency = time.time() - start_time
    first_byte_time = response.elapsed.total_seconds()
    response_time = latency + first_byte_time


    table = Table(title=f"Device Details of - {device['device_id']}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Thread id", str(thread_id))
    table.add_row("Status Code", str(response.status_code))
    table.add_row("Latency (s)", f"{latency:.4f}")
    table.add_row("First Byte Time (s)", f"{first_byte_time:.4f}")
    table.add_row("Response time (sec)", f"{response_time:.4f}")
    table.add_row("Response", response.text[:200] +"..." if len(response.text) > 200 else response.text)
    console.print(table)


    record_metrics("device_api", {
        "latency": latency,
        "first_byte_time": first_byte_time,
        "status_code": response.status_code,
        "response_time": response_time
    },  tags={"device_id": device["device_id"]})


#function for parameter values    
def get_parameters_values(param_config):
    global request_counter, auth_token
    thread_id = threading.get_ident()

    with counter_lock:
        request_counter += 1

    #console.print(f"\n[bold Blue]Fetching parameters values for {param_config['device_id']} ...[/bold Blue]")

    url = param_config["url"]
    headers = {**param_config["headers"], "Authorization": f"Bearer {auth_token}"}
    payload = param_config["payload"]

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload, verify=False, timeout=5)
    latency = time.time() - start_time
    first_byte_time = response.elapsed.total_seconds()
    response_time = latency + first_byte_time

    # with request_counter_lock:
    #     total_request_counter += 1

    # request_counter += 1

    table = Table(title=f"parameter Values - {param_config['device_id']}")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style=" Bold green")
    table.add_row("Thread id", str(thread_id))
    table.add_row("Status Code", str(response.status_code))
    table.add_row("Latency (sec)", f"{latency:.4f}")
    table.add_row("First Byte Time (sec)", f"{first_byte_time:.4f}")
    table.add_row("Response time(sec)", f"{response_time:.4f}")
    table.add_row("Response", response.text[:200] + "..." if len(response.text) > 200 else response.text)
    console.print(table)

    record_metrics("get_parameters_values", {
        "latency": latency,
        "first_byte_time": first_byte_time,
        "response_time": response_time,
        "status_code": response.status_code
    }, tags={"device_id": param_config["device_id"]
    })

def execute_api_operations(api_config):
    with ThreadPoolExecutor() as executor:
        executor.map(get_device_data, api_config["device_data"])
        executor.map(get_parameters_values, api_config["get_parameters_values"])

api_config = load_config("con.yaml")

auth_token = authenticate(api_config)
if not auth_token:
    exit(1)

iteration_uptime_list = []
iteration_rps_list =[]

for i in range(10):
    if 1 > 0 and i % 500 == 0:
        auth_token = authenticate(api_config)
        if not auth_token:
            exit(1)

    request_counter = 0
    iteration_start_time = time.time()

    execute_api_operations(api_config)

    iteration_uptime = time.time() - iteration_start_time
    requests_per_second = request_counter / iteration_uptime if iteration_uptime > 0 else 0

    iteration_uptime_list.append(iteration_uptime)
    iteration_rps_list.append(requests_per_second)
    total_uptime= sum(iteration_uptime_list)

    console.print(f"[bold]  iterations {i+1}: Requests = {request_counter}, UpTime = {iteration_uptime:.2f}sec, RPS = {requests_per_second:.2f}[/bold]")

    record_metrics("api_uptime", {"uptime_seconds": iteration_uptime})
    record_metrics("api_requests_per_second", {"requests_per_second": requests_per_second})

    
    console.print(f"[bold] requests per second for iterations {i+1}: {requests_per_second:.2f}")


average_uptime = sum(iteration_uptime_list) / len(iteration_uptime_list) if iteration_uptime_list else 0
average_requests_per_second = sum(iteration_rps_list) / len(iteration_rps_list) if iteration_rps_list else 0

console.print(f"\n[bold] Average Uptime: {average_uptime:.2f}sec[/bold]")
console.print (f"[bold] total uptime: {total_uptime}sec")
console.print(f"[bold] Average Requests per Second: {average_requests_per_second:.2f} requests")






































# import requests
# import yaml
# import urllib3


# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# class APIExecutor:
#     def __init__(self, config_file):
#         self.config = self.load_config(config_file)
#         self.token = None
#         self.session = requests.Session()

#     def load_config(self, config_file):
#         with open(config_file, "r") as file:
#             return yaml.safe_load(file)


#     # def load_config(self, config_file):
#     #     try:
#     #         with open(config_file, 'r') as file:
#     #             return yaml.safe_load(file)
#     #     except FileNotFoundError:
#     #         raise FileNotFoundError(f"Config filec{config_file} not found")
#     #     except yaml.YAMLError as e:
#     #         raise ValueError(f"Error reading YAML file: {e}")
        
#     def execute_apis(self):
#         for api in self.config.get("apis", []):
#             # print("____test___")
#             if api.get("execute", False):
#                 # print("___print___")
#                 response = self.execute_api(api)
#                 print("-------------------------------------------------------------")
#                 print(f"API Name: {api['name']}")
#                 print("-------------------------------------------------------------")
#                 print(f"Response: {response}\n")
#                 print("-------------------------------------------------------------")

#     def execute_api(self, api):
#         method = api["method"].upper()
#         url = api["url"]
#         headers = api.get("headers", {})
#         payload = api.get("payload")
#         verify_ssl = api.get("verify_ssl", True)

#         if self.token:
#             headers = {k: v.format(token=self.token) for k, v in headers.items()}  


#         # if method == "POST" and headers.get("Content-Type") == "application/x-www-form-urlencoded":
#         #     payload = "'" + "&".join(f"{key}={value}" for key, value in payload.items()) + "'"
#         if isinstance(payload, str):
#             payload = f"'{payload}'"

#             # response = self.session.post(data=payload, headers=headers, verify=verify_ssl)
        


#         # if headers.get("Content-Type") == "application/json" and isinstance(payload, dict):
#         #    payload = f"'{payload}'"
        
#         # elif headers.get("Content-Type") == "application/x-www-form-urlencoded":
#         #     payload = "&".join(f"{k}={v}" for k,v in payload.items())
#         # print(f"{payload}")    

  

#         elif method == "POST":
#             response = self.session.post(url, json=payload, headers=headers, verify=verify_ssl)
#         elif method == "GET":
#             response = self.session.get(url, headers=headers, verify=verify_ssl)
#         else:
#             raise ValueError(f"unsupported http method: {method}")
        
#         if "access_token" in response.json():
#             self.token = response.json().get("access_token")


#         return response.json() if response.status_code == 200 else response.text
    

# # if __name__ == "__main__":
# #     executor = APIExecutor("config.yaml")
# #     executor.execute_apis()



