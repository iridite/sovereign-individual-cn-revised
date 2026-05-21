$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path $scriptDir).Path

python (Join-Path $repoRoot "build_epub.py")
