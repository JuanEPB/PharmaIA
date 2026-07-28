# Login profesional para la app

Este mockup propone una pantalla de acceso mas solida para Pharma Neural.

Archivo visual:

```text
docs/mockups/login-pro.html
```

## Enfoque

- Pantalla dividida: lado izquierdo con identidad del producto y beneficios; lado derecho con formulario.
- Imagen real relacionada con farmacia para que no se vea como plantilla generica.
- Tarjeta compacta de login, sin elementos excesivamente redondeados.
- Mensaje de seguridad conectado con roles de la app.
- Responsive para escritorio y movil.

## Campos

- Correo o usuario.
- Contrasena.
- Recordar equipo.
- Recuperar acceso.
- Boton principal: `Entrar al sistema`.

## Conexion con backend

Cuando exista login real, la app debe enviar:

```http
X-API-Key: <api-key>
X-User-Id: <id-del-usuario>
X-User-Role: <rol>
```

Roles actuales:

- `admin`
- `supervisor`
- `encargado`
- `vendedor`

## Pendiente tecnico

El repo actual es backend. Este diseno queda como mockup listo para migrarse a
React, React Native, Vue o el frontend que se conecte a la API.
