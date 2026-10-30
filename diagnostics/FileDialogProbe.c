#define COBJMACROS
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <shobjidl.h>
#include <stdio.h>
#include <wchar.h>

static FILE *report;
static HRESULT (WINAPI *original_co_create)(REFCLSID, LPUNKNOWN, DWORD, REFIID, LPVOID *);
static HRESULT (WINAPI *original_sh_create)(LPCWSTR, REFCLSID, IUnknown *, REFIID, void **);
static HRESULT (WINAPI *original_get_desktop)(IShellFolder **);
static HRESULT (WINAPI *original_parse_item)(PCWSTR, IBindCtx *, REFIID, void **);
static BOOL (WINAPI *original_path_exists)(LPCWSTR);
static BOOL simulate_missing_shellstyle;
static void hr_line(const wchar_t *label, HRESULT hr) {
    wprintf(L"%ls: 0x%08lX\n", label, (unsigned long)hr);
    if (report) fwprintf(report, L"%ls: 0x%08lX\n", label, (unsigned long)hr);
}
static void text_line(const wchar_t *text) {
    wprintf(L"%ls\n", text);
    if (report) fwprintf(report, L"%ls\n", text);
}
static HRESULT WINAPI trace_co_create(REFCLSID clsid, LPUNKNOWN outer, DWORD context, REFIID iid, LPVOID *result) {
    wchar_t guid[64], label[160];
    StringFromGUID2(clsid, guid, 64);
    swprintf(label, 160, L"Nested CoCreateInstance %ls", guid);
    HRESULT hr = original_co_create(clsid, outer, context, iid, result);
    hr_line(label, hr);
    return hr;
}
static HRESULT WINAPI trace_sh_create(LPCWSTR text, REFCLSID clsid, IUnknown *outer, REFIID iid, void **result) {
    wchar_t guid[64] = L"(string CLSID)", label[160];
    if (clsid) StringFromGUID2(clsid, guid, 64);
    swprintf(label, 160, L"Nested SHCoCreateInstance %ls", guid);
    HRESULT hr = original_sh_create(text, clsid, outer, iid, result);
    hr_line(label, hr);
    return hr;
}
static HRESULT WINAPI trace_get_desktop(IShellFolder **folder) {
    HRESULT hr = original_get_desktop(folder);
    hr_line(L"Nested SHGetDesktopFolder", hr);
    return hr;
}
static HRESULT WINAPI trace_parse_item(PCWSTR path, IBindCtx *context, REFIID iid, void **result) {
    HRESULT hr = original_parse_item(path, context, iid, result);
    hr_line(L"Nested SHCreateItemFromParsingName", hr);
    return hr;
}
static BOOL WINAPI trace_path_exists(LPCWSTR path) {
    BOOL exists = original_path_exists(path);
    if (wcsstr(path, L"ShellStyle.dll") || wcsstr(path, L"shellstyle.dll")) {
        text_line(exists ? L"Dialog checked ShellStyle.dll: present" : L"Dialog checked ShellStyle.dll: missing");
        if (simulate_missing_shellstyle) {
            text_line(L"Host-only simulation: returning missing ShellStyle without changing any file.");
            return FALSE;
        }
    }
    return exists;
}
static void trace_imports(HMODULE module) {
    BYTE *base = (BYTE *)module;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + dos->e_lfanew);
    DWORD imports = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (!imports) return;
    IMAGE_IMPORT_DESCRIPTOR *desc = (IMAGE_IMPORT_DESCRIPTOR *)(base + imports);
    for (; desc->Name; ++desc) {
        if (!desc->OriginalFirstThunk) continue;
        IMAGE_THUNK_DATA *names = (IMAGE_THUNK_DATA *)(base + desc->OriginalFirstThunk);
        IMAGE_THUNK_DATA *addresses = (IMAGE_THUNK_DATA *)(base + desc->FirstThunk);
        for (; names->u1.AddressOfData; ++names, ++addresses) {
            if (IMAGE_SNAP_BY_ORDINAL(names->u1.Ordinal)) continue;
            const char *name = (char *)((IMAGE_IMPORT_BY_NAME *)(base + names->u1.AddressOfData))->Name;
            void *replacement = NULL;
            if (!strcmp(name, "CoCreateInstance")) {
                original_co_create = (void *)addresses->u1.Function;
                replacement = trace_co_create;
            } else if (!strcmp(name, "SHCoCreateInstance")) {
                original_sh_create = (void *)addresses->u1.Function;
                replacement = trace_sh_create;
            } else if (!strcmp(name, "SHGetDesktopFolder")) {
                original_get_desktop = (void *)addresses->u1.Function;
                replacement = trace_get_desktop;
            } else if (!strcmp(name, "SHCreateItemFromParsingName")) {
                original_parse_item = (void *)addresses->u1.Function;
                replacement = trace_parse_item;
            } else if (!strcmp(name, "PathFileExistsW")) {
                original_path_exists = (void *)addresses->u1.Function;
                replacement = trace_path_exists;
            }
            if (replacement) {
                DWORD old_protect, unused;
                if (VirtualProtect(&addresses->u1.Function, sizeof(ULONG_PTR), PAGE_READWRITE, &old_protect)) {
                    addresses->u1.Function = (ULONG_PTR)replacement;
                    VirtualProtect(&addresses->u1.Function, sizeof(ULONG_PTR), old_protect, &unused);
                }
            }
        }
    }
}
static void check_library(const wchar_t *name) {
    HMODULE module = LoadLibraryExW(name, NULL, LOAD_LIBRARY_SEARCH_SYSTEM32);
    wchar_t label[160];
    swprintf(label, 160, L"LoadLibrary %ls", name);
    hr_line(label, module ? S_OK : HRESULT_FROM_WIN32(GetLastError()));
    if (module) FreeLibrary(module);
}
typedef HRESULT (WINAPI *GetClassObjectFn)(REFCLSID, REFIID, void **);
static void probe_legacy_startup(void) {
    text_line(L"--- Legacy editor startup check ---");
    check_library(L"SensApi.dll");
    check_library(L"dbghelp.dll");
    check_library(L"CRYPT32.dll");
    check_library(L"WINTRUST.dll");
    check_library(L"OLEAUT32.dll");
    const wchar_t *folder = L"X:\\Windows\\Temp\\SimplicityLegacyEditor-x64";
    wchar_t command[] = L"\"X:\\Windows\\Temp\\SimplicityLegacyEditor-x64\\notepad++.exe\" -multiInst -nosession -noPlugin";
    STARTUPINFOW startup = { sizeof(startup) };
    PROCESS_INFORMATION process = {0};
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
    if (!CreateProcessW(NULL, command, NULL, NULL, FALSE, 0, NULL, folder, &startup, &process)) {
        hr_line(L"CreateProcess legacy editor", HRESULT_FROM_WIN32(GetLastError()));
        return;
    }
    hr_line(L"CreateProcess legacy editor", S_OK);
    DWORD wait = WaitForSingleObject(process.hProcess, 7000);
    DWORD exit_code = 0;
    if (wait == WAIT_TIMEOUT) text_line(L"Editor is still running after 7 seconds; inspect its window or Task Manager.");
    else if (GetExitCodeProcess(process.hProcess, &exit_code)) hr_line(L"Legacy editor process exit code", (HRESULT)exit_code);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
}
static void compare_full_windows_dialog(BOOL no_ui) {
    wchar_t full_path[MAX_PATH];
    GetModuleFileNameW(NULL, full_path, MAX_PATH);
    wchar_t *slash = wcsrchr(full_path, L'\\');
    if (!slash) return;
    wcscpy(slash + 1, L"FullWindows\\comdlg32.dll");
    text_line(L"--- Direct factory test of matching full-Windows comdlg32.dll ---");
    HMODULE full = LoadLibraryExW(full_path, NULL, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    hr_line(L"Load full-Windows comdlg32.dll", full ? S_OK : HRESULT_FROM_WIN32(GetLastError()));
    if (!full) return;
    trace_imports(full);
    GetClassObjectFn get_factory = (GetClassObjectFn)GetProcAddress(full, "DllGetClassObject");
    if (!get_factory) { hr_line(L"Get DllGetClassObject", HRESULT_FROM_WIN32(GetLastError())); FreeLibrary(full); return; }
    IClassFactory *factory = NULL;
    HRESULT hr = get_factory(&CLSID_FileSaveDialog, &IID_IClassFactory, (void **)&factory);
    hr_line(L"Full-Windows DllGetClassObject FileSaveDialog", hr);
    if (factory) {
        IFileSaveDialog *dialog = NULL;
        hr = IClassFactory_CreateInstance(factory, NULL, &IID_IFileSaveDialog, (void **)&dialog);
        hr_line(L"Full-Windows CreateInstance FileSaveDialog", hr);
        if (dialog) {
            IFileSaveDialog_SetTitle(dialog, L"Full-Windows dialog diagnostic - choose Cancel");
            IFileSaveDialog_SetOptions(dialog, FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST);
            IFileSaveDialog_SetFileName(dialog, L"diagnostic-test.txt");
            if (!no_ui) {
                if (report) fflush(report);
                hr = IFileSaveDialog_Show(dialog, NULL);
                hr_line(L"Full-Windows Show Save dialog (cancel = 0x800704C7)", hr);
            }
            IFileSaveDialog_Release(dialog);
        }
        IClassFactory_Release(factory);
    }
    FreeLibrary(full);
}
int wmain(int argc, wchar_t **argv) {
    simulate_missing_shellstyle = argc > 2 && wcscmp(argv[2], L"--simulate-missing-shellstyle") == 0;
    BOOL no_ui = argc > 1 && wcscmp(argv[1], L"--no-ui") == 0;
    BOOL wait_at_end = argc > 1 && wcscmp(argv[1], L"--wait") == 0;
    BOOL legacy = argc > 1 && wcscmp(argv[1], L"--legacy") == 0;
    if (legacy) wait_at_end = TRUE;
    wchar_t temp[MAX_PATH] = L".", path[MAX_PATH];
    if (GetTempPathW(MAX_PATH, temp)) {
        swprintf(path, MAX_PATH, L"%lsSimplicity-FileDialogProbe.txt", temp);
        report = _wfopen(path, L"w, ccs=UTF-8");
    }
    text_line(L"SimplicityBRS modern file-dialog diagnostic (no registry changes)");
    if (legacy) {
        probe_legacy_startup();
        if (report) { fclose(report); wprintf(L"\nReport saved to %ls\n", path); }
        wprintf(L"\nTake a screenshot, then press Enter to close.\n"); getchar();
        return 0;
    }
    text_line(L"A test Save dialog may appear. Choose Cancel; this tool does not save a document.");
    check_library(L"comdlg32.dll");
    check_library(L"ExplorerFrame.dll");
    check_library(L"comctl32.dll");
    check_library(L"windows.storage.dll");
    check_library(L"propsys.dll");
    check_library(L"StructuredQuery.dll");
    check_library(L"shellstyle.dll");
    HRESULT initialized = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED | COINIT_DISABLE_OLE1DDE);
    hr_line(L"CoInitializeEx", initialized);
    if (SUCCEEDED(initialized)) {
        IFileSaveDialog *save = NULL;
        HRESULT hr = CoCreateInstance(&CLSID_FileSaveDialog, NULL, CLSCTX_INPROC_SERVER, &IID_IFileSaveDialog, (void **)&save);
        hr_line(L"CoCreateInstance FileSaveDialog", hr);
        if (SUCCEEDED(hr) && save) {
            IFileDialogCustomize *custom = NULL;
            hr = IFileSaveDialog_QueryInterface(save, &IID_IFileDialogCustomize, (void **)&custom);
            hr_line(L"QueryInterface IFileDialogCustomize", hr);
            if (custom) IFileDialogCustomize_Release(custom);
            hr = IFileSaveDialog_SetOptions(save, FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST);
            hr_line(L"SetOptions", hr);
            IShellItem *folder = NULL;
            hr = SHCreateItemFromParsingName(temp, NULL, &IID_IShellItem, (void **)&folder);
            hr_line(L"Create writable TEMP shell item", hr);
            if (folder) {
                hr = IFileSaveDialog_SetFolder(save, folder);
                hr_line(L"SetFolder TEMP", hr);
                IShellItem_Release(folder);
            }
            if (!no_ui) {
                IFileSaveDialog_SetTitle(save, L"Simplicity diagnostic - Cancel this test dialog");
                IFileSaveDialog_SetFileName(save, L"diagnostic-test.txt");
                if (report) fflush(report);
                hr = IFileSaveDialog_Show(save, NULL);
                hr_line(L"Show Save dialog (0x800704C7 means user cancelled)", hr);
            }
            IFileSaveDialog_Release(save);
        }
        IFileOpenDialog *open = NULL;
        hr = CoCreateInstance(&CLSID_FileOpenDialog, NULL, CLSCTX_INPROC_SERVER, &IID_IFileOpenDialog, (void **)&open);
        hr_line(L"CoCreateInstance FileOpenDialog", hr);
        if (open) IFileOpenDialog_Release(open);
        compare_full_windows_dialog(no_ui);
        CoUninitialize();
    }
    if (report) { fclose(report); wprintf(L"\nReport saved to %ls\n", path); }
    if (wait_at_end) { wprintf(L"\nTake a screenshot of these results, then press Enter to close.\n"); getchar(); }
    return 0;
}
