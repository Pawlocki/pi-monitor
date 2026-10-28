from dataclasses import dataclass


@dataclass
class DiskInfo:
    name: str
    size: str
    model: str
    transport: str
    mountpoints: list[str]
    usage_percent: float | None
    error: str | None