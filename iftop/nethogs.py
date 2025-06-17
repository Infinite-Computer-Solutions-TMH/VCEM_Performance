import subprocess
import re
import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB Configuration
INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "iftop"
INFLUXDB_ORG = "vz"
INFLUXDB_TOKEN = "M9uY-cVXo6qDs_kYlMlg4o4m7i18-xmfcGUCKwj-XEbhdnJ7dggplVN76AkO7yeFUrD5tYNTUqmOiFVAypjw9g=="

# List of VM IPs to monitor
TARGET_IPS = {"101.101.63.15", "101.101.63.14", "101.101.63.18"}

# Initialize InfluxDB client
client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

def parse_nethogs_line(line):
    # Match pattern: srcIP:port-dstIP:port/X/X   send_kbps   recv_kbps
    match = re.match(r'(\d+\.\d+\.\d+\.\d+):\d+-([\d\.]+):\d+/\d+/\d+\s+([\d\.]+)\s+([\d\.]+)', line)
    if match:
        return match.groups()
    return None

def collect_traffic():
    cmd = ["sudo", "nethogs", "-t", "-d", "1", "-v", "3"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    traffic = {ip: {"sent": 0.0, "recv": 0.0} for ip in TARGET_IPS}

    try:
        while True:
            line = proc.stdout.readline().strip()
            if not line or ':' not in line or '-' not in line:
                continue

            parsed = parse_nethogs_line(line)
            if not parsed:
                continue

            src_ip, dst_ip, sent_kbps, recv_kbps = parsed
            sent_bytes = float(sent_kbps) * 1024
            recv_bytes = float(recv_kbps) * 1024

            if src_ip in TARGET_IPS:
                traffic[src_ip]["sent"] += sent_bytes
            if dst_ip in TARGET_IPS:
                traffic[dst_ip]["recv"] += recv_bytes

            # Flush every second
            if time.time() % 1 < 0.1:
                for ip in TARGET_IPS:
                    point = Point("vm_network_traffic") \
                        .tag("ip", ip) \
                        .field("sent_bytes", round(traffic[ip]["sent"], 2)) \
                        .field("recv_bytes", round(traffic[ip]["recv"], 2)) \
                        .time(datetime.utcnow())
                    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
                    print("[{}] {} => Sent: {:.2f} B, Recv: {:.2f} B".format(datetime.utcnow(), ip, traffic[ip]["sent"], traffic[ip]["recv"]))
                    traffic[ip] = {"sent": 0.0, "recv": 0.0}

                time.sleep(1)

    except Exception as e:
        print("Error running nethogs:", e)
        proc.kill()

    finally:
        proc.kill()

collect_traffic()





