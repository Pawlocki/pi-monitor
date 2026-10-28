from pathlib import Path
from time import perf_counter
import tempfile
import os
import subprocess
import json

class DiskTester:
    def __init__(self, disk_path: str, device_path: str):
        self.disk_path = Path(disk_path)
        self.device_path = device_path

    def test_data_integrity(self) -> bool:
        data = os.urandom(1024 * 1024)

        try:
            with tempfile.NamedTemporaryFile(dir=self.disk_path) as temp:
                for _ in range(10):
                    temp.write(data)

                temp.flush()
                os.fsync(temp.fileno())
                temp.seek(0)

                for _ in range(10):
                    if temp.read(1024 * 1024) != data:
                        return False

                return True

        except OSError:
            return False

    def measure_read_speed(self) -> float | None:
        data = os.urandom(1024 * 1024)
        size = 0

        try:
            with tempfile.NamedTemporaryFile(dir=self.disk_path) as temp:
                for _ in range(100):
                    temp.write(data)

                temp.flush()
                os.fsync(temp.fileno())
                temp.seek(0)
                os.posix_fadvise(temp.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)

                start = perf_counter()

                while chunk := temp.read(4096):
                    size += len(chunk)

                end = perf_counter()

            elapsed = end-start
            if elapsed > 0:
                return size / (elapsed * 1024 * 1024)

            return None

        except OSError:
            return None

    def measure_write_speed(self) -> float | None:
        try:
            data = os.urandom(1024 * 1024)

            with tempfile.NamedTemporaryFile(dir=self.disk_path) as temp:
                start = perf_counter()

                for _ in range(100):
                    temp.write(data)

                temp.flush()
                os.fsync(temp.fileno())

                end = perf_counter()
            
            elapsed = end-start
            if elapsed > 0:
                return 100/elapsed
            
            return None
        except OSError:
            return None

    def check_smart(self) -> bool | None:
        try:
            result = subprocess.run(["smartctl", "-aj", self.device_path], capture_output=True, text=True)
            data = json.loads(result.stdout)
            
            if result.returncode & 0b00000111:
                return None

            passed = data.get("smart_status", {}).get("passed")

            if passed is False:
                return False
            
        except (OSError, json.JSONDecodeError):
            return None
        
        try:    
            attributes = data["ata_smart_attributes"]["table"]
            required_ids = {5, 197, 198}
            found_ids = set()
            
            for attribute in attributes:
                if attribute["id"] in required_ids:
                    found_ids.add(attribute["id"])

                    value = attribute["raw"]["value"]

                    if type(value) is not int or value < 0:
                        return None

                    if value > 0:
                        return False

            if found_ids != required_ids:
                return None

            return passed if isinstance(passed, bool) else None
            
        except (KeyError, TypeError, ValueError):
            return None

def main():
    tester = DiskTester("/media/usb", "/dev/sda")

    print(tester.check_smart())

if __name__ == "__main__":
    main()