# Workspace workflow

Open RecoveryPE.code-workspace in VS Code. Accept workspace trust only if you trust this project's source. Install the recommended Microsoft PowerShell extension when prompted if you want syntax support.

## Source layout

- launcher/: verified launcher prototype source
- desktop/: desktop startup and shortcut setup
- scripts/: build, dependency download, and source validation
- vendor/manifest.json and vendor/SOURCES.md: upstream versions and checksums
- vendor/WinXShell and vendor/ExplorerPP: ignored downloaded dependencies

The launcher baseline was tested successfully by the user in VMware. The desktop variant is prepared and awaiting VM validation. Checks of script syntax do not establish WinPE compatibility.

## Normal edit cycle

1. Edit source in VS Code.
2. Run Terminal > Run Task > RecoveryPE: Check source.
3. Build from a separate administrator PowerShell window. VS Code itself does not need administrator access.
4. Boot the resulting ISO in the disposable VMware VM and check the affected behavior.
5. Review Source Control changes and commit with a short description.
6. Push to the configured GitHub repository when ready.

## First-time dependencies

Install the matching Microsoft ADK Deployment Tools and WinPE add-on. Then run the Download dependencies task. It downloads pinned upstream files and checks their hashes; it does not execute downloaded programs on the host.

## Desktop build

From administrator PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\lamar\OneDrive\Documents\ChatGPT\System Recovery Project\scripts\Build-Desktop.ps1"
```

The default build folder is C:\RecoveryPE-Desktop. To keep an earlier build, append `-BuildRoot C:\RecoveryPE-Desktop-02` (choose an unused directory). The script refuses an existing build folder.

## Git and GitHub

Source control excludes ISO/WIM images, virtual disks, and downloaded binaries. Keep VMware machines and build output outside this source folder. Commit source and dependency records so builds can be recreated.

A remote URL and Git author name/email must be configured before the first commit and push. Use a GitHub no-reply email if preferred. Repository visibility is selected by the owner.

Use small commits that describe one working change. Tag versions only after their corresponding VM checks pass. Keep the original launcher ISO available as a known working recovery image.
