# File dialog diagnostic

Native x64 diagnostic for the silent Notepad++ Open/Save failure in minimal WinPE. It logs DLL load failures and HRESULTs from COM dialog activation, interface queries, folder selection, and dialog display. It does not register components or write a user document. Its report is saved to TEMP/Simplicity-FileDialogProbe.txt.

Run Run-Diagnostic.cmd in WinPE. If a Save dialog appears, choose Cancel. Photograph the console results. The diagnostic can be supplied on a separate, nonbootable ISO without rebuilding WinPE.

Close Notepad++ before replacing its ISO. To avoid disturbing the main application media, a second virtual CD/DVD drive can be attached to the VM instead.

## Reproduce the diagnostic build

The locally cached compiler is Zig 0.15.2, downloaded from the official publisher:
https://ziglang.org/download/0.15.2/zig-x86_64-windows-0.15.2.zip

Archive SHA-256: 3a0ed1e8799a2f8ce2a6e6290a9ff22e6906f8227865911fb7ddedc3cc14cb0c

Extract under %LOCALAPPDATA%/SimplicityBRS/toolchains so zig.exe is at %LOCALAPPDATA%/SimplicityBRS/toolchains/zig-x86_64-windows-0.15.2/zig.exe. This keeps compiler files outside the OneDrive project. Run scripts/Build-Diagnostics.ps1 with an unused output directory. The diagnostic is built from diagnostics/FileDialogProbe.c. Compiler binaries and generated outputs are excluded from Git.

--no-ui tests dialog activation without displaying it. --wait retains the console for reading. Run in the affected WinPE build for relevant results; successful host activation alone does not establish WinPE support.

First WinPE result: comdlg32, ExplorerFrame, comctl32, windows.storage, and propsys load successfully. StructuredQuery and shellstyle report 0x8007007E (module/dependency not found). CoInitializeEx succeeds, but both FileSaveDialog and FileOpenDialog activation report 0x80040111 (CLASS_E_CLASSNOTAVAILABLE).

The follow-up disc includes a Microsoft-signed full-Windows comdlg32.dll from build family 26100. The probe loads it by explicit path and calls its class factory directly, without modifying COM registration or replacing WinPE's system DLL. This tests whether the reduced PE DLL or a common dependency/environment restriction is responsible. The reference DLL is only on the generated local diagnostic ISO; it is not tracked in Git.

Follow-up WinPE result: the full-Windows DLL loads and supplies its FileSaveDialog class factory (S_OK), but CreateInstance returns 0x80040111. Replacing comdlg32 alone is therefore not sufficient.

## Red Stone editor comparison

The first reference-editor disc copied Red Stone's 7.5.6 application directory. The user encountered side-by-side activation error 0x800736B1. A subsequent PE-header check found both notepad++.exe and SciLexer.dll are x86 (0x014C), while Simplicity is minimal amd64. This architecture mismatch should have been checked before packaging.

The corrected comparison disc is C:\Simplicity-Reference-Editor-x64\Simplicity-Reference-Editor-x64.iso. It uses the official upstream 7.5.6 x64 ZIP at https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v7.5.6/npp.7.5.6.bin.x64.zip, preserves license.txt, and verifies the executable's PE machine is AMD64 before packaging. Double-click TestReferenceEditor.vbs inside the recovery VM. It copies the editor to a distinct temporary RAM directory, seeds the legacy-dialog setting observed in Red Stone, and launches with plugins disabled. Test Save As and reopen a RAM-desktop file. No change is made to the selected Simplicity app version. This old release is for a controlled compatibility comparison, not an approved product downgrade. Its binaries are not tracked in Git.

Corrected x64 reference result: a startup diagnostic confirmed the checked DLLs load and CreateProcess succeeds, but the editor exits with 0xC0000005 (access violation). The old release is not a viable fallback in its current form. No Save dialog behavior was verified.

The current modern-dialog probe traces calls to CoCreateInstance and SHCoCreateInstance imported by its explicitly loaded reference comdlg32.dll. Hooks exist only in the diagnostic process's import table, log nested class IDs/HRESULTs, and do not alter files, registry, or other applications. This is intended to identify a failing child COM object during dialog initialization.

## ShellStyle prerequisite reproduction

The nested-call trace did not add information. Inspection of matching comdlg32 code then identified a check of theme application properties and PathFileExistsW for %SystemRoot%/System32/ShellStyle.dll before modern file-dialog construction. Missing ShellStyle causes the same CLASS_E_CLASSNOTAVAILABLE result.

The probe now records that path check in its explicitly loaded reference DLL. `--no-ui --simulate-missing-shellstyle` makes only this diagnostic process report ShellStyle missing. On the host, ordinary activation succeeds; this simulation reproduces 0x80040111 during CreateInstance. No Windows file is removed or changed and no registry setting is modified. Desktop-08 adds the missing DLL and en-US resource for actual WinPE verification.

## Desktop-09 runtime result

User testing confirmed no improvement to the missing filename field or saved-file opening. Startup reported StructuredQuery self-registration failure (regsvr32 exit code 5). This exit code identifies a registration-routine failure; it is not by itself proof of Windows access-denied error 5. Removed the unsuccessful automatic registration and extra StructuredQuery copy from future builds. Existing Desktop-09 ISO remains unchanged. Save/Open is still unresolved; VMware interaction is user-operated.

