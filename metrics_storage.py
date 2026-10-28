import sqlite3
from system_metrics import SystemMetrics
from system_monitor import SystemMonitor

class MetricsStorage:
    def __init__(self, path, max_records=1000):
        if type(max_records) is not int or max_records<=0:
            raise ValueError("max_records must be a positive integer")
        self.path = path
        self.max_records = max_records
        self.initialize_db()

    def initialize_db(self):
        conn = sqlite3.connect(self.path)

        try:
            with conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics(
                    id INTEGER PRIMARY KEY,
                    timestamp INTEGER,
                    cpu_usage REAL,
                    ram_usage REAL,
                    cpu_temperature REAL,
                    disk_usage REAL,
                    uptime_minutes INTEGER,
                    network_status INTEGER
                )
                """)
        finally:
            conn.close()

    def save_metrics(self, metrics: SystemMetrics):
        conn = sqlite3.connect(self.path)

        try:
            with conn:
                conn.execute(
                    "INSERT INTO system_metrics (timestamp, cpu_usage, ram_usage, cpu_temperature, disk_usage, uptime_minutes, network_status) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (metrics.timestamp, metrics.cpu_usage, metrics.ram_usage, metrics.cpu_temperature, metrics.disk_usage, metrics.uptime_minutes, metrics.network_status)
                    )
                
                self._cleanup_old_metrics(conn)

        finally:
            conn.close()

    def get_latest_metrics(self, limit: int) -> list[tuple]:
        conn = sqlite3.connect(self.path)

        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM system_metrics ORDER BY id DESC LIMIT (?)", (limit,))
            latest_metrics = cur.fetchall()
        
        finally:
            conn.close()
        
        return latest_metrics

    def _cleanup_old_metrics(self, conn):
        conn.execute("""
        DELETE FROM system_metrics 
        WHERE id IN 
        (SELECT id FROM system_metrics 
        ORDER BY id DESC 
        LIMIT -1 OFFSET ? 
        )
        """, 
        (self.max_records,)
        )