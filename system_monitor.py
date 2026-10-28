import psutil
import time
import subprocess
import re

from disk_info import DiskInfo
from system_metrics import SystemMetrics


class MonitorConfigurationError(Exception):
    pass


class SystemMonitor:
    def __init__(self, temperature_sensor, disk_path, network_interface):
        self.temperature_sensor = temperature_sensor
        self.disk_path = disk_path
        self.network_interface = network_interface

        self._validate_configuration()

    def read_cpu_usage(self) -> float:
        return psutil.cpu_percent(interval=1)

    def read_ram_usage(self) -> float:
        return psutil.virtual_memory().percent

    def read_cpu_temperature(self) -> float:
        return psutil.sensors_temperatures()[self.temperature_sensor][0].current

    def read_disk_usage(self) -> float:
        return psutil.disk_usage(self.disk_path).percent

    def read_uptime_minutes(self) -> int:
        uptime_seconds = time.time() - psutil.boot_time()
        return int(uptime_seconds // 60)

    def read_network_status(self) -> bool:
        return psutil.net_if_stats()[self.network_interface].isup

    def collect_timestamp(self) -> int:
        return int(time.time())

    def collect_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            cpu_usage=self.read_cpu_usage(),
            ram_usage=self.read_ram_usage(),
            cpu_temperature=self.read_cpu_temperature(),
            disk_usage=self.read_disk_usage(),
            uptime_minutes=self.read_uptime_minutes(),
            network_status=self.read_network_status(),
            timestamp=self.collect_timestamp(),
        )

    def read_disks(self) -> list[DiskInfo]:
        result = subprocess.run(
            ["lsblk", "-Pn", "-o", "NAME,PKNAME,TYPE,SIZE,MODEL,TRAN,MOUNTPOINTS"],
            capture_output=True,
            text=True,
            check=True
        )

        devices = [] 
        disks = []

        for line in result.stdout.splitlines():
            devices.append({
                "name": re.search(r'NAME="([^"]*)"', line).group(1),
                "pkname": re.search(r'PKNAME="([^"]*)"', line).group(1),
                "type": re.search(r'TYPE="([^"]*)"', line).group(1),
                "size": re.search(r'SIZE="([^"]*)"', line).group(1),
                "model": re.search(r'MODEL="([^"]*)"', line).group(1),
                "transport": re.search(r'TRAN="([^"]*)"', line).group(1),
                "mountpoint": re.search(r'MOUNTPOINTS="([^"]*)"', line).group(1),
            })

        for device in devices:
            if device["type"] == "disk" and device["transport"]:
                mountpoints = []

                for partition in devices:
                    if (
                        partition["type"] == "part"
                        and partition["pkname"] == device["name"]
                        and partition["mountpoint"]
                    ):
                        mountpoints.append(partition["mountpoint"])
                if mountpoints:
                    usage_percent = max(
                        psutil.disk_usage(mountpoint).percent
                        for mountpoint in mountpoints
                    )
                else:
                    usage_percent = None

                error = self.get_disk_error(device["name"])

                disks.append(
                        DiskInfo(
                            name=device["name"],
                            size=device["size"],
                            model=device["model"],
                            transport=device["transport"],
                            mountpoints=mountpoints,
                            usage_percent=usage_percent,
                            error=error
                        )
                )

        return disks

    def get_disk_error(self, disk_name: str) -> str | None:
        result = subprocess.run(
            ["fdisk", "-l", f"/dev/{disk_name}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return result.stderr.strip()
        
        return None

    def _validate_configuration(self):
        errors = []

        try:
            psutil.sensors_temperatures()[self.temperature_sensor][0]
        except (KeyError, IndexError):
            errors.append(
                f"Temperature sensor '{self.temperature_sensor}' does not exist."
            )

        try:
            psutil.disk_usage(self.disk_path)
        except FileNotFoundError:
            errors.append(f"Disk path '{self.disk_path}' does not exist.")

        if self.network_interface not in psutil.net_if_stats():
            errors.append(
                f"Network interface '{self.network_interface}' does not exist."
            )

        if errors:
            raise MonitorConfigurationError("\n".join(errors))
