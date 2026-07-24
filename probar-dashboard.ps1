$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8000"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " PRUEBAS DEL DASHBOARD DE INVENTARIO" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

function Show-ApiResult {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,

        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    Write-Host $Title -ForegroundColor Yellow

    $Response = Invoke-RestMethod `
        -Uri $Url `
        -Method Get

    $Response |
        ConvertTo-Json -Depth 20

    Write-Host ""
}

Show-ApiResult `
    -Title "1. Resumen general" `
    -Url "$BaseUrl/inventario/resumen"

Show-ApiResult `
    -Title "2. Alertas inteligentes" `
    -Url "$BaseUrl/inventario/alertas?limite=20"

Show-ApiResult `
    -Title "3. Estadísticas por categoría" `
    -Url "$BaseUrl/inventario/estadisticas/categorias"

Show-ApiResult `
    -Title "4. Estadísticas por proveedor" `
    -Url "$BaseUrl/inventario/estadisticas/proveedores"

Show-ApiResult `
    -Title "5. Ranking de stock" `
    -Url "$BaseUrl/inventario/ranking-stock?limite=5"

Write-Host "Pruebas finalizadas." -ForegroundColor Green
