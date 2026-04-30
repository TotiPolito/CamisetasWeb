# Toti Camisetas

Catalogo web de camisetas con backend Flask, panel admin para gestion de stock y flujo de pedido por WhatsApp.

## Caracteristicas

- catalogo publico sin registro para clientes
- detalle por producto con fotos, videos y stock por talle
- carrito local con envio del pedido por WhatsApp
- panel admin para actualizar stock
- estructura MVC con SQLite
- modo claro y modo oscuro

## Estructura

- `app/controllers/`: rutas y controladores
- `app/models/`: acceso a datos
- `app/services/`: logica compartida
- `app/templates/`: vistas
- `app/static/`: estilos, scripts e imagenes
- `data/products.json`: catalogo inicial
- `storage/`: base local y archivos persistentes

## Inicio rapido

La forma mas simple de abrirlo en Windows es:

```text
abrir-web.bat
```

## Inicio manual

1. Crear entorno virtual:

```powershell
python -m venv .venv
```

2. Instalar dependencias:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Levantar la app:

```powershell
.venv\Scripts\python.exe run.py
```

4. Abrir en el navegador:

```text
http://127.0.0.1:5000
```

## Variables de entorno

Para configurar el acceso admin y la app, definir:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

## Despliegue

El proyecto incluye `render.yaml` para facilitar el deploy en Render.

Recomendaciones generales:

- usar variables de entorno para configuracion sensible
- mantener fuera del repositorio los archivos multimedia originales
- utilizar almacenamiento persistente para la base y el contenido
