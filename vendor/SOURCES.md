# Desktop prototype dependencies

WinXShell x64 and companion files were downloaded from the creator's WimBuilder2 repository:
https://github.com/slorelee/wimbuilder2/tree/45b9fa4b257ff67658f9365b8a4c95bbaf4e0673/vendor/WinXShell

The shell source project is https://github.com/slorelee/PExplorer (WinXShell_shellpart branch, LGPL-2.1). This does not establish licensing for every bundled WinXShell component. This prototype is for local testing; distribution requires reviewing the bundled components' terms.

Explorer++ 1.4.0 x64 was downloaded from its author's release:
https://github.com/derceg/explorerplusplus/releases/tag/version-1.4.0
Its included License.txt is retained alongside the executable.

manifest.json records local SHA-256 checksums to detect changes before building. These are integrity records, not independent publisher authenticity attestations.

Downloaded executables have not been run on the host. Runtime validation is performed in the disposable VMware recovery test VM.
