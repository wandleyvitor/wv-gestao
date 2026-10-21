$processFile = Join-Path $PSScriptRoot '.runtime\processos.json'
if (!(Test-Path -LiteralPath $processFile)) { Write-Host 'Nenhum registro de execução encontrado.'; return }
$records = Get-Content -Encoding utf8 -LiteralPath $processFile -Raw | ConvertFrom-Json
foreach ($record in $records) {
    $ownedProcess = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    # O ID pode ter sido reutilizado pelo Windows. Confira também o início.
    if ($ownedProcess -and $ownedProcess.StartTime.ToUniversalTime().ToString('o') -eq $record.start) {
        Stop-Process -Id $ownedProcess.Id
    }
}
Write-Host 'Serviços desta execução encerrados.'
