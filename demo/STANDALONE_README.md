# Secure Contact Discovery Demo

This folder contains compiled Linux programs and editable demo inputs. No C++
compilation or original CS670 folder is required to run this copy. Docker Desktop
must be running, and the saved Docker image
`secure-contact-discovery-runtime:local` must remain installed on this computer.
The launcher starts a fresh temporary container using that image and this folder.
It does not depend on the original VS Code container or its storage volumes.

## Run from Windows PowerShell

Open this folder in File Explorer. Click the address bar, type `powershell`, and
press Enter. Then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Run-Demo.ps1
```

This runs the three walkthrough scenarios with both secure implementations and
pauses between scenarios. Press Enter to continue.

For the editable current inputs only:

```powershell
powershell -ExecutionPolicy Bypass -File .\Run-Demo.ps1 -CurrentOnly
```

For an unattended walkthrough:

```powershell
powershell -ExecutionPolicy Bypass -File .\Run-Demo.ps1 -NoPause
```

The execution-policy option applies only to the launched PowerShell process.

## Files to edit

- `demo/server.txt`: registered identifiers, one per line.
- `demo/client.txt`: client contacts, one per line.
- `demo/config.json`: demo title and the new contact for the walkthrough.

Use synthetic numbers in screenshots. The walkthrough contact must initially be
absent from both input files. Input changes do not require recompilation.

## Evidence and limitations

Read `demo/PRESENTATION_GUIDE.md` for what to explain and screenshot. Actual demo
outputs and the exact scenario inputs are saved under `demo/output/`. Previous
performance measurements, when included, are under `comparison/results/`.

The demonstration verifies functional results. It does not prove privacy. The
PIR-PSI privacy model assumes semi-honest parties and non-colluding servers. All
roles run in one container here. No TLS, malicious-security or production-scale
performance claim is made.

## Moving the folder

You can move this folder elsewhere on this same computer and use the launcher.
Moving it to another computer also requires compatible x86-64 Docker execution
and transfer of the runtime image; copying this folder alone is insufficient.
Keep the saved Docker image and avoid deleting it during Docker cleanup.
