# Pharma Neural Assistant - Version 2

## Objetivo

La Version 2 convierte el proyecto en una plataforma mas completa para operar inventario farmaceutico con IA, no solo en un asistente de consultas.

Esta etapa consolida las funciones ya creadas, actualiza la documentacion y deja una ruta clara para preparar el sistema para uso real con frontend, seguridad y despliegue.

## Capacidades incluidas

- Asistente conversacional para consultas de inventario.
- Clasificacion de intenciones con modelo PyTorch.
- Busqueda y analisis de medicamentos.
- Alertas de bajo stock, agotados y caducidad.
- Memoria conversacional.
- Acciones conversacionales con confirmacion.
- Movimientos de inventario.
- Dashboard de inventario.
- Dashboard predictivo.
- Prediccion de agotamiento.
- Recomendaciones automaticas.
- Planeador de compras.
- Reportes inteligentes.
- Deteccion de anomalias.
- Vision artificial para etiquetas.
- Asistente de voz.
- Agente autonomo.
- Aprendizaje por feedback del usuario.
- Pruebas automatizadas para los modulos principales.

## Mejoras prioritarias de la V2

1. Ordenar la documentacion para que coincida con las funciones reales.
2. Separar backups historicos del codigo activo.
3. Completar variables de entorno y guia de instalacion.
4. Preparar autenticacion y autorizacion para rutas sensibles.
5. Restringir CORS por ambiente.
6. Unificar rutas antiguas y rutas nuevas bajo una estructura consistente.
7. Cambiar mensajes `print` por `logging`.
8. Crear flujo formal para aplicar migraciones SQL.
9. Agregar Docker para desarrollo y despliegue.
10. Preparar integracion con frontend.

## Criterios para considerar estable la V2

- Las pruebas automatizadas pasan.
- El endpoint raiz reporta version `2.0.0`.
- La documentacion describe las capacidades actuales.
- `.env.example` contiene las variables necesarias para ejecutar el proyecto.
- El README apunta a esta hoja de ruta.

## Proxima fase sugerida

La siguiente fase deberia enfocarse en preparar el sistema para usuarios reales:

- Login y roles.
- Panel web.
- Exportacion de reportes.
- Auditoria de movimientos.
- Configuracion visual de stock minimo, compras y predicciones.
- Despliegue reproducible con Docker.
