$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8000"
$MedicineId = 1
$MedicineName = "Paracetamol"
$SessionId = "prediccion-001"

Write-Host ""
Write-Host "1. Predicción por ID..." -ForegroundColor Yellow

$ById = Invoke-RestMethod `
    -Uri "$BaseUrl/predicciones/agotamiento/medicamento/$MedicineId" `
    -Method Get

$ById | ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "2. Predicción por nombre..." -ForegroundColor Yellow

$EncodedName = [uri]::EscapeDataString($MedicineName)

$ByName = Invoke-RestMethod `
    -Uri "$BaseUrl/predicciones/agotamiento/buscar?nombre=$EncodedName" `
    -Method Get

$ByName | ConvertTo-Json -Depth 20

Write-Host ""
Write-Host "3. Consulta mediante el chat..." -ForegroundColor Yellow

$Body = @{
    mensaje    = "¿Cuándo se agotará $MedicineName?"
    sesion_id  = $SessionId
    usuario_id = 1
} | ConvertTo-Json

$Chat = Invoke-RestMethod `
    -Uri "$BaseUrl/chat" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($Body))

$Chat | ConvertTo-Json -Depth 20
