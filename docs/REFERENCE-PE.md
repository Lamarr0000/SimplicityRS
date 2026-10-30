# Gandalf Red Stone 3 reference image

Inspected October 29, 2026 at the user's request. Source: E:\Continuity\Tools\ISOs\Red_Stone3.iso. File size: 4,648,009,728 bytes. Host last-modified timestamp: September 2, 2020 (not proof of release date).

Mounted read-only through Windows' ISO facility for inspection, then dismounted. No bundled applications were executed or copied into Simplicity.

## Observed organization

- Volume label: Red Stone 3.
- Boot and efi directories plus sources/boot.wim (1,225,949,572 bytes).
- A separate Programs directory outside the boot WIM contains the application collection.
- Win10PE.cd, CdUsb.Y, TheOven_Startup_CD.cmd, and pecmdExt.ini provide media/startup integration clues.
- Sysinternals_Suite is one bundled application directory; this does not establish that Microsoft Sysinternals authored the PE distribution.

## Requested tools found

| Tool | Executable version observed |
| --- | --- |
| Acronis TrueImage | 20.0.0.5554 |
| Lazesoft DataRecoveryApp / DiskImageCloneApp | 4.0.0.1 |
| Notepad++ | 7.56 |
| Firefox | 59.0.3 |
| Chrome (64-bit portable folder) | 64.0.3282.186 |
| ImgBurn | 2.5.8.0 |
| Recuva x64 | 1.53.0.1087 |

Other observed folders include AOMEI Backupper, Macrium Reflect Home, InfraRecorder_x64, OperaPortable, PENetwork, and multiple disk/partition recovery tools. No Edge-named folder was present in the external Programs directory; the boot WIM was not inspected, so this is not a conclusion about its entire contents.

## Implications for Simplicity

### Notepad++ Save dialog comparison

On follow-up inspection, Red Stone's `Programs/Notepad++Portable/Data/Config/config.xml` sets `<GUIConfig name="MISC" ... newStyleSaveDlg="no" ... />`. Its Notepad++ executable reports 7.56 (upstream version 7.5.6).

The upstream v7.5.6 `PowerEditor/src/WinControls/OpenSaveFileDialog/FileDialog.cpp` uses the older GetOpenFileName/GetSaveFileName APIs. Simplicity's 8.9.8.1 uses COM FileOpenDialog/FileSaveDialog. The older image therefore provides a useful legacy-dialog example, but it is not testing the same dialog implementation as our current app. Copying `newStyleSaveDlg="no"` into the current app is not assumed to work.

PE-header inspection also confirmed Red Stone's Notepad++ and SciLexer.dll are x86 (machine 0x014C). The first isolated reference test failed with a side-by-side activation error on minimal amd64 WinPE. A corrected comparison uses upstream's x64 release of the same version; the original binary comparison was invalid for this environment.

This is a concrete version/configuration difference relevant to the silent Save failure. Simplicity's native diagnostic reports CLASS_E_CLASSNOTAVAILABLE for the modern classes. Continue the modern implementation comparison before deciding whether a compatibility alternative is needed.

Upstream legacy source: https://github.com/notepad-plus-plus/notepad-plus-plus/blob/v7.5.6/PowerEditor/src/WinControls/OpenSaveFileDialog/FileDialog.cpp

This is concrete reference material for the app collection the user wants. Folder presence and executable metadata establish inclusion, not runtime success in Simplicity. The user knows these tools work in the reference environment. New app versions may need different libraries, services, drivers, registry configuration, or architecture support.

The external Programs layout is a useful alternative to placing every application in the RAM-loaded WIM. Evaluate a small boot image plus a discoverable application payload on the ISO/USB, with writable profiles/cache staged in RAM where necessary. Retain the planned multiboot USB entries for Simplicity and official Windows 11 installation media.

Use the reference to understand integration, while acquiring selected app versions from publisher sources and observing their licensing. In particular, evaluate current browsers for the Microsoft account recovery-key workflow rather than adopting the old browser binaries in this reference.

## Boot WIM and offline registry comparison

Follow-up inspection used 7-Zip 26.05 and python-registry without elevation. Extracted configuration and hives were read as files, never loaded into the host registry. No reference executable was run. The archive reader warned about incorrect reference counts, so inventory counts are advisory. WIM metadata identifies Windows build 16299.15 x64; the friendly image name "Windows PE 4.0" is not a reliable OS version.

| Area | Red Stone 3 | Simplicity Desktop-09 |
| --- | --- | --- |
| Boot entry, offline SYSTEM Setup/CmdLine | PECMD, SwitchToAdmin.ini | winpeshl.exe, our windowless startup host |
| Desktop shell | Microsoft Windows Explorer | WinXShell plus Explorer++ |
| User/session preparation | Administrator session switch, profile and logon setup | Explicit Default profile environment in PE startup |
| External applications | Mounted/discovered as Y:, Programs payload | Matching media GUID discovery, external Programs |
| 32-bit subsystem | wow64.dll and extensive SysWOW64 payload | wow64.dll absent; some SysWOW64 files present do not establish executable support |
| File-dialog classes | Registered | Open/Save registered, but runtime controls incomplete |
| Appinfo / Themes service keys | Present | Absent |
| ProfSvc / RPC / DCOM service keys | Present | Present; configuration differs |

The key finding is the **session model**, not simply additional DLLs. SYSTEM Setup/CmdLine points to SwitchToAdmin.ini. Its command script sets t=0 and directly chooses LoadAdminSession. SwitchToAdminPrepare.ini prepares the workgroup and Administrator logon, starts gpsvc/ProfSvc/seclogon/ShellHWDetection, and disconnects the initial session. SwitchToAdminLogon.ini then initializes the user desktop and starts Explorer. These are configured startup actions, not a live trace proving every service succeeded.

Simplicity's StartDesktop.vbs instead sets USERPROFILE/APPDATA/LOCALAPPDATA to Default and starts its shell without a comparable logon transition. This makes session/token support a credible lead for the reported missing-token error; it does **not** prove the filename-control issue has the same cause. File presence or registry service Start values also do not prove runtime health.

Both images contain ProfSvc and userinit/winlogon binaries. It would be inaccurate to say that Simplicity lacks all profile facilities. Likewise, Redstone uses an older Notepad++ with a different file-dialog implementation, so it does not establish modern Notepad++ compatibility.

Reproduction: diagnostics/Compare-PE.py reads the two saved archive listings and extracted SOFTWARE/SYSTEM files under the local inspection cache and writes a focused JSON comparison. Full extracted hives stay outside Git.

## Separate compatibility baseline

See [compatibility baseline](COMPATIBILITY-BASELINE.md). Preserve the existing ADK build and reproduce a coherent Explorer/Administrator/WoW64 foundation using matching Windows source through a maintained build recipe. Do not transplant build-16299 system files or whole registry hives into build-26100 PE.
