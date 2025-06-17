import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from rich.console import Console

# Console for colored output
console = Console()

# InfluxDB Configuration
INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "device"
INFLUXDB_ORG = "vz"
INFLUXDB_TOKEN = "zWNMX5YCnNTu5UHol5wchEIm0aLdSd4HAOdvnh2KFLp5UtvU0Gpx0ZY0Z-sW3wrn2vUz0P7ev5Wh4dunbUj1eQ=="
# Initialize InfluxDB Client
client = influxdb_client.InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Write to InfluxDB
def record_total_devices(total_devices1):
    point = Point("total_devices1").field("count", total_devices1)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    console.print(f"[bold green] Recorded {total_devices1} devices in InfluxDB (bucket: 'device', measurement: 'total_devices')[/bold green]")

# Ask user for input
user_input = input("Enter number of devices per VM : ")

if not user_input.isdigit():
    console.print("[red]Invalid input. Please enter a numeric value.[/red]")
else:
    per_vm_devices = int(user_input)
    #----enter vm count-----
    vm_count = 2
    total_devices1   = per_vm_devices * vm_count
    console.print(f"[cyan] Total Devices Created Across {vm_count} VMs: {total_devices1}[/cyan]")
    record_total_devices(total_devices1)