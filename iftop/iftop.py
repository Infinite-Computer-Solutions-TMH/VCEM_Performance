import subprocess
import re
import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Config
INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "iftop"
INFLUXDB_ORG = "vz"
INFLUXDB_TOKEN = "M9uY-cVXo6qDs_kYlMlg4o4m7i18-xmfcGUCKwj-XEbhdnJ7dggplVN76AkO7yeFUrD5tYNTUqmOiFVAypjw9g=="
TARGET_IPS = {"101.101.63.15", "101.101.63.13", "101.101.63.18"}

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def parse_iftop_output(output):
    traffic = {ip: {'sent': 0.0, 'recv': 0.0} for ip in TARGET_IPS}
    lines = output.splitlines()
    current_ip = None
    for i, line in enumerate(lines):
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
        if ip_match:
            ip = ip_match.group(1)
            if ip in TARGET_IPS:
                current_ip = ip
                # Look for => line (sent)
                if "=>" in line:
                    sent_match = re.findall(r'(\d+\.\d+)\s*(B|KB|MB|GB)', line)
                    if sent_match:
                        val, unit = sent_match[0]
                        traffic[ip]['sent'] += convert_to_bytes(float(val), unit)
                # Look for <= line (recv)
                elif "<=" in line:
                    recv_match = re.findall(r'(\d+\.\d+)\s*(B|KB|MB|GB)', line)
                    if recv_match:
                        val, unit = recv_match[0]
                        traffic[ip]['recv'] += convert_to_bytes(float(val), unit)
    return traffic

def convert_to_bytes(value, unit):
    unit = unit.upper()
    if unit == "KB":
        return value * 1024
    elif unit == "MB":
        return value * 1024 * 1024
    elif unit == "GB":
        return value * 1024 * 1024 * 1024
    return value  # B

def run_iftop_cycle():
    cmd = ["sudo", "iftop", "-n", "-t", "-s", "10", "-i", "ens33"]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        return output
    except subprocess.CalledProcessError as e:
        print("Error running iftop:", e.output.decode())
        return ""

def send_to_influx(traffic_data):
    for ip, stats in traffic_data.items():
        point = Point("vm_network_traffic") \
            .tag("ip", ip) \
            .field("sent_bytes", stats["sent"]) \
            .field("recv_bytes", stats["recv"]) \
            .time(datetime.utcnow())
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print(f"[{datetime.utcnow()}] {ip} - Sent: {stats['sent']:.2f} B, Recv: {stats['recv']:.2f} B")

# Main loop
while True:
    print("[INFO] Running iftop...")
    raw_output = run_iftop_cycle()
    if raw_output:
        traffic = parse_iftop_output(raw_output)
        send_to_influx(traffic)
    else:
        print("[WARN] No output from iftop.")
    time.sleep(1)










# INFLUXDB_URL = "101.101.63.15:8086"
# INFLUXDB_BUCKET = "iftop"
# INFLUXDB_ORG = "vz"
# INFLUXDB_TOKEN = "M9uY-cVXo6qDs_kYlMlg4o4m7i18-xmfcGUCKwj-XEbhdnJ7dggplVN76AkO7yeFUrD5tYNTUqmOiFVAypjw9g=="

# TARGET_IPS = {"101.101.63.15", "101.101.63.14", "101.101.63.18"}
# TARGET_IPS = {"63.69.79.175", "63.69.79.175", "101.101.64.20"}