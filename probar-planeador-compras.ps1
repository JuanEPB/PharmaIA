$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8000"
$SessionId = "planeador-compras-001"

function Send-Chat {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $Body = @{
        mensaje    = $Message
        sesion_id  = $SessionId
        usuario_id = 1
    } | ConvertTo-Json

    Invoke-RestMethod `
        -Uri "$BaseUrl/chat" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($Body))
}

Write-Host ""
Write-Host "1. Solicitando análisis automático..." -ForegroundColor Yellow

$Plan = Send-Chat `
    -Message "Analiza el inventario"

$Plan | ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "2. Cancelando para evitar generar órdenes de prueba..." -ForegroundColor Yellow

$Cancellation = Send-Chat `
    -Message "cancelar"

$Cancellation | ConvertTo-Json -Depth 20
