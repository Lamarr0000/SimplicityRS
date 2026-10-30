# Separate compatibility baseline

Prepared October 29, 2026 following the read-only Red Stone audit. This is an experiment, not a replacement for the verified Simplicity desktop or a claim that Notepad++ works.

## Selected experiment

Use upstream Win10XPE 2023-08-23, with its coherent Explorer shell, Administrator session support, WoW64, and Windows component/registry recipes. Upstream describes a WinRE-based build and lists Windows 11 build 22000 source support:
https://github.com/ChrisRfr/Win10XPE

This is a candidate to test, not a claim that this older project supports every current Windows release. Existing source E:\Continuity\Tools\ISOs\Win11_English_x64.iso has setup.exe version 10.0.22000.1. This is an older compatibility experiment; select current supported source/builder combinations separately before general distribution. Do not combine this source with host build-26100 system files or the current ADK-copy patches.

Workspace: C:\SimplicityBRS-Compatibility, outside OneDrive and the Git repository. Official archive parts were downloaded from ChrisRfr/Win10XPE. Repository HEAD at preparation: 9b9a34e6d0091f237031d9187a06c3d34b3d487e. Local downloaded SHA-256 values (provenance records, not independent publisher signatures):

| Part | SHA-256 |
| --- | --- |
| .001 | 70ea60f2d3c34cc17b477b75fd19209b012b9a1055e46b6f581416457b93aace |
| .002 | f1563166d86e8f66a39109e6072ffc63aba3aa9eb528f68960f9d67308d4b945 |
| .003 | 7419fc5584de187687425f494d10f00e2fbd5b0db1d05d9afd8f9196181f463f |

No security exclusions or changes to host protection are part of this workflow.

## Prepared settings and payload

scripts/Prepare-Compatibility.ps1 copies the mounted Windows source to WindowsSource without deleting existing files. It backs up Core.script once, selects Explorer, Administrator switching, basic WoW64, network additions and VC runtimes, and retains external Programs. It stages the same checksum-pinned modern Notepad++ version as Simplicity under Custom/x64/IsoRoot/Programs/SimplicityTest/NotepadPP. A Public Desktop test launcher uses its external Y: path and temporary writable settings. The Simplicity wallpaper is staged through the builder's supported Custom directory.

The main Simplicity StartDesktop.vbs and InitDesktop.vbs are deliberately not applied: they would replace the session behavior this experiment is intended to test. Integrate the main launcher through the builder's user startup hooks only after the baseline passes. Existing included builder applications are not approved toolkit selections.

## Build and acceptance

This tool session is not elevated. No ISO is claimed to have been generated. In an elevated builder:

1. Open C:\SimplicityBRS-Compatibility\builder\Win10XPE\Win10XPE.exe.
2. Select C:\SimplicityBRS-Compatibility\WindowsSource and an x64 edition through the source selector, allowing its metadata detection to run.
3. Review Build Core: Explorer, Switch To Admin, WoW64 Basic; external Programs (Run ALL Programs From RAM unchecked). Keep only needed bundled apps for the comparison.
4. Build with the main Play button. Retain the log and generated ISO path; do not assume a specific output file exists.
5. User attaches the resulting ISO in VMware. Confirm the Administrator desktop appears, then run Test latest Notepad++.cmd.
6. Enter text and Save As to Documents with an explicit new filename; verify filename/type controls are present, content is correct, and File > Open and double-click both reopen it. Repeat Save after editing. Check the actual latest version in About to avoid confusing a bundled older editor with the test payload.

Only after those tests pass: add Simplicity launcher startup, preserve external app discovery and RAM settings, verify shutdown, then proceed to one browser and BitLocker tooling. A failed comparison should be investigated from its build/runtime logs before another component-copy build is proposed.

## First generated comparison ISO

WinBuilder generated Win10XPE_x64.ISO at 16:29 on October 29. Optional MPC-BE/AOMEI/Chrome downloads failed. Host Code Integrity blocked DrvInstPatch.exe; upstream identifies this optional helper as patching drvinst.exe to ignore signed-catalog validation. Host protections were not changed. The generated core remains unverified in VMware.

The original ISO lacked the custom external test payload because Create ISO / Include Files In ISO Root was unchecked. Copied the prepared SimplicityTest payload into the staging ISO/Programs folder, enabled that inclusion setting for future builds, and repackaged with the installed Microsoft OSCDIMG using BIOS and UEFI boot entries. Corrected test ISO: C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-01.iso. This packaging correction does not resolve or conceal the earlier optional app failures. Test the core and exact latest Notepad++ before relying on any other bundled app.


## Display-only comparison 02

User reports diagonal desktop corruption after both accepting and declining the Administrator switch. This rules out that switch as the sole trigger. The common Pecmd.ini startup force-loads display drivers, runs FixScreen.exe and requests 1024x768 followed by 1366x768. Candidate 02 replaces that sequence with one 1024x768x32 request and skips forced display-driver reload and FixScreen. Session settings, applications and other image contents remain the same. Source candidate is stored at C:\SimplicityBRS-Compatibility\DisplayTest02\Pecmd.ini; a copied media tree was updated using the builder's wimlib-imagex update command. Extracted updated configuration was hash-compared to the input before BIOS/UEFI ISO packaging. New ISO: C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-02.iso. Earlier ISOs were preserved. Runtime display behavior is not yet verified.


## Launcher comparison 03

User verified candidate 02 renders correctly and regular Notepad saves. Notepad++ Save/Open remains untested. Candidate 03 preserves candidate 02 startup/display settings, adds the Simplicity HTA, normal Explorer file-manager button, GUID-discovered external Notepad++ payload and settings helper, explicit Default/Administrator/Public desktop shortcuts, and a common Startup shortcut. Does not replace Winpeshl, PECMD or profile initialization. ISO: C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-03.iso. Runtime launcher startup and modern Notepad++ file operations still require user testing.


## Launcher comparison 04

User verified the launcher appears in 03, but launching Notepad++ fails in ExternalApps EnsureAppFolder with out-of-memory (800A0007). The recursive helper had no guard for empty/nonexistent root parents, so an invalid settings path could recurse indefinitely. Fixed guards for empty/unexpanded paths, TEMP fallback when LOCALAPPDATA is undefined, and working-directory fallback if Documents is unavailable. Regression tests cover unresolved environment paths and reject empty recursion. Candidate 04 adds the HKCU text-file association via an Explorer-session startup helper, preserving PECMD and display settings. Updated WIM scripts were extracted and hash-verified. ISO: C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-04.iso. Runtime app launch, file operations and association still need verification.


## User-verified checkpoint: candidate 04

User confirmed: launcher works, Notepad++ launches, and all its save features work. Candidate 02 display correction is retained. Preserve C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-04.iso as the working compatibility checkpoint. Separate File > Open / Explorer double-click reopening and the new .txt association were not explicitly confirmed by this report. Do not generalize this result to the older ADK Desktop-09 baseline or untested bundled applications.


User additionally confirmed reopening saved files through Notepad++ File > Open and by double-clicking in File Manager. Candidate 04 passes the agreed editor save/reopen acceptance checks.


## Clean desktop candidate 05

Requested appearance: only This PC, Recycle Bin and Simplicity launcher on the desktop; remove the regular Notepad launcher button; cobalt-blue buttons and black background at 85% opacity. Candidate 05 preserves verified 04 app/session behavior and the display fix. It removes PECMD desktop-link creation while retaining Start menu links, removes test/editor desktop shortcuts from a copied WIM, retains one Public Desktop Simplicity shortcut, and explicitly controls Explorer namespace icons in the existing user-session startup helper. Regular Notepad remains installed for the existing .txt handler; its launcher button is removed.

New compatibility launcher source: launcher/SimplicityDesktop.hta. Buttons use cobalt #0047AB; background is #000000. desktop/LauncherOpacity.c is a small x64 Win32 helper scoped to the SimplicityBRS HTA window title and class. It sets layered-window alpha 217/255 (approximately 85%); this is whole-window opacity, including text and buttons, because the HTA implementation does not provide independent translucent desktop-backed background composition. This limitation was explained before building. No security settings changed.

Reproduce with scripts/Build-CleanCompatibility.ps1 using an unused build/output path. It compiles the helper with cached Zig, modifies a copy of the 04 staging media, hash-checks extracted updated WIM files and packages BIOS/UEFI ISO. Source syntax and existing functional helper tests pass. Offline inventory confirms only one desktop shortcut and no active PECMD desktop LINK entries. Runtime appearance/opacity and editor regression checks are pending. ISO: C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-05.iso. Preserve 04 as the last user-verified functional checkpoint until 05 is confirmed.

