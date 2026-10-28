from system_metrics import SystemMetrics
from disk_info import DiskInfo


class HealthChecker:
    def __init__(self, cpu_limit, ram_limit, temperature_limit, disk_limit):
        self.cpu_limit = cpu_limit
        self.ram_limit = ram_limit
        self.temperature_limit = temperature_limit
        self.disk_limit = disk_limit

    def check_system(self, system_metrics: SystemMetrics) -> list[str]:
        warnings = []
        if system_metrics.cpu_usage > self.cpu_limit:
            warnings.append(f"Cpu usage: {system_metrics.cpu_usage}% is too high")
        if system_metrics.ram_usage > self.ram_limit:
            warnings.append(f"Ram usage: {system_metrics.ram_usage}% is too high")    
        if system_metrics.cpu_temperature > self.temperature_limit:
            warnings.append(f"Cpu temperature: {system_metrics.cpu_temperature} is too high")
        if system_metrics.disk_usage > self.disk_limit:
            warnings.append(f"Disk usage: {system_metrics.disk_usage}% is too high")
        if system_metrics.network_status != True:
            warnings.append("Network status is False.")

        return warnings

    def check_disks(self, disks: list[DiskInfo]) -> list[str]:
        warnings = []
        for disk in disks:
            if disk.error is not None:
                warnings.append(f"Disk {disk.name} error: {disk.error}")
            elif not disk.mountpoints:
                warnings.append(f"Disk {disk.name} is not mounted.")
            if disk.usage_percent is not None and disk.usage_percent > self.disk_limit:
                warnings.append(f"Disk {disk.name} usage: {disk.usage_percent}% is too high")

        return warnings
