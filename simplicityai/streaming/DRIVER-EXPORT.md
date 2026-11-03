# Driver packages: inventory, export and integrity checks

This isolated prototype uses Microsoft's fixed DISM PowerShell commands:
`Get-WindowsDriver` and `Export-WindowsDriver`. It never installs or removes drivers,
mounts images, unlocks BitLocker or loads offline registry hives.

## Use

Close the pilot and run `launch_admin.py` using the existing pilot Python to request
administrator permission. Approve the Windows UAC prompt yourself. This starts only
the isolated prototype; the normal installed application is unchanged.

- “Back up my drivers” inventories running Windows and prepares a plan.
- “Recover drivers from offline Windows at E:\” selects that image root explicitly.
  Supply the root containing Windows, not a WIM file or a guessed drive letter.
  If Windows is mounted in a folder, supply that folder's full local path.
- Optional: “Back up drivers from E:\ to D:\Backups”. The destination parent must
  already exist. Offline export requires a different destination volume from the
  source; there is no automatic source/destination selection.
- Review source, destination and package count, then say “export drivers”.
- “List driver packages from E:\” inventories that selected offline image.
- “Verify driver backup” rereads the last backup from this session. After reopening,
  use “Verify driver backup from D:\Backups\DriverBackup-...”.

Plain “yes” is not export confirmation. Plans expire after ten minutes and are
consumed before dispatch. Cancellation, another task, New chat or closing the app
invalidates the plan. Unknown or failed exports are never replayed automatically.

## Results and limits

Exports create a unique folder, a status record, DISM log, package inventory and a
SHA256 manifest. Package INF names/count must cover the inventory; every package
file is hashed and reread. Verification checks for missing, changed and unexpected
package files. The local manifest is not tamper-proof or a certificate of trust.
Root operation logs/status/scratch are excluded from package integrity checks.

A failed/cancelled export retains partial files and a partial status record; it is
not a verified backup. Nothing overwrites or deletes an existing destination.
At least 1 GiB free is required to start; this is a floor, not a size estimate.
Large driver stores may need substantially more space and time.

Only third-party INF-style packages are exported. Windows inbox drivers, vendor
applications/settings and EXE/MSI installers are outside the backup. Successful
export/hash checks do not prove hardware function, signature authenticity, update
currency, restoration success or compatibility with a different computer.

Mounted offline Windows must be accessible and already unlocked. Drive-letter
discovery is only a candidate list; folder-mounted installations need an explicit
path. UNC/network/device paths and reparse points are refused. No VM host access
is gained unless its Windows volume is actually exposed to this environment.
DISM and Windows may write normal servicing logs; no source-image modification
operation is requested. Use trusted source images; this is not a hardened sandbox
for actively hostile filesystem changes during export.

## Validation

`check_driver_packages.py` uses synthetic packages and temporary directories to
exercise manifests, corruption, missing/extra files, cancellation, source swaps,
expiry, changed inventory, existing destinations and explicit selection/confirmation.

`check_driver_live.py --export` is a separate opt-in elevated acceptance check. It
exports real **online** packages to a new folder under
`C:\SimplicityAI-Lab\ControlAdapter` and records a report there. It does not test an
offline image. `launch_admin.py --validate` requests one UAC elevation for that
check and starts the updated elevated pilot afterward, microphone off.

Sources:
- https://learn.microsoft.com/en-us/powershell/module/dism/export-windowsdriver
- https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism-driver-servicing-command-line-options-s14
