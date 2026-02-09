$ErrorActionPreference = "Stop"

# Configuración
$SourceDir = Get-Location
$BackupRootDir = Join-Path $SourceDir "_backups"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$DestinationDir = Join-Path $BackupRootDir "backup_$Timestamp"

# Exclusiones (patrones de archivo/carpeta a ignorar)
$Excludes = @(".git", ".venv", "venv", "__pycache__", "*.pyc", ".idea", ".vscode", "_backups", "*.sqlite3")

# Crear directorio de destino
if (-not (Test-Path -Path $DestinationDir)) {
    New-Item -ItemType Directory -Path $DestinationDir | Out-Null
    Write-Host "Directorio creado: $DestinationDir" -ForegroundColor Cyan
}

# Copiar archivos excluyendo los patrones definidos
Get-ChildItem -Path $SourceDir -Exclude $Excludes | ForEach-Object {
    $itemPath = $_.FullName
    $itemName = $_.Name
    
    # Verificar si el elemento está en la lista de exclusiones (para carpetas)
    if ($itemName -in $Excludes) {
        return
    }

    Copy-Item -Path $itemPath -Destination $DestinationDir -Recurse -Force
}

Write-Host "✅ Backup (Copia Directa) completado en: $DestinationDir" -ForegroundColor Green
Write-Host "Nota: Se han excluido carpetas de sistema y temporales." -ForegroundColor Gray
