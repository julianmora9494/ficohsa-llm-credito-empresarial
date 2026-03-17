---
description: Indexa los documentos descargados en los índices FAISS del sistema
---

Ejecuta la ingestión e indexación de documentos en FicoCrédito AI.

```bash
python scripts/ingest_documents.py --tipo $ARGUMENTS
```

Si $ARGUMENTS está vacío, usa `sector`.

Opciones válidas: `sector`, `financiero`, `todos`

Después muéstrame cuántos chunks quedaron indexados y el contenido de `data/vectorstore/faiss_index/`.
