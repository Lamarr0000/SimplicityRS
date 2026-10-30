# SimplicityBRS

## Current Windows 11 baseline

Compatibility ISO 04 was user-verified in VMware: readable Explorer desktop, Simplicity launcher, Notepad++ launch, all save features, File > Open, and File Manager double-click reopening. Version 05 adds a clean desktop (This PC, Recycle Bin, Simplicity), cobalt launcher buttons, black background, and approximately 85% whole-window opacity. The user approved the appearance; editor regression testing on 05 has not been explicitly reported.

See [baseline preparation, findings and test history](docs/COMPATIBILITY-BASELINE.md). `scripts/Prepare-Compatibility.ps1` prepares the separate Win10XPE workspace. `scripts/Build-CleanCompatibility.ps1` applies the appearance preset to an existing compatibility-04 staging tree; it is not a fresh Windows-to-ISO builder. Required Windows sources, upstream builder, toolchains, downloaded applications and generated media are not committed. Current local appearance ISO: `C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-05.iso`.

The ADK/WinXShell instructions below describe the earlier prototype. Its modern Notepad++ file-dialog integration remains incomplete; the successful compatibility baseline uses a separate Windows 11/Explorer foundation.

## External apps

Notepad++ is now packaged outside boot.wim in the ISO's Programs directory. Desktop and launcher entries locate the correct media by a per-build marker and use RAM-backed settings. See [external app integration](docs/EXTERNAL-APPS.md) and [roadmap](docs/ROADMAP.md).

## SimplicityBRS branding

The desktop build now uses the SimplicityBRS (Backup and Recovery Suite) name, custom wallpaper, and swoosh launcher icon. Branding assets are kept in `assets/` so builds do not depend on a Pictures folder. This branding does not add backup or restore functionality.

The new desktop ISO is named `SimplicityBRS-Desktop.iso`. Build into a fresh folder, for example `-BuildRoot C:\RecoveryPE-Desktop-03`, from administrator PowerShell. Previous builds are not updated. Boot the new ISO in VMware to verify wallpaper scaling, the launcher title/icon, and desktop/Start Menu/taskbar shortcut icons. The media root includes an icon and `autorun.inf` for the mounted drive; Windows policy and caching may affect display. The ISO file's own Explorer icon is controlled by file association.

Source validation passes. The user verified the branded desktop build and, on the follow-up build in `C:\RecoveryPE-Desktop-04`, confirmed the custom icon works. The icon uses bitmap-encoded frames at 16, 24, 32, 48, 64, 128, and 256 pixels for WinPE compatibility. The launcher uses an explicit icon path. Mounted-media icon display has not been separately verified.

Learning project: an amd64 WinPE recovery environment, launcher, and desktop prototype.

## Verified baseline

The user verified RecoveryPE-Launcher.iso boots in VMware Workstation 17 and the launcher opens disk inspection, network information, Notepad, and Command Prompt.

## Desktop prototype

Run scripts/Build-Desktop.ps1 from administrator PowerShell. It creates a fresh C:\RecoveryPE-Desktop working directory using the installed ADK and matching WinPE optional components. It does not modify C:\RecoveryPE or the baseline ISO. Existing build directories are refused; supply a new -BuildRoot to retry.

The output is C:\RecoveryPE-Desktop\RecoveryPE-Desktop.iso. Attach it to the powered-off VM's CD/DVD drive, with Connect at power on enabled, and boot.

The user verified the first desktop build boots with a taskbar and launcher, and the desktop/tool checks work. It also exposed a startup console whose closure ends the WinPE session.

The updated startup uses winpeshl.ini and a windowless script host instead of the default command shell. Initialization completes before the launcher and desktop start; the host waits for the desktop shell to exit. This fix awaits a new VM test.

Test: no persistent startup command prompt, File Manager, Win+E, launcher reopening, switching between windows, disk inspection, and shutdown. Open and close a Command Prompt from the launcher and confirm the desktop remains running.

Explorer++ supports file changes and deletion. Use the disposable virtual disk for testing.

The desktop prototype uses upstream third-party components documented in vendor/SOURCES.md. It is not a full Windows installation and has no claim of general application compatibility.
