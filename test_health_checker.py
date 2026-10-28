import pytest
from health_checker import HealthChecker
from system_metrics import SystemMetrics
from disk_info import DiskInfo


@pytest.fixture
def valid_metrics():
    return SystemMetrics(
        cpu_usage=20,
        ram_usage=30,
        cpu_temperature=50,
        disk_usage=40,
        uptime_minutes=100, 
        network_status=True,
        timestamp=1000
    )

@pytest.fixture
def invalid_metrics():
    return SystemMetrics(
        cpu_usage=95,
        ram_usage=95,
        cpu_temperature=100,
        disk_usage=95,
        uptime_minutes=100, 
        network_status=False,
        timestamp=1000
    )


@pytest.fixture
def configured_health_checker():
    return HealthChecker(
        cpu_limit=90, 
        ram_limit=90, 
        temperature_limit=75, 
        disk_limit=85
    )


def test_valid_metrics(valid_metrics, configured_health_checker):
    assert configured_health_checker.check_system(valid_metrics) == []


def test_invalid_metrics(invalid_metrics, configured_health_checker):
    assert configured_health_checker.check_system(invalid_metrics) == [
        "Cpu usage: 95% is too high",
        "Ram usage: 95% is too high",
        "Cpu temperature: 100 is too high",
        "Disk usage: 95% is too high",
        "Network status is False."
    ]


def test_high_cpu(valid_metrics, configured_health_checker):
    valid_metrics.cpu_usage = 95
    assert configured_health_checker.check_system(valid_metrics) == ["Cpu usage: 95% is too high"]


def test_high_ram(valid_metrics, configured_health_checker):
    valid_metrics.ram_usage = 95
    assert configured_health_checker.check_system(valid_metrics) == ["Ram usage: 95% is too high"]


def test_high_temperature(valid_metrics, configured_health_checker):
    valid_metrics.cpu_temperature = 100
    assert configured_health_checker.check_system(valid_metrics) == ["Cpu temperature: 100 is too high"]


def test_high_system_disk_usage(valid_metrics, configured_health_checker):
    valid_metrics.disk_usage = 95
    assert configured_health_checker.check_system(valid_metrics) == ["Disk usage: 95% is too high"]


def test_network_down(valid_metrics, configured_health_checker):
    valid_metrics.network_status = False
    assert configured_health_checker.check_system(valid_metrics) == ["Network status is False."]


def test_system_disk_equal_to_limit(valid_metrics, configured_health_checker):
    valid_metrics.disk_usage = 85
    assert configured_health_checker.check_system(valid_metrics) == []


def test_disks_are_healthy(configured_health_checker):
    disks = [
        DiskInfo(
            name="sda",
            size="298.1G",
            model="WDC",
            transport="usb",
            mountpoints=["/media/usb"],
            usage_percent=40,
            error=None
        )
    ]

    assert configured_health_checker.check_disks(disks) == []


def test_disk_usage_is_too_high(configured_health_checker):
    disks = [
        DiskInfo(
            name="sda",
            size="298.1G",
            model="WDC",
            transport="usb",
            mountpoints=["/media/usb"],
            usage_percent=95,
            error=None
        )
    ]

    assert configured_health_checker.check_disks(disks) == ["Disk sda usage: 95% is too high"]


def test_disk_has_no_mountpoints(configured_health_checker):
    disks = [
        DiskInfo(
            name="sda",
            size="298.1G",
            model="WDC",
            transport="usb",
            mountpoints=[],
            usage_percent=None,
            error=None
        )
    ]

    assert configured_health_checker.check_disks(disks) == ["Disk sda is not mounted."]


def test_disk_has_error(configured_health_checker):
    disks = [
        DiskInfo(
            name="sda",
            size="298.1G",
            model="WDC",
            transport="usb",
            mountpoints=[],
            usage_percent=None,
            error="Input/output error"
        )
    ]

    assert configured_health_checker.check_disks(disks) == ["Disk sda error: Input/output error"]