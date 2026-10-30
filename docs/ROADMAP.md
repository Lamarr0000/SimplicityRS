# SimplicityBRS roadmap

Recorded from the user's restated requirements on October 29, 2026 after part of the chat history became unavailable. These are requested capabilities, not claims that the applications have been integrated or tested.

Reference environment: the user's Gandalf Red Stone 3 ISO has been inspected; see [reference findings](REFERENCE-PE.md). It contains the requested editor, recovery tools, Firefox, and Chrome in an external Programs payload. Use its layout and integrations to inform implementation.

## Recovery toolkit

| Requested application or capability | Purpose | Selection status |
| --- | --- | --- |
| Notepad++ (user wrote Note++) | Edit text, logs, and scripts | Requested; verify x64 portable build in WinPE |
| Lazesoft (user wrote Lazsoft) | Windows recovery utilities | Requested; assess supported recovery functions, PE integration, and licensing |
| Acronis or a free/open-source alternative | Disk backup, imaging, and restore | Requested; evaluate candidates and recovery-media requirements |
| File undelete utility | Recover deleted files | Requested; select a compatible tool and test on disposable data |
| ImgBurn (assumed from Image burn) or a free/open-source alternative | Disc image creation and burning | Requested; confirm intended app/capabilities and check PE device support |

Free and open-source alternatives are acceptable. Free-of-charge software is not necessarily open source or redistributable. Check publisher sources, architecture, dependencies, PE compatibility, and redistribution terms before inclusion. Where a tool requires its own recovery media, consider a separate boot option rather than assuming its Windows application runs in PE.

## Browsers

Requested: Microsoft Edge, Mozilla Firefox, and Google Chrome.

Validate each browser in the actual WinPE build, including HTTPS, networking, fonts, certificate handling, and Microsoft account sign-in. Integration is conditional on compatibility and distribution terms. Start with one proven browser to support the recovery-key workflow, then evaluate the others. A portable package alone does not establish WinPE compatibility.

## BitLocker unlock and key retrieval

1. Detect encrypted volumes and display drive identity and lock status.
2. Where available, show the recovery key ID so the user can match the drive to the correct saved key.
3. Allow the user to enter their 48-digit BitLocker recovery key and unlock the selected volume using Windows' supported BitLocker facilities.
4. Provide the requested retrieval button, using the clearer label **Retrieve my BitLocker recovery key**, opening https://aka.ms/myrecoverykey in a tested browser.
5. Explain that the user must sign into the Microsoft account where their key was backed up. The link does not guarantee a key is available; work/school-managed devices may require the organization's recovery process.
6. Also display the URL for use on another device when networking or the browser is unavailable.
7. Do not persist recovery keys in source files, logs, diagnostic reports, or saved settings. Clear the entry after an unlock attempt. Do not automatically decrypt the disk or disable its protection.

Terminology: the recovery key is the 48-digit recovery password, distinct from a startup PIN. The original requested button wording was "Retrieve my bit locker Recovery Pin"; final UI should use "recovery key" for clarity.

Microsoft reference: https://support.microsoft.com/en-gb/windows/security/encryption/find-your-bitlocker-recovery-key

## Suggested implementation order

This ordering is a proposed next-step sequence, not a previously recovered agreement:

1. Preserve the verified desktop/launcher build and current branding.
2. Integrate and test Notepad++ and one browser.
3. Add BitLocker volume discovery, unlock UI, and recovery-key retrieval link; test against a disposable encrypted virtual disk.
4. Add an undelete tool and a disk imaging/restore tool; test recovery results before expanding.
5. Evaluate the remaining browsers, Lazesoft/Acronis integrations or alternatives, and disc image/burning support.

Track each tool as requested, selected, integrated, and VM-verified separately. Commit working source changes and retain earlier bootable ISOs as baselines.
