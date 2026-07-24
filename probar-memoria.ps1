$BaseUrl = "http://127.0.0.1:8000"

Write-Host ""
Write-Host "Prueba 1: consultar medicamento" -ForegroundColor Cyan

$FirstBody = @{
    mensaje   = "Muéstrame el Paracetamol"
    sesion_id = "usuario-prueba-001"
} | ConvertTo-Json

$FirstResponse = Invoke-RestMethod `
    -Uri "$BaseUrl/conversation/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $FirstBody

$FirstResponse | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "Prueba 2: pregunta de seguimiento" -ForegroundColor Cyan

$SecondBody = @{
    mensaje   = "¿Cuánto stock tiene?"
    sesion_id = "usuario-prueba-001"
} | ConvertTo-Json

$SecondResponse = Invoke-RestMethod `
    -Uri "$BaseUrl/conversation/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $SecondBody

$SecondResponse | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "Prueba 3: consultar contexto" -ForegroundColor Cyan

Invoke-RestMethod `
    -Uri "$BaseUrl/conversation/usuario-prueba-001/context" `
    -Method Get |
    ConvertTo-Json -Depth 10
