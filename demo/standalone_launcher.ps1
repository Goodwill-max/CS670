param(
    [switch]$NoPause,
    [switch]$CurrentOnly
)
$ErrorActionPreference = 'Stop'
$demoRoot = $PSScriptRoot
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCommand) {
    $dockerExecutable = $dockerCommand.Source
} else {
    $dockerCandidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'),
        (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe')
    )
    $dockerExecutable = $dockerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $dockerExecutable) { throw 'Docker Desktop was not found. Install it and keep it running.' }
$imageName = 'secure-contact-discovery-runtime:local'
& $dockerExecutable image inspect $imageName *> $null
if ($LASTEXITCODE -ne 0) { throw 'The saved Docker runtime image is missing. Keep the secure-contact-discovery-runtime:local image installed on this computer.' }
$dockerArguments = @('run', '--rm')
if (-not $NoPause) { $dockerArguments += @('-it') }
$dockerArguments += @('--mount', "type=bind,source=$demoRoot,target=/app", '--workdir', '/app', '--entrypoint', 'python3', $imageName, 'demo/present_demo.py', '--compare')
if (-not $CurrentOnly) { $dockerArguments += '--walkthrough' }
if ((-not $NoPause) -and (-not $CurrentOnly)) { $dockerArguments += '--pause' }
& $dockerExecutable @dockerArguments
exit $LASTEXITCODE
