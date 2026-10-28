import pytest
from disk_tester import DiskTester
import tempfile
from unittest.mock import MagicMock
import subprocess
import json

@pytest.fixture
def valid_disk_tester(tmp_path):
    return DiskTester(str(tmp_path), "/dev/fake_disk")

@pytest.fixture
def valid_json():
    return {
        "smart_status": {
            "passed": True
        },
        "ata_smart_attributes": {
            "table": [
                {
                    "id": 5,
                    "raw": {
                        "value": 0
                    }
                },
                {
                    "id": 197,
                    "raw": {
                        "value": 0
                    }
                },
                {
                    "id": 198,
                    "raw": {
                        "value": 0
                    }
                }
            ]
        }
    }


def test_data_integrity_success(valid_disk_tester):
    assert valid_disk_tester.test_data_integrity() is True

def test_data_integrity_error(valid_disk_tester, monkeypatch):
    monkeypatch.setattr(tempfile, "NamedTemporaryFile", MagicMock(side_effect=OSError))

    assert valid_disk_tester.test_data_integrity() is False

def test_data_integrity_corrupted_data(valid_disk_tester, monkeypatch):
    original = tempfile.NamedTemporaryFile

    def fake_tempfile(*args, **kwargs):
        temp = original(*args, **kwargs)
        temp.read = MagicMock(return_value=b"")
        return temp
    
    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fake_tempfile)

    assert valid_disk_tester.test_data_integrity() is False

def test_measure_read_speed_success(valid_disk_tester):
    read_speed = valid_disk_tester.measure_read_speed()

    assert isinstance(read_speed, float)
    assert read_speed > 0

def test_measure_read_speed_error(valid_disk_tester, monkeypatch):
    original = tempfile.NamedTemporaryFile

    def fake_tempfile(*args, **kwargs):
        temp = original(*args, **kwargs)
        temp.write = MagicMock(side_effect=OSError)
        return temp

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fake_tempfile)

    assert valid_disk_tester.measure_read_speed() is None

def test_measure_write_speed_success(valid_disk_tester):
    write_speed = valid_disk_tester.measure_write_speed()

    assert isinstance(write_speed, float)
    assert write_speed > 0

def test_measure_write_speed_error(valid_disk_tester, monkeypatch):
    original = tempfile.NamedTemporaryFile

    def fake_run(*args, **kwargs):
        temp = original(*args, **kwargs)
        temp.write = MagicMock(side_effect=OSError)
        return temp

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fake_run)

    assert valid_disk_tester.measure_write_speed() is None

@pytest.mark.parametrize(
    "case",
    [
        {"value_198": 0, "passed": True, "returncode": 0, "expected": True},
        {"value_198": 3, "passed": True, "returncode": 0, "expected": False},
        {"value_198": 0, "passed": False, "returncode": 0, "expected": False},
        {"value_198": 0, "passed": True, "returncode": 1, "expected": None},
        {"value_198": 0, "passed": True, "returncode": 64, "expected": True},
        {"value_198": 3, "passed": True, "returncode": 64, "expected": False},
    ],
    ids=[
        "healthy_disk",
        "bad_sectors",
        "smart_failed",
        "smartctl_error",
        "smart_warning_healthy",
        "smart_warning_bad_sectors"
    ]
)
def test_check_smart(valid_disk_tester, valid_json, monkeypatch, case):
    def fake_run(*args, **kwargs):
        json_file = valid_json

        for attribute in json_file["ata_smart_attributes"]["table"]: 
            if attribute["id"] == 198:
                attribute["raw"]["value"] = case["value_198"]

        json_file["smart_status"]["passed"] = case["passed"]

        result = subprocess.CompletedProcess(
            args=args[0],
            returncode=case["returncode"],
            stdout=json.dumps(json_file)
        )

        return result

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is case["expected"]

def test_check_smart_invalid_json(valid_disk_tester, monkeypatch):
    def fake_run(*args, **kwargs):
        json_file = '{"smart_status": invalid}'

        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json_file
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is None

def test_check_smart_os_error(valid_disk_tester, monkeypatch):
    monkeypatch.setattr(subprocess, "run", MagicMock(side_effect=OSError))

    assert valid_disk_tester.check_smart() is None

def test_check_smart_missing_attribute(valid_disk_tester, valid_json, monkeypatch):
    def fake_run(*args, **kwargs):
        json_file = valid_json
        table = json_file["ata_smart_attributes"]["table"]

        for attribute in table:
            if attribute["id"] == 198:
                table.remove(attribute)
                break

        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(json_file)
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is None

def test_check_smart_invalid_value(valid_disk_tester, valid_json, monkeypatch):
    def fake_run(*args, **kwargs):
        json_file = valid_json

        for attribute in json_file["ata_smart_attributes"]["table"]:
            if attribute["id"] == 5:
                attribute["raw"]["value"] = "unknown" 

        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(json_file)
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is None

def test_check_smart_negative_value(valid_disk_tester, valid_json, monkeypatch):
    def fake_run(*args, **kwargs):
        json_file = valid_json

        for attribute in json_file["ata_smart_attributes"]["table"]:
            if attribute["id"] == 5:
                attribute["raw"]["value"] = -1

        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(json_file)
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is None

def test_check_smart_missing_status(valid_disk_tester, valid_json, monkeypatch):
    def fake_run(*args, **kwargs):
        json_file = valid_json

        del json_file["smart_status"]["passed"]

        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(json_file)
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is None

def test_check_smart_missing_table(valid_disk_tester, valid_json, monkeypatch):
    def fake_run(*args, **kwargs):
        json_file = valid_json

        del json_file["ata_smart_attributes"]["table"]

        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(json_file)
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert valid_disk_tester.check_smart() is None