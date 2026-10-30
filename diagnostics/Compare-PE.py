"""Read-only comparison of 7-Zip WIM listings and extracted offline registry hives.

Requires python-registry. Never loads hives into the host registry or executes PE code.
Usage: Compare-PE.py CACHE_ROOT OUTPUT_JSON
"""
import json
import re
import sys
from pathlib import Path
from Registry import Registry

root = Path(sys.argv[1])
output = Path(sys.argv[2])
components = ["Windows/explorer.exe", "Windows/System32/comdlg32.dll",
              "Windows/System32/ExplorerFrame.dll", "Windows/System32/shellstyle.dll",
              "Windows/System32/StructuredQuery.dll", "Windows/System32/profsvc.dll",
              "Windows/System32/userinit.exe", "Windows/System32/winlogon.exe",
              "Windows/SysWOW64/ntdll.dll", "Windows/System32/wow64.dll"]
classes = {"FileOpenDialog": "{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}",
           "FileSaveDialog": "{C0B4E2F3-BA21-4773-8DBA-335EC946EB8B}",
           "ExplorerBrowser": "{71F96385-DDD6-48D3-A0C1-AE06E8B055FB}",
           "ExplorerNavigationBar": "{056440FD-8568-48E7-A632-72157243B55B}"}

def values(hive, key):
    try:
        return {v.name(): v.value() for v in hive.open(key).values()}
    except Registry.RegistryKeyNotFoundException:
        return None

def inspect(name):
    listing = (root / f"{name}-wim-list.txt").read_text(encoding="utf-8-sig")
    paths = set()
    for line in listing.splitlines():
        match = re.match(r"\d{4}-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+\s+\d+\s+\d+\s+(.+)", line)
        if match:
            paths.add(match[1].replace("\\", "/").lower())
    base = root / f"{name}-inspection" / "Windows" / "System32" / "config"
    software = Registry.Registry(str(base / "SOFTWARE"))
    system = Registry.Registry(str(base / "SYSTEM"))
    select = values(system, "Select") or {}
    control = f"ControlSet{select.get('Current', 1):03d}"
    services = {}
    for service in ["ProfSvc", "Appinfo", "RpcSs", "DcomLaunch", "Themes", "WSearch", "W32Time"]:
        entry = values(system, control + "\\Services\\" + service)
        services[service] = {k: entry[k] for k in ("Start", "Type", "ImagePath") if k in entry} if entry else None
    return {"files_in_listing": len(paths),
            "syswow64_files": sum(p.startswith("windows/syswow64/") for p in paths),
            "components": {p: p.lower() in paths for p in components},
            "setup": values(system, "Setup"),
            "winlogon": values(software, "Microsoft\\Windows NT\\CurrentVersion\\Winlogon"),
            "dialog_classes": {n: values(software, "Classes\\CLSID\\" + c + "\\InprocServer32") for n, c in classes.items()},
            "services": services}

result = {name: inspect(name) for name in ("redstone", "simplicity")}
output.write_text(json.dumps(result, indent=2, default=lambda v: v.hex() if isinstance(v, bytes) else str(v)), encoding="utf-8")
print(output)
