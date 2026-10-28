Raspberry Pi System & Disk Monitor

A Python application for monitoring Raspberry Pi performance and connected storage devices. Every 60 seconds, it collects CPU and RAM usage, CPU temperature, disk usage, uptime, and network status. Measurements are stored in SQLite, while configurable thresholds trigger warnings in the terminal.

The project detects connected disks and includes standalone data integrity tests, read/write speed measurements, and S.M.A.R.T. health checks. These diagnostics are implemented but are not yet integrated into the main monitoring loop.

The code is organized into separate classes for monitoring, disk testing, health checks, and storage. Automated unit tests use Pytest fixtures, parametrization, and mocking to validate functionality and error handling.

A desktop GUI for viewing live and historical metrics, along with integration of disk diagnostics into the main application, is planned for a future update.

Running the project

Designed for Raspberry Pi running Linux. Install dependencies with pip install -r requirements.txt, check the device-specific settings in monitor.py, and run python monitor.py. To execute the tests, install Pytest and run python -m pytest.