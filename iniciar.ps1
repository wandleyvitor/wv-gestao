$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonExe = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodeExe = if ($nodeCommand) { $nodeCommand.Source } else { Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' }
if (!(Test-Path -LiteralPath $pythonExe) -or !(Test-Path -LiteralPath $nodeExe)) { throw 'Prepare o ambiente Python e instale Node.js conforme o README.' }
foreach ($port in @(8000,5173)) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listener) { throw "A porta $port já está em uso. Confira se a aplicação já está aberta." }
}
$env:Path = (Split-Path $nodeExe) + ';' + $env:Path
$runtime = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'backend.log') -RedirectStandardError (Join-Path $runtime 'backend-error.log')
$frontendProcess = Start-Process -FilePath $nodeExe -ArgumentList @('node_modules/vite/bin/vite.js','--configLoader','runner','--host','127.0.0.1','--port','5173','--strictPort') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'frontend.log') -RedirectStandardError (Join-Path $runtime 'frontend-error.log')
@(@{id=$backendProcess.Id;start=$backendProcess.StartTime.ToUniversalTime().ToString('o')},@{id=$frontendProcess.Id;start=$frontendProcess.StartTime.ToUniversalTime().ToString('o')}) | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath (Join-Path $runtime 'processos.json')
Write-Host 'WV Gestão: http://127.0.0.1:5173'
Write-Host 'API: http://127.0.0.1:8000/docs'
Write-Host 'Dados fictícios só são carregados pelo comando explícito do README. Para encerrar: ./parar.ps1'
