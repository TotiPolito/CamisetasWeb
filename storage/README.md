Esta carpeta guarda datos persistentes de la app.

- `catalog.sqlite3`: base SQLite generada por la aplicacion.
- `media/`: fotos y videos originales servidos por el backend.

En desarrollo local ya podes dejar tus archivos dentro de `storage/media/`.
Para un deploy publico, conviene que el repo no incluya esos originales.

Si usas Render con el `render.yaml` de este proyecto:

- monta un disco persistente en `storage/`
- luego subi tus fotos y videos a `storage/media/`
- la app mostrara solo los archivos que realmente existan
