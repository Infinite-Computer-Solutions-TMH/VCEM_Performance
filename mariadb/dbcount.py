import time
import threading
import pymysql
import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ---------------- InfluxDB Configuration ----------------
# InfluxDB Configuration
INFLUXDB_URL = "101.101.63.15:8086"
INFLUXDB_BUCKET = "db_count"
INFLUXDB_ORG = "vz"
INFLUXDB_TOKEN = "wVJT2rutXrFTI9nX4UKPru5AR76zq4T_TcqGVeWBHOjvi3GEWbU0SqkYhqDyjyz9Ti7JbiUVhhjUKt4ruHax_A=="

# Initialize InfluxDB Client
influx_client = influxdb_client.InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# ---------------- MariaDB Configuration ----------------
DB_HOST = "101.101.64.49."
DB_PORT = 3306
DB_USER = "0UXT32VAeF4p"
DB_PASSWORD = "8Q{`N{9X4hud"

# ---------------- Monitor Interval ----------------
POLL_INTERVAL = 1  # in seconds

def fetch_counts_and_push():
    while True:
        try:
            connection = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )

            with connection.cursor() as cursor:
                # --- Query Process List ---
                cursor.execute("SHOW PROCESSLIST")
                rows = cursor.fetchall()

                sleep_count = sum(1 for row in rows if row["Command"] == "Sleep")
                query_count = sum(1 for row in rows if row["Command"] == "Query")

                # --- Query InnoDB Transaction Table ----
                cursor.execute("SELECT * FROM information_schema.innodb_trx")
                trx_rows = cursor.fetchall()
                trx_count = len(trx_rows)

                # --- Write to InfluxDB ---
                now = time.time_ns()
                points = [
                    Point("mariadb_process_count")
                        .field("sleep", sleep_count)
                        .field("query", query_count)
                        .time(now),
                    Point("mariadb_transaction_count")
                        .field("trx", trx_count)
                        .time(now)
                ]

                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
                print(f" --> Sent data — Sleep: {sleep_count}, Query: {query_count}, Trx: {trx_count}")

        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            if connection:
                connection.close()
            time.sleep(POLL_INTERVAL)

# ---------------- Start Thread ----------------
monitor_thread = threading.Thread(target=fetch_counts_and_push, daemon=True)
monitor_thread.start()

# Keep the script running
while True:
    time.sleep(60)