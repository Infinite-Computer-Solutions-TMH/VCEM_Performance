import re
import time
import threading
from collections import defaultdict
from datetime import datetime, timedelta
import pytz  
import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

# -------------------
# InfluxDB Config
# -------------------
INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "jetty_count"
INFLUXDB_ORG = "vz"
INFLUXDB_TOKEN = "KkMttEuiINrRL-XVUwfX8CsvrG8nB0CP4M6dT8IHQ4vGjClJAlsO5xYwwlsJgBOXKc__CMEaU4u1MMrJQztaAQ=="

client = influxdb_client.InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

# -------------------
# Globals
# -------------------
LOG_FILE = "/var/lib/docker/volumes/vcem_vcem-jetty_logs/_data/jetty-request.log"
KEYWORDS = ["api", "cwmp"]
FLUSH_INTERVAL_SECONDS = 600  # 10 minutes

# Format: { 'YYYY-MM-DD HH:MM:SS': {'api': X, 'cwmp': Y} }
per_second_counts = defaultdict(lambda: {k: 0 for k in KEYWORDS})
timestamp_pattern = re.compile(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})')

# Set your desired timezone
LOCAL_TZ = pytz.timezone("US/Eastern")  # Change if needed

# ---------------- Helper Functions ----------------
def parse_timestamp(line):
    match = timestamp_pattern.search(line)
    if match:
        dt = datetime.strptime(match.group(1), "%d/%b/%Y:%H:%M:%S")
        dt = dt.replace(tzinfo=pytz.utc).astimezone(LOCAL_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None

def monitor_log():
    with open(LOG_FILE, 'r') as f:
        f.seek(0, 2)  # Move to the end of file

        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue

            ts = parse_timestamp(line)
            if not ts:
                continue

            lower_line = line.lower()
            for kw in KEYWORDS:
                if kw in lower_line:
                    per_second_counts[ts][kw] += 1

def flush_to_influx():
    while True:
        time.sleep(FLUSH_INTERVAL_SECONDS)
        flush_data()

def flush_data():
    print(f"[FLUSH] Sending data to InfluxDB at {datetime.now(LOCAL_TZ)}")
    batch = []

    if not per_second_counts:
        print("[FLUSH] No data to write.")
        return

    timestamps = sorted(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in per_second_counts.keys())
    start_time = timestamps[0]
    end_time = timestamps[-1]

    # Fill missing seconds
    current_time = start_time
    while current_time <= end_time:
        ts_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        if ts_str not in per_second_counts:
            per_second_counts[ts_str] = {kw: 0 for kw in KEYWORDS}
        current_time += timedelta(seconds=1)

    for ts_str, keyword_counts in sorted(per_second_counts.items()):
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        dt = LOCAL_TZ.localize(dt)
        for keyword, count in keyword_counts.items():
            point = Point(f"{keyword}_per_second") \
                .field("count", count) \
                .time(dt)
            batch.append(point)

    if batch:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=batch)
        print(f"[FLUSH] Wrote {len(batch)} points to InfluxDB.")
        per_second_counts.clear()
    else:
        print("[FLUSH] No data to write.")

# ---------------- Start Threads ----------------
t1 = threading.Thread(target=monitor_log, daemon=True)
t2 = threading.Thread(target=flush_to_influx, daemon=True)

t1.start()
t2.start()

# Keep the main thread alive
while True:
    time.sleep(60)









































































# import re
# import time
# import threading
# from collections import defaultdict
# from datetime import datetime, timedelta
# import influxdb_client
# from influxdb_client import Point
# from influxdb_client.client.write_api import SYNCHRONOUS

# # -------------------
# # InfluxDB Config
# # -------------------
# INFLUXDB_URL = "101.101.63.15:8086"
# INFLUXDB_BUCKET = "jetty_count"
# INFLUXDB_ORG = "vz"
# INFLUXDB_TOKEN = "KkMttEuiINrRL-XVUwfX8CsvrG8nB0CP4M6dT8IHQ4vGjClJAlsO5xYwwlsJgBOXKc__CMEaU4u1MMrJQztaAQ=="

# client = influxdb_client.InfluxDBClient(
#     url=INFLUXDB_URL,
#     token=INFLUXDB_TOKEN,
#     org=INFLUXDB_ORG
# )
# write_api = client.write_api(write_options=SYNCHRONOUS)

# # -------------------
# # Globals
# # -------------------
# LOG_FILE = "/var/lib/docker/volumes/vcem_vcem-jetty_logs/_data/jetty-request.log"
# KEYWORDS = ["api", "cwmp"]
# FLUSH_INTERVAL_SECONDS = 600  # 10 minutes

# # Format: { 'YYYY-MM-DD HH:MM:SS': {'api': X, 'cwmp': Y} }
# per_second_counts = defaultdict(lambda: {k: 0 for k in KEYWORDS})
# timestamp_pattern = re.compile(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})')


# # -------------------
# # Helper Functions
# # -------------------
# def parse_timestamp(line):
#     match = timestamp_pattern.search(line)
#     if match:
#         dt = datetime.strptime(match.group(1), "%d/%b/%Y:%H:%M:%S")
#         return dt.strftime("%Y-%m-%d %H:%M:%S")
#     return None

# def monitor_log():
#     with open(LOG_FILE, 'r') as f:
#         f.seek(0, 2)  # move to the end of file

#         while True:
#             line = f.readline()
#             if not line:
#                 time.sleep(0.1)
#                 continue

#             ts = parse_timestamp(line)
#             if not ts:
#                 continue

#             lower_line = line.lower()
#             for kw in KEYWORDS:
#                 if kw in lower_line:
#                     per_second_counts[ts][kw] += 1

# def flush_to_influx():
#     while True:
#         time.sleep(FLUSH_INTERVAL_SECONDS)
#         flush_data()

# def flush_data():
#     print(f"[FLUSH] Sending data to InfluxDB at {datetime.utcnow()}")
#     batch = []

#     if not per_second_counts:
#         print("[FLUSH] No data to write.")
#         return

#     # Find earliest and latest timestamps we have
#     timestamps = sorted(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in per_second_counts.keys())
#     start_time = timestamps[0]
#     end_time = timestamps[-1]

#     # Fill missing seconds
#     current_time = start_time
#     while current_time <= end_time:
#         ts_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
#         if ts_str not in per_second_counts:
#             per_second_counts[ts_str] = {kw: 0 for kw in KEYWORDS}
#         current_time += timedelta(seconds=1)

#     # Build batch to send
#     for ts_str, keyword_counts in sorted(per_second_counts.items()):
#         dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
#         for keyword, count in keyword_counts.items():
#             point = Point(f"{keyword}_per_second") \
#                 .field("count", count) \
#                 .time(dt)
#             batch.append(point)

#     if batch:
#         write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=batch)
#         print(f"[FLUSH] Wrote {len(batch)} points to InfluxDB.")
#         per_second_counts.clear()
#     else:
#         print("[FLUSH] No data to write.")

# # -------------------
# # Start Monitoring and Flushing Threads
# # -------------------
# t1 = threading.Thread(target=monitor_log, daemon=True)
# t2 = threading.Thread(target=flush_to_influx, daemon=True)

# t1.start()
# t2.start()

# # Keep the main thread alive forever
# while True:
#     time.sleep(60)


















































































# import re
# import time
# import threading
# from collections import defaultdict
# from datetime import datetime
# import influxdb_client
# from influxdb_client import Point
# from influxdb_client.client.write_api import SYNCHRONOUS

# # -------------------
# # InfluxDB Config
# # -------------------
# INFLUXDB_URL = "101.101.63.15:8086"
# INFLUXDB_BUCKET = "jetty"
# INFLUXDB_ORG = "vz"
# INFLUXDB_TOKEN = "ibn12p-5yM8JKFw2-kBRXuwxlq3bh0bID0S8lWwHJ4pu4whWpc6VH34SlS81qR60o3B5h7ySKquXSEWe0Uj2BA=="

# client = influxdb_client.InfluxDBClient(
#     url=INFLUXDB_URL,
#     token=INFLUXDB_TOKEN,
#     org=INFLUXDB_ORG
# )
# write_api = client.write_api(write_options=SYNCHRONOUS)

# # -------------------
# # Globals
# # -------------------
# LOG_FILE = "/var/lib/docker/volumes/vcem_vcem-jetty_logs/_data/jetty-request.log"
# KEYWORDS = ["api", "cwmp"]
# FLUSH_INTERVAL_SECONDS = 600  # 10 minutes

# # Format: { 'YYYY-MM-DD HH:MM:SS': {'api': X, 'cwmp': Y} }
# per_second_counts = defaultdict(lambda: {k: 0 for k in KEYWORDS})
# timestamp_pattern = re.compile(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})')

# # -------------------
# # Helper Functions
# # -------------------
# def parse_timestamp(line):
#     match = timestamp_pattern.search(line)
#     if match:
#         dt = datetime.strptime(match.group(1), "%d/%b/%Y:%H:%M:%S")
#         return dt.strftime("%Y-%m-%d %H:%M:%S")
#     return None

# def monitor_log():
#     with open(LOG_FILE, 'r') as f:
#         f.seek(0, 2)  # move to the end of file

#         while True:
#             line = f.readline()
#             if not line:
#                 time.sleep(0.1)
#                 continue

#             ts = parse_timestamp(line)
#             if not ts:
#                 continue

#             lower_line = line.lower()
#             for kw in KEYWORDS:
#                 if kw in lower_line:
#                     per_second_counts[ts][kw] += 1

# def flush_to_influx():
#     while True:
#         time.sleep(FLUSH_INTERVAL_SECONDS)
#         flush_data()

# def flush_data():
#     print(f"[FLUSH] Sending data to InfluxDB at {datetime.utcnow()}")
#     batch = []

#     for ts_str, keyword_counts in per_second_counts.items():
#         dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
#         for keyword, count in keyword_counts.items():
#             point = Point(f"{keyword}_per_second") \
#                 .field("count", count) \
#                 .time(dt)
#             batch.append(point)

#     if batch:
#         write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=batch)
#         print(f"[FLUSH] Wrote {len(batch)} points.")
#         per_second_counts.clear()
#     else:
#         print("[FLUSH] No data to write.")

# # -------------------
# # Run Immediately
# # -------------------
# t1 = threading.Thread(target=monitor_log, daemon=True)
# t2 = threading.Thread(target=flush_to_influx, daemon=True)

# t1.start()
# t2.start()

# # Keep the main thread alive forever
# while True:
#     time.sleep(60)
























































































# import re
# import influxdb_client
# from influxdb_client import Point
# from influxdb_client.client.write_api import SYNCHRONOUS

# # InfluxDB config
# # InfluxDB config
# INFLUXDB_URL = "101.101.63.15:8086"
# INFLUXDB_BUCKET = "jetty"
# INFLUXDB_ORG = "vz"
# INFLUXDB_TOKEN = "ibn12p-5yM8JKFw2-kBRXuwxlq3bh0bID0S8lWwHJ4pu4whWpc6VH34SlS81qR60o3B5h7ySKquXSEWe0Uj2BA=="

# # Match log lines between two timestamps and containing specific patterns
# def count_filtered_lines(log_file_path, start_time, end_time, url_path, ip, device_prefix):
#     count = 0
#     in_range = False

#     # Convert everything to lowercase for consistent matching
#     url_path = url_path.lower()
#     ip = ip.lower()
#     device_prefix = device_prefix.lower()

#     with open(log_file_path, 'r') as file:
#         for line in file:
#             line_lower = line.lower()

#             # Start collecting lines once start_time is found
#             if start_time in line:
#                 in_range = True

#             if in_range:
#                 if (url_path in line_lower and ip in line_lower and device_prefix in line_lower):
#                     count += 1

#                 # Stop when end_time is found
#                 if end_time in line:
#                     break

#     return count

# # Send count to InfluxDB
# def write_to_influx(measurement, field_key, field_value):
#     client = influxdb_client.InfluxDBClient(
#         url=INFLUXDB_URL,
#         token=INFLUXDB_TOKEN,
#         org=INFLUXDB_ORG
#     )
#     write_api = client.write_api(write_options=SYNCHRONOUS)

#     point = Point(measurement).field(field_key, field_value)
#     write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
#     print(f"[InfluxDB] Wrote {field_key}={field_value} to measurement '{measurement}' in bucket '{INFLUXDB_BUCKET}'.")

# # --- Main Logic ---
# log_path = "/var/lib/docker/volumes/vcem_vcem-jetty_logs/_data/jetty_2025-04-23.1.log"
# start_ts = "[23/Apr/2025:16:15:56"
# end_ts   = "[23/Apr/2025:19:42:40"
# url_filter = "/cwmpweb/cpemgt"
# source_ip = "101.101.63.13"
# device_filter = "bot0"

# cwmp_count = count_filtered_lines(log_path, start_ts, end_ts, url_filter, source_ip, device_filter)
# print(f'Total filtered "cwmp" lines: {cwmp_count}')
# write_to_influx("cwmp_count", "count", cwmp_count)











































































# def count_api_lines(log_file_path):
#     count = 0
#     with open(log_file_path, 'r') as file:
#         for line in file:
#             if "api" in line.lower():  # Case-insensitive match
#                 count += 1

#     print(f'Total lines containing "api" (case-insensitive): {count}')

# # --- Set the path to the log file ---
# log_path = "/var/lib/docker/volumes/vcem_vcem-jetty_logs/_data/jetty_2025-04-22.2.log"
# count_api_lines(log_path)