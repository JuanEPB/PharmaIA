# Revision de base de datos - Version 2

Archivo revisado: `pharmacontrol (9).sql`

Fecha del dump: 2026-07-27

## Resumen

La base de datos ya contiene una estructura util para inventario farmaceutico, ventas, pedidos, usuarios, empresa, farmacia, planes y suscripciones.

Para la Version 2 conviene mejorar integridad, limpieza de datos, consistencia de nombres y soporte para las funciones nuevas de IA del backend.

## Hallazgos principales

### 1. Datos de prueba mezclados con datos reales

En `medicamentos` hay registros como `MedicamentoPrueba`, valores vacios y fechas `0000-00-00`.

Tambien en `usuarios` existe un registro con nombre, apellido, email y contrasena vacios.

Riesgo:

- Puede afectar busquedas del asistente.
- Puede alterar reportes, predicciones y recomendaciones.
- Puede romper consultas si MySQL/MariaDB se configura con modo estricto.

Mejora recomendada:

- Crear un script de limpieza.
- Separar datos demo de datos reales.
- Agregar validaciones para impedir nombres vacios, lotes vacios y fechas invalidas.

### 2. Duplicidad de tablas de importacion

Existen dos tablas similares:

- `historial_importacion`
- `historial_importaciones`

Riesgo:

- El sistema puede guardar historial en una tabla y consultar otra.
- Aumenta la confusion en reportes y auditoria.

Mejora recomendada:

- Elegir una tabla oficial.
- Migrar datos si existen.
- Eliminar o dejar obsoleta la tabla duplicada.

### 3. Nombres de columnas inconsistentes

Hay mezcla de estilos:

- `usuarioId`
- `medicamentoId`
- `proveedorId`
- `categoriaId`
- `usuario_id`
- `medicamento_id`
- `farmacia_id`

Riesgo:

- Mas errores en queries y repositorios.
- Dificulta mantener el backend.

Mejora recomendada:

- Usar un solo estilo para V2, preferentemente `snake_case`.
- Mantener compatibilidad temporal si el frontend actual usa camelCase.

### 4. Falta relacion directa de medicamentos con farmacia

`medicamentos` no tiene `farmacia_id` ni `empresa_id`.

Riesgo:

- Si hay varias farmacias, todas compartirian el mismo inventario.
- Los reportes por farmacia pueden quedar incorrectos.

Mejora recomendada:

- Agregar `farmacia_id` a `medicamentos`.
- Crear indice por `farmacia_id`.
- Ajustar consultas del backend para filtrar por farmacia.

### 5. Precio como `float`

En `medicamentos.precio` se usa `float`.

Riesgo:

- Los valores monetarios pueden tener errores de redondeo.

Mejora recomendada:

- Cambiar a `decimal(10,2)` o `decimal(12,2)`.

### 6. Campos de contacto combinados

En `proveedores.contacto` se guarda telefono y email juntos.

Riesgo:

- Es dificil buscar, validar o mostrar datos limpios.

Mejora recomendada:

- Separar en `telefono`, `email` y opcionalmente `contacto_nombre`.

### 7. Fechas y caracteres con problemas de codificacion

Se observan textos como `San JosÃ©`, `MÃ©xico`, `BÃ¡sico`.

Riesgo:

- Mala experiencia visual.
- Busquedas del asistente menos precisas.

Mejora recomendada:

- Reexportar/importar usando UTF-8 real.
- Corregir datos existentes.

### 8. Falta soporte persistente para IA V2

El backend V2 tiene funciones como feedback, prediccion, acciones conversacionales y planeador de compras.

La base revisada todavia no incluye claramente tablas para:

- Movimientos de inventario normalizados.
- Configuracion de compras.
- Ordenes de compra generadas por IA.
- Configuracion de prediccion de agotamiento.
- Eventos de aprendizaje/feedback.
- Memoria conversacional persistente.

Mejora recomendada:

- Aplicar y consolidar las migraciones del proyecto en `migrations/`.
- Verificar que el dump final incluya esas tablas V2.

## Indices recomendados

Agregar indices para consultas frecuentes:

- `medicamentos(nombre)`
- `medicamentos(lote)`
- `medicamentos(caducidad)`
- `medicamentos(stock)`
- `medicamentos(categoriaId)`
- `medicamentos(proveedorId)`
- `venta(fecha)`
- `venta(usuarioId)`
- `venta(farmacia_id)`
- `venta_detalle(medicamentoId)`
- `pedidos(estatus)`
- `pedidos(fecha_pedido)`

Si se agrega `farmacia_id` a medicamentos:

- `medicamentos(farmacia_id)`
- `medicamentos(farmacia_id, nombre)`
- `medicamentos(farmacia_id, caducidad)`

## Restricciones recomendadas

Agregar reglas para evitar datos invalidos:

- `stock >= 0`
- `precio >= 0`
- `cantidad > 0`
- `total >= 0`
- `nombre <> ''`
- `lote <> ''`
- emails no vacios para usuarios reales

## Prioridad sugerida

1. Limpiar datos invalidos y demo.
2. Unificar tablas duplicadas de importacion.
3. Agregar `farmacia_id` a medicamentos.
4. Cambiar `precio` de `float` a `decimal`.
5. Separar contacto de proveedores.
6. Aplicar migraciones V2 faltantes.
7. Agregar indices de busqueda y reportes.
8. Preparar una migracion SQL formal para estos cambios.

## Migraciones agregadas

- `005_harden_inventory_schema.sql`: agrega `stock_minimo`, `farmacia_id`, precio decimal e indices para inventario, ventas y pedidos.
- `006_create_ai_operational_tables.sql`: agrega tablas persistentes para memoria conversacional, acciones IA, feedback de aprendizaje y predicciones.
- `007_clean_seed_data_quality.sql`: corrige datos vacios o invalidos que afectan a la app y a la IA.

Para aplicarlas:

```powershell
.\aplicar-migraciones.ps1
```
