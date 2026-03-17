---
description: Descarga fuentes de datos públicas centroamericanas (BCH, SIB, SECMCA) para el RAG
---

Ejecuta el script de descarga automática de fuentes de datos para FicoCrédito AI.

Corre el siguiente comando y muéstrame el resultado:

```bash
python scripts/download_sources.py --fuente $ARGUMENTS
```

Si $ARGUMENTS está vacío, usa `todas`.

Después de la descarga, muéstrame cuántos archivos quedaron en cada carpeta de `data/raw/informes_gestion/`.
