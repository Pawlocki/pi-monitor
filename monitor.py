import time

from metrics_storage import MetricsStorage
from system_monitor import SystemMonitor
from health_checker import HealthChecker

def main():
    storage = MetricsStorage("metrics.db")

    monitor = SystemMonitor(
        temperature_sensor="cpu_thermal",
        disk_path="/",
        network_interface="eth0"
    )

    checker = HealthChecker(
        cpu_limit=80,
        ram_limit=80,
        temperature_limit=80,
        disk_limit=80
    )

    try:
        while True:
            metrics = monitor.collect_metrics()
            storage.save_metrics(metrics)

            print("Zapisano pomiar:", metrics)

            system_warnings = checker.check_system(metrics)

            for warning in system_warnings:
                print(warning)

            disks = monitor.read_disks()
            disk_warnings = checker.check_disks(disks)

            for warning in disk_warnings:
                print(warning)

            time.sleep(60)

    except KeyboardInterrupt:
        print("\nZatrzymano monitorowanie")

if __name__ == "__main__":
    main()