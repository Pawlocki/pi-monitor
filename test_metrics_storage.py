import pytest
from metrics_storage import MetricsStorage
from system_metrics import SystemMetrics
from dataclasses import replace

@pytest.fixture
def valid_metrics_storage(tmp_path):
    return MetricsStorage(str(tmp_path / "test_metrics.db"))

@pytest.fixture
def valid_system_metrics():
    return SystemMetrics(
        cpu_usage=15.5,
        ram_usage=32.4,
        cpu_temperature=54.2,
        disk_usage=23.1,
        uptime_minutes=120,
        network_status=True,
        timestamp=1000
    )


def test_save_metrics(valid_metrics_storage, valid_system_metrics):
    valid_metrics_storage.save_metrics(valid_system_metrics)

    records = valid_metrics_storage.get_latest_metrics(1)

    assert len(records) == 1

    record = records[0]

    assert record[1] == valid_system_metrics.timestamp
    assert record[2] == valid_system_metrics.cpu_usage
    assert record[3] == valid_system_metrics.ram_usage
    assert record[4] == valid_system_metrics.cpu_temperature
    assert record[5] == valid_system_metrics.disk_usage
    assert record[6] == valid_system_metrics.uptime_minutes
    assert record[7] == int(valid_system_metrics.network_status)

def test_get_latest_metrics(valid_metrics_storage, valid_system_metrics):
    metrics_list = []

    for i in range(5):
        metrics = replace(
            valid_system_metrics,
            timestamp=valid_system_metrics.timestamp + i
        )

        metrics_list.append(metrics)
        valid_metrics_storage.save_metrics(metrics)

    records = valid_metrics_storage.get_latest_metrics(3)

    assert len(records) == 3

    for record, expected in zip(records, reversed(metrics_list[-3:])):
        assert record[1] == expected.timestamp
        assert record[2] == expected.cpu_usage
        assert record[3] == expected.ram_usage
        assert record[4] == expected.cpu_temperature
        assert record[5] == expected.disk_usage
        assert record[6] == expected.uptime_minutes
        assert record[7] == int(expected.network_status)

def test_get_latest_metrics_empty_database(valid_metrics_storage):
    assert valid_metrics_storage.get_latest_metrics(2) == []

def test_max_records(tmp_path, valid_system_metrics):
    storage = MetricsStorage(
        str(tmp_path / "test_metrics.db"),
        max_records=3
    ) 

    metrics_list = []

    for i in range(5):
        metrics = replace(
            valid_system_metrics,
            timestamp=valid_system_metrics.timestamp + i
        )

        metrics_list.append(metrics)
        storage.save_metrics(metrics)

    records = storage.get_latest_metrics(10)

    assert len(records) == 3

    for record, expected in zip(records, reversed(metrics_list[-3:])):
        assert record[1] == expected.timestamp

@pytest.mark.parametrize("max_records", [0, -1, 2.5, "100", True, None])
def test_invalid_max_records(tmp_path, max_records):
    with pytest.raises(ValueError):
        MetricsStorage(str(tmp_path / "test_metrics.db"),max_records=max_records)