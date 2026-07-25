$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8000"
$SessionId = "prueba-acciones-001"

function Send-Chat {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $Body = @{
        mensaje   = $Message
        sesion_id = $SessionId
        usuario_id = 1
    } | ConvertTo-Json

    Invoke-RestMethod `
        -Uri "$BaseUrl/chat" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($Body))
}

Write-Host ""
Write-Host "1. Preparando entrada..." -ForegroundColor Yellow

$Preview = Send-Chat `
    -Message "Agrega 20 cajas de Paracetamol"

$Preview | ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "2. Confirmando entrada..." -ForegroundColor Yellow

$Confirmation = Send-Chat `
    -Message "confirmar"

$Confirmation | ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "3. Preparando orden de compra..." -ForegroundColor Yellow

$OrderPreview = Send-Chat `
    -Message "Genera una orden de compra para los medicamentos críticos"

$OrderPreview | ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "Para no crear órdenes durante la prueba automática," -ForegroundColor Cyan
Write-Host "la segunda acción se cancelará." -ForegroundColor Cyan

$Cancellation = Send-Chat `
    -Message "cancelar"

$Cancellation | ConvertTo-Json -Depth 20
