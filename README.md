# Catalogo de Camisetas MVC

Aplicacion web con backend Flask, base de datos SQLite y estructura MVC para:

- mostrar el catalogo al publico sin login
- servir fotos y videos desde backend
- evitar enlaces directos visibles al contenido
- iniciar sesion como admin
- editar stock facilmente desde un panel privado

## Estructura

- `run.py`: punto de arranque local
- `config.py`: configuracion principal
- `requirements.txt`: dependencias Python
- `abrir-web.bat`: inicia la web local con doble clic
- `render.yaml`: configuracion recomendada para publicar en Render
- `data/products.json`: seed inicial de camisetas, stock y media
- `storage/catalog.sqlite3`: base de datos local generada al iniciar
- `storage/media/`: fotos y videos originales fuera del repo publico
- `app/controllers/`: rutas y controladores
- `app/models/`: acceso a datos SQLite
- `app/services/`: autenticacion, seed y media
- `app/templates/`: vistas Jinja
- `app/static/`: CSS y JS del frontend

## Arquitectura

Se siguio una separacion tipo MVC:

- Model: `app/models`
- View: `app/templates`
- Controller: `app/controllers`

Los servicios compartidos quedaron en `app/services` para no mezclar logica de negocio con rutas o vistas.

## Como abrirla facil

La forma mas simple es hacer doble clic en:

```text
abrir-web.bat
```

Ese archivo:

- crea el entorno virtual si hace falta
- instala dependencias
- levanta el servidor local
- abre el navegador en `http://127.0.0.1:5000`

Mientras esa ventana siga abierta, la web sigue funcionando.

## Como iniciar manualmente

1. Crear entorno virtual si no existe:

```powershell
C:\Users\Administrador\Desktop\Webs\Web Camisetas\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Levantar el servidor:

```powershell
C:\Users\Administrador\Desktop\Webs\Web Camisetas\.venv\Scripts\python.exe run.py
```

3. Abrir en el navegador:

```text
http://127.0.0.1:5000
```

## Login admin por defecto

- Usuario: `admin`
- Contrasena: `admin12345`

Antes de publicar, conviene cambiar esas credenciales usando variables de entorno:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

## Repo publico y seguridad

No hace falta poner el repo privado para que la web no "se hackee". Lo importante es:

- no subir secretos reales al repo
- cambiar las credenciales admin antes de publicar
- usar variables de entorno para claves
- no versionar fotos y videos originales si queres proteger el contenido

Por eso este proyecto ya deja `storage/media/` fuera de Git. Tus archivos se usan localmente, pero no conviene publicarlos dentro del repo.

## Importante sobre la proteccion del contenido

Se aplicaron medidas de proteccion razonables para web publica:

- no hay enlaces directos a archivos en la interfaz
- los media se sirven por backend mediante tokens
- se ocultan botones de descarga en los videos
- se bloquean acciones rapidas como click derecho y drag sobre media

Aun asi, ningun sitio web puede impedir al 100% que alguien capture lo que ve en pantalla o inspeccione trafico si tiene conocimientos tecnicos. Esta implementacion reduce la exposicion casual, que es lo realista en web.

## Despliegue recomendado

Esta version no es apta para Netlify estatico porque ahora usa:

- login
- sesiones
- SQLite persistente
- actualizacion de stock en servidor

La opcion mas simple para este proyecto es Render:

- soporta apps Flask
- se conecta directo con GitHub
- te da dominio `onrender.com`
- acepta dominio propio
- permite disco persistente para `SQLite` y `media`

Pasos recomendados:

1. Subir el repo a GitHub.
2. Crear un servicio web en Render desde ese repo.
3. Usar el `render.yaml` incluido.
4. Cargar `ADMIN_USERNAME` y `ADMIN_PASSWORD`.
5. Subir tus fotos y videos al disco persistente dentro de `storage/media/`.

Si queres mantener el repo publico, esta es la forma correcta: codigo publico, secretos privados y archivos multimedia fuera del repositorio.
