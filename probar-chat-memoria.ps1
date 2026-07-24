$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8000"
$SessionId = "usuario-prueba-001"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " PRUEBAS DE MEMORIA CONVERSACIONAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

function Send-ChatMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $Body = @{
        mensaje   = $Message
        sesion_id = $SessionId
    } | ConvertTo-Json

    $Response = Invoke-RestMethod `
        -Uri "$BaseUrl/chat" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($Body))

    return $Response
}

Write-Host "1. Consultando Paracetamol..." -ForegroundColor Yellow

$FirstResponse = Send-ChatMessage `
    -Message "Muéstrame el Paracetamol"

$FirstResponse |
    ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "2. Consultando stock con contexto..." -ForegroundColor Yellow

$SecondResponse = Send-ChatMessage `
    -Message "¿Cuánto stock tiene?"

$SecondResponse |
    ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "3. Consultando caducidad con contexto..." -ForegroundColor Yellow

$ThirdResponse = Send-ChatMessage `
    -Message "¿Cuándo caduca?"

$ThirdResponse |
    ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "4. Consultando proveedor con contexto..." -ForegroundColor Yellow

$FourthResponse = Send-ChatMessage `
    -Message "¿Quién lo provee?"

$FourthResponse |
    ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "5. Consultando memoria almacenada..." -ForegroundColor Yellow

$ContextResponse = Invoke-RestMethod `
    -Uri "$BaseUrl/chat/context/$SessionId" `
    -Method Get

$ContextResponse |
    ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "Pruebas terminadas." -ForegroundColor Green
