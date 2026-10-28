from dataclasses import dataclass


@dataclass
class SystemMetrics:
    cpu_usage: float
    ram_usage: float
    cpu_temperature: float
    disk_usage: float
    uptime_minutes: int
    network_status: bool
    timestamp: int
    