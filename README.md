# RecoveryPE

Learning project: an amd64 WinPE recovery environment, launcher, and desktop prototype.

## Verified baseline

The user verified RecoveryPE-Launcher.iso boots in VMware Workstation 17 and the launcher opens disk inspection, network information, Notepad, and Command Prompt.

## Desktop prototype

Run scripts/Build-Desktop.ps1 from administrator PowerShell. It creates a fresh C:\RecoveryPE-Desktop working directory using the installed ADK and matching WinPE optional components. It does not modify C:\RecoveryPE or the baseline ISO. Existing build directories are refused; supply a new -BuildRoot to retry.

The output is C:\RecoveryPE-Desktop\RecoveryPE-Desktop.iso. Attach it to the powered-off VM's CD/DVD drive, with Connect at power on enabled, and boot.

Expected: WinXShell desktop/taskbar, shortcuts and Start menu entries, and the RecoveryPE launcher. Test File Manager, Win+E, launcher reopening, switching between windows, disk inspection, and shutdown. Runtime compatibility is pending this VM test.

Explorer++ supports file changes and deletion. Use the disposable virtual disk for testing.

The desktop prototype uses upstream third-party components documented in vendor/SOURCES.md. It is not a full Windows installation and has no claim of general application compatibility.
