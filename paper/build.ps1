# Compile main.tex with MiKTeX into build/. Sources are staged there (style files live in
# acl-style-files/, so they are copied in alongside) which keeps the paper root clean.
$ErrorActionPreference = "Continue"
$bin = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64"
$env:PATH = "$bin;$env:PATH"
$here = $PSScriptRoot
$build = Join-Path $here "build"

# leave build/ before deleting it: this script ends by cd'ing into it, and PowerShell keeps the
# working directory across invocations, which otherwise locks the folder against removal
Set-Location $here
if (Test-Path $build) { Remove-Item $build -Recurse -Force }
New-Item -ItemType Directory $build | Out-Null
foreach ($f in @("main.tex", "tables.tex", "custom.bib")) {
  Copy-Item (Join-Path $here $f) $build -Force
}
foreach ($f in @("acl.sty", "acl_natbib.bst")) {
  Copy-Item (Join-Path $here "acl-style-files\$f") $build -Force
}
Copy-Item (Join-Path $here "figures") $build -Recurse -Force

Set-Location $build
$flags = @("-interaction=nonstopmode", "main.tex")
& pdflatex @flags | Out-Null
& bibtex main | Out-Null
& pdflatex @flags | Out-Null
& pdflatex @flags | Out-Null

Write-Output "==== BIBTEX ===="
if (Test-Path "main.blg") {
  $b = Select-String -Path "main.blg" -Pattern "error|warning|I couldn't|I found no"
  if ($b) { $b | Select-Object -First 15 -ExpandProperty Line } else { Write-Output "clean" }
}
Write-Output "==== LATEX ERRORS ===="
$e = Select-String -Path "main.log" -Pattern '^!|Citation .* undefined|Reference .* undefined|LaTeX Warning: There were'
if ($e) { $e | Select-Object -First 25 -ExpandProperty Line } else { Write-Output "none" }
Write-Output "==== OVERFULL (>10pt) ===="
$o = Select-String -Path "main.log" -Pattern 'Overfull \\hbox \((\d+)'
if ($o) { $o | Select-Object -First 12 -ExpandProperty Line } else { Write-Output "none" }
Write-Output "==== OUTPUT ===="
Select-String -Path "main.log" -Pattern 'Output written on' | Select-Object -ExpandProperty Line
Set-Location $here
