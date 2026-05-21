$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\\..")).Path

python (Join-Path $repoRoot "tools\\build_epub.py")
