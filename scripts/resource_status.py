"""Read-only resource snapshot for conservative batch operation; no guessed temperature."""
import json
import os
import platform
from pathlib import Path
import subprocess


def snapshot():
    result = {'platform': platform.system(), 'logical_cpu_count': os.cpu_count(), 'temperature': None}
    if hasattr(os, 'getloadavg'):
        result['load_average'] = list(os.getloadavg())
    if platform.system() == 'Darwin':
        result['memory_pressure'] = subprocess.run(['memory_pressure'], capture_output=True, text=True).stdout.strip()
        result['thermal_status'] = subprocess.run(['pmset', '-g', 'therm'], capture_output=True, text=True).stdout.strip()
    elif platform.system() == 'Linux':
        result['meminfo'] = Path('/proc/meminfo').read_text()
        zones = []
        for path in Path('/sys/class/thermal').glob('thermal_zone*'):
            try:
                zones.append({'type': (path / 'type').read_text().strip(), 'celsius': int((path / 'temp').read_text()) / 1000})
            except (OSError, ValueError):
                pass
        result['thermal_zones'] = zones  # May be empty in a VM/container; not a measurement of GPU temperature.
    elif platform.system() == 'Windows':
        import ctypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('memory_load', ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in ('total_phys', 'avail_phys', 'total_pagefile', 'avail_pagefile', 'total_virtual', 'avail_virtual', 'avail_extended')]
        status = MemoryStatus(); status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            result['available_memory_bytes'] = status.avail_phys; result['memory_load_percent'] = status.memory_load
        result['thermal_status'] = 'Not available via standard library; check vendor/OS monitor'
    return result

if __name__ == '__main__':
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
