$ErrorActionPreference = "Stop"
$BaseUrl = "http://127.0.0.1:8000"
$MedicineId = 1

function Register-Movement {
    param([string]$Type, [int]$Quantity, [string]$Reason)
    $Body = @{
        medicamento_id = $MedicineId
        tipo = $Type
        cantidad = $Quantity
        motivo = $Reason
        usuario_id = 1
    } | ConvertTo-Json

    Invoke-RestMethod `
        -Uri "$BaseUrl/inventario/movimientos" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($Body))
}

Write-Host "Registrando entrada..." -ForegroundColor Yellow
Register-Movement -Type "ENTRADA" -Quantity 5 -Reason "Compra a proveedor" | ConvertTo-Json -Depth 20

Write-Host "Registrando salida..." -ForegroundColor Yellow
Register-Movement -Type "SALIDA" -Quantity 2 -Reason "Venta en mostrador" | ConvertTo-Json -Depth 20

Write-Host "Consultando historial..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "$BaseUrl/inventario/movimientos/medicamento/$MedicineId" -Method Get | ConvertTo-Json -Depth 20
