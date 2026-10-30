# External application payload

Notepad++ 8.9.8.1 x64 portable is the first external app. Its source URL, version, license and archive SHA-256 are pinned in apps/catalog.json. Downloads are from the official notepad-plus-plus GitHub releases; the recorded archive hash matches the release's GitHub asset digest. The upstream archive includes license.txt. Downloaded packages stay ignored by Git.

Run scripts/Get-Dependencies.ps1 to restore dependencies. The desktop build extracts the checksum-verified app archive into media/Programs/NotepadPP, outside boot.wim. It preserves the upstream license and package contents.

Each build writes the same fresh ID to media/SimplicityBRS.media and the WinPE image's RecoveryPE/media-id.txt. LaunchApp.vbs scans ready volumes and matches the marker, avoiding a hardcoded drive letter or accidental selection of another Simplicity build. It reports missing media/apps without ending the desktop session.

Notepad++ is launched with -multiInst -nosession -noPlugin and a -settingsDir under LOCALAPPDATA/SimplicityBRS/NotepadPP on the RAM disk. Settings disappear on reboot. Save documents to an explicitly chosen persistent disk when needed. Do not remove the boot media while external apps are in use.

The desktop, Start menu, quick-launch area, and Simplicity launcher all use the same windowless app wrapper. Windows Notepad remains available as a fallback. Notepad++ currently uses a standard text-editor shortcut icon.

The current app wrapper supports only the known notepadpp app ID. Adding another catalog item also requires defining its launch behavior; this is not yet a generic arbitrary-app execution engine.

## VMware acceptance checks

Desktop-07 result: the user reports the added file-dialog components did not resolve Save/Save As. Do not treat those additions as a verified fix. A standalone native diagnostic is being prepared to obtain the COM activation/display HRESULT without another WinPE rebuild; see diagnostics/README.md.

The first native diagnostic confirmed CLASS_E_CLASSNOTAVAILABLE (0x80040111) for both Open and Save COM activation despite successful loading of the primary DLLs. The next diagnostic compares PE's implementation with a matching-build full-Windows dialog DLL through direct class-factory calls, without changing system registration.

### Identified dialog prerequisite: ShellStyle.dll

Both reference DLL activation and the nested-call trace continued to fail with 0x80040111 in WinPE. Inspection of the matching full-Windows comdlg32 implementation identified a prerequisite check for System32/ShellStyle.dll before constructing the modern dialog. The native probe's process-local PathFileExistsW interception reproduced exactly 0x80040111 on the working host when only ShellStyle was reported absent; normal host activation succeeds. No host files or registry entries were changed for this test.

Desktop-08 now adds missing System32/shellstyle.dll and en-US/shellstyle.dll.mui using the existing Windows product-build and signature checks. It does not replace comdlg32 or downgrade Notepad++. WinPE validation remains pending: test new-file Save As, edit-and-Save, reopen, and Save a Copy As. Additional prerequisites could surface after class creation succeeds.

Desktop-08 user result: Save As now displays a location picker, but the user reports no filename entry. A saved `X:\Users\Default\Documents\new 1.txt` (6 bytes) is visible in Explorer++; opening it there reports "An attempt was made to reference a token that does not exist." Exact Save As layout and whether the token error occurs outside Explorer++ are awaiting clarification.

Prepared separately: PE-session .txt association uses a unique SimplicityBRS.Text ProgID and a direct Windows Notepad command, avoiding inherited app-activation handlers. Notepad++ launches with the writable Documents folder as its working directory. These changes are not yet VM-verified and do not claim to fix the missing filename control.

User's follow-up Save As screenshot shows the entire dialog, including Save/Cancel and Notepad++'s Append extension checkbox, but no built-in filename/type row. This is not simple off-screen clipping. The user says the saved-file error occurs regardless of where it is opened; the precise cause of that error remains unproven.

Read-only inspection of Desktop-08 boot.wim found comdlg32, its MUI/MUN resources, dui70 and duser present. The comdlg32 MUI's dialog templates match the host's templates. The image lacks StructuredQuery.dll and associated COM registrations, including Structured Query Helper and condition objects referenced by comdlg32. The next candidate adds that provider and registrations; no claim of resolution is made until VM testing.

Desktop-09 candidate: adds the matching-build signed StructuredQuery.dll and invokes its DllRegisterServer through regsvr32 at PE startup. Static import inspection found its non-API dependencies, including icu.dll, already present in the image. Startup records Documents as the Personal known folder, and the app wrapper uses Documents as its working directory. The separate direct .txt association change is also included. No DLL registration is performed on the host by the source validation checks. Acceptance remains pending: filename/type controls, named Save As, edit-and-Save, reopen through File > Open and via File Manager.

The user confirmed Notepad++ launches and the icon decoder fix works in VMware. The Start menu entry was also observed. Save/reopen, all shortcut entry points, and physical USB checks remain unconfirmed.

Follow-up: the user reports Windows Notepad saves correctly, but Notepad++ save operations do not work. Modern Notepad++ 8.9.8.1 uses COM-based FileSaveDialog/FileOpenDialog (see upstream CustomFileDialog.cpp). Investigate dialog creation/registration and initial working directory separately from disk write access. Exact failure behavior is awaiting user clarification; no save fix has been verified.

The user clarified that Save commands silently close the menu with no dialog or error. A query inside WinPE confirmed FileSaveDialog registration already points to comdlg32.dll with Apartment threading. The build now adds missing comctl32.dll and ExplorerFrame.dll, together with ExplorerFrame's en-US MUI and MUN resources, from matching-build signed Windows files. The source directory defaults to the local Windows directory and can be supplied using -WindowsComponentSource. Existing image files are preserved. Startup ensures the ExplorerFrame CLSID {056440FD-8568-48e7-A632-72157243B55B} has registration only if it was missing.

Integration reference: https://github.com/slorelee/wimbuilder2/blob/45b9fa4b257ff67658f9365b8a4c95bbaf4e0673/Projects/WIN10XPE/shared/NewBrowseDlg/main.bat . This is a candidate fix, not a verified resolution. Next test: build Desktop-07, open Notepad++, Save As to the RAM desktop, reopen the file, edit and Save it, and try Save a Copy As.

1. Build into a new directory, such as C:\RecoveryPE-Desktop-05.
2. Boot its SimplicityBRS-Desktop.iso.
3. Open Notepad++ using the launcher, desktop shortcut, and Start menu.
4. Create text, save it to X:\Users\Default\Desktop\editor-test.txt, close and reopen it. This tests RAM-disk writes only.
5. Confirm settings writes produce no read-only-media error.
6. Open another app, close Notepad++, and confirm the desktop remains running.
7. Confirm the external Programs directory is on the mounted ISO, not inside X:\Program Files.
8. For physical USB acceptance, confirm discovery and launches after booting on a machine with a different drive-letter assignment.

Host checks validate source syntax, media matching, settings-directory creation, and command quoting. The user additionally verified application launch in WinPE and the icon decoder fix.

## First VM test: icon decoder dependency

The user reached Notepad++ in the Desktop-05 build, confirming external media discovery and startup. Notepad++ then displayed `IconList::addIcon : LoadIcon() function return null`, with icon resource ID 501. Application editing/saving has not yet been verified.

Upstream issue https://github.com/notepad-plus-plus/notepad-plus-plus/issues/15465 reports the same error and identifies IconCodecService.dll as a cause. The user subsequently confirmed that adding the matching decoder fixed the error in our build.

The build now supplies Windows' IconCodecService.dll when absent from the mounted image. The default source is the local Windows System32 directory; it must have a valid signature, x64 PE architecture, and the same Windows major/minor/build as the mounted WinPE kernel. The current host file is 10.0.26100.1, with a valid Microsoft signature. No Windows DLL is committed to Git. A different build machine can supply -IconCodecSource with a matching Windows file. An existing decoder in WinPE is preserved.

Build into a new directory such as C:\RecoveryPE-Desktop-06. Acceptance: Notepad++ starts without the icon dialog, displays tab/toolbar icons, opens from all three entry points, and can save/reopen a test file on the RAM desktop.
