import pytest
import system_monitor
import time

from unittest.mock import MagicMock
from types import SimpleNamespace
from system_monitor import SystemMonitor, MonitorConfigurationError
from system_metrics import SystemMetrics
from disk_info import DiskInfo


@pytest.fixture
def valid_environment(monkeypatch):
    monkeypatch.setattr(system_monitor.psutil, "sensors_temperatures", lambda: {"cpu_thermal": [SimpleNamespace(current=50.0)]})
    monkeypatch.setattr(system_monitor.psutil, "disk_usage", lambda path: SimpleNamespace(percent=40.0))
    monkeypatch.setattr(system_monitor.psutil, "net_if_stats", lambda: {"eth0": SimpleNamespace(isup=True)})


@pytest.fixture
def valid_system_monitor(valid_environment):
    return SystemMonitor("cpu_thermal", "/", "eth0")


def test_valid_configuration(valid_system_monitor):
    assert isinstance(valid_system_monitor, SystemMonitor)


def test_invalid_temperature_sensor(valid_environment):
    with pytest.raises(MonitorConfigurationError) as error:
        SystemMonitor("thermal", "/", "eth0")

    assert "Temperature sensor 'thermal' does not exist." in str(error.value)


def test_invalid_disk_path(valid_environment, monkeypatch):
    def fake_disk_usage(path):
        if path == "/home/nonexisting":
            raise FileNotFoundError

        return SimpleNamespace(percent=40.0)

    monkeypatch.setattr(
        system_monitor.psutil,
        "disk_usage",
        fake_disk_usage,
    )

    with pytest.raises(MonitorConfigurationError) as error:
        SystemMonitor("cpu_thermal", "/home/nonexisting", "eth0")

    assert "Disk path '/home/nonexisting' does not exist." in str(error.value)


def test_invalid_network_interface(valid_environment):
    with pytest.raises(MonitorConfigurationError) as error:
        SystemMonitor("cpu_thermal", "/", "eth1")

    assert "Network interface 'eth1' does not exist." in str(error.value)


def test_read_cpu_temperature(valid_system_monitor):
    assert valid_system_monitor.read_cpu_temperature() == 50


def test_read_disk_usage(valid_system_monitor):
    assert valid_system_monitor.read_disk_usage() == 40


def test_read_network_status(valid_system_monitor):
    assert valid_system_monitor.read_network_status() == True


def test_read_cpu_usage(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(system_monitor.psutil, "cpu_percent", lambda interval: 13)

    assert valid_system_monitor.read_cpu_usage() == 13


def test_read_ram_usage(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(system_monitor.psutil, "virtual_memory", lambda: SimpleNamespace(percent=11))

    assert valid_system_monitor.read_ram_usage() == 11


def test_read_uptime_minutes(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(system_monitor.time, "time", lambda: 6400)

    monkeypatch.setattr(system_monitor.psutil, "boot_time", lambda: 1000)
    assert valid_system_monitor.read_uptime_minutes() == 90

def test_collect_timestamp(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(time, "time", MagicMock(return_value=1))

    assert valid_system_monitor.collect_timestamp() == 1


def test_collect_metrics(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(valid_system_monitor, "read_cpu_usage", lambda: 10)
    monkeypatch.setattr(valid_system_monitor, "read_ram_usage", lambda: 20)
    monkeypatch.setattr(valid_system_monitor, "read_cpu_temperature", lambda: 50)
    monkeypatch.setattr(valid_system_monitor, "read_disk_usage", lambda: 40)
    monkeypatch.setattr(valid_system_monitor, "read_uptime_minutes", lambda: 90)
    monkeypatch.setattr(valid_system_monitor, "read_network_status", lambda: True)
    monkeypatch.setattr(valid_system_monitor, "collect_timestamp", lambda: 1)

    result = valid_system_monitor.collect_metrics()

    expected = SystemMetrics(
        cpu_usage=10,
        ram_usage=20,
        cpu_temperature=50,
        disk_usage=40,
        uptime_minutes=90,
        network_status=True,
        timestamp=1,
    )

    assert result == expected


def test_read_disks(valid_system_monitor, monkeypatch):
    fake_output = """\
NAME="loop0" PKNAME="" TYPE="loop" SIZE="2G" MODEL="" TRAN="" MOUNTPOINTS=""
NAME="sda" PKNAME="" TYPE="disk" SIZE="298.1G" MODEL="WDC WD3200BMVW-11AMCS4" TRAN="usb" MOUNTPOINTS=""
NAME="sda1" PKNAME="sda" TYPE="part" SIZE="298.1G" MODEL="" TRAN="" MOUNTPOINTS=""
NAME="mmcblk0" PKNAME="" TYPE="disk" SIZE="29.7G" MODEL="" TRAN="mmc" MOUNTPOINTS=""
NAME="mmcblk0p1" PKNAME="mmcblk0" TYPE="part" SIZE="512M" MODEL="" TRAN="mmc" MOUNTPOINTS="/boot/firmware"
NAME="mmcblk0p2" PKNAME="mmcblk0" TYPE="part" SIZE="29.2G" MODEL="" TRAN="mmc" MOUNTPOINTS="/"
NAME="zram0" PKNAME="" TYPE="disk" SIZE="2G" MODEL="" TRAN="" MOUNTPOINTS="[SWAP]"
"""

    def fake_disk_usage(path):
        if path == "/boot/firmware":
            return SimpleNamespace(percent=20)

        if path == "/":
            return SimpleNamespace(percent=55)

    def fake_subprocess_run(args, **kwargs):
        if args[0] == "lsblk":
            return SimpleNamespace(
                stdout=fake_output,
                stderr="",
                returncode=0
            )

        if args[0] == "fdisk":
            return SimpleNamespace(
                stdout="",
                stderr="",
                returncode=0
            )
        
    monkeypatch.setattr(system_monitor.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(system_monitor.psutil, "disk_usage", fake_disk_usage)

    result = valid_system_monitor.read_disks()

    assert result == [
        DiskInfo(
            name="sda",
            size="298.1G",
            model="WDC WD3200BMVW-11AMCS4",
            transport="usb",
            mountpoints=[],
            usage_percent=None,
            error=None
        ),
        DiskInfo(
            name="mmcblk0",
            size="29.7G",
            model="",
            transport="mmc",
            mountpoints=["/boot/firmware", "/"],
            usage_percent=55,
            error=None
        )
    ]


def test_read_disks_handles_disk_without_mountpoint(valid_system_monitor, monkeypatch):
    fake_output = """\
NAME="loop0" PKNAME="" TYPE="loop" SIZE="2G" MODEL="" TRAN="" MOUNTPOINTS=""
NAME="mmcblk0" PKNAME="" TYPE="disk" SIZE="29.7G" MODEL="" TRAN="mmc" MOUNTPOINTS=""
NAME="zram0" PKNAME="" TYPE="disk" SIZE="2G" MODEL="" TRAN="" MOUNTPOINTS="[SWAP]"
"""

    def fake_subprocess_run(args, **kwargs):
        if args[0] == "lsblk":
            return SimpleNamespace(
                stdout=fake_output,
                stderr="",
                returncode=0
            )

        if args[0] == "fdisk":
            return SimpleNamespace(
                stdout="",
                stderr="",
                returncode=0
            )

    monkeypatch.setattr(system_monitor.subprocess, "run", fake_subprocess_run)

    result = valid_system_monitor.read_disks()

    assert result == [
        DiskInfo(
            name="mmcblk0",
            size="29.7G",
            model="",
            transport="mmc",
            mountpoints=[],
            usage_percent=None,
            error=None
        )
    ]


def test_get_disk_error_returns_none_when_fdisk_succeeds(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(system_monitor.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=""))

    assert valid_system_monitor.get_disk_error("sda") is None


def test_get_disk_error_returns_error_when_fdisk_fails(valid_system_monitor, monkeypatch):
    monkeypatch.setattr(system_monitor.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="Input/output error"))
    
    assert valid_system_monitor.get_disk_error("sda") == "Input/output error"
