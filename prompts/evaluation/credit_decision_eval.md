# Dataset de Evaluación — Análisis Crediticio

## Propósito
Casos de prueba para evaluar la calidad del sistema RAG con RAGAS.
Todos los casos usan datos **ficticios** — ninguno refleja empresas reales.

---

## Métricas RAGAS a evaluar

| Métrica | Descripción |
|---|---|
| `faithfulness` | Las afirmaciones del dictamen están respaldadas por el contexto recuperado |
| `answer_relevancy` | La respuesta es relevante para la pregunta/caso planteado |
| `context_precision` | Los chunks recuperados son pertinentes para el análisis |
| `context_recall` | Se recuperó suficiente contexto para responder correctamente |

---

## Casos de Prueba

### Caso 1 — Empresa Agrícola (Honduras)
**Input**: Empresa agrícola con liquidez 0.85, endeudamiento 75%, sector café Honduras.
**Pregunta**: ¿Se recomienda aprobar el crédito?
**Respuesta esperada**: APROBAR CON CONDICIONES (liquidez baja, endeudamiento elevado).
**Grounding requerido**: Informe de gestión Honduras, sección sector agrícola.

---

### Caso 2 — Empresa Comercial (Guatemala)
**Input**: Empresa comercio retail con liquidez 2.1, endeudamiento 45%, buena rentabilidad.
**Pregunta**: Evaluar viabilidad crediticia.
**Respuesta esperada**: APROBAR (indicadores sólidos).
**Grounding requerido**: Informe de gestión Guatemala, sección comercio/retail.

---

### Caso 3 — Empresa Industrial con Flujo Negativo
**Input**: Empresa manufactura con flujo operativo negativo dos años consecutivos.
**Pregunta**: ¿Qué señales de riesgo se identifican?
**Respuesta esperada**: Mencionar flujo negativo, posible descapitalización.
**Grounding requerido**: Estados financieros empresa + contexto sector industrial.

---

### Caso 4 — Consulta Sectorial
**Pregunta**: ¿Cómo está el sector agrícola en Honduras según los informes de gestión?
**Respuesta esperada**: Resumen de situación del sector basado en informe HN.
**Grounding requerido**: Informe de gestión Honduras, sección agrícola.

---

## Notas de evaluación

- Un dictamen es correcto si:
  1. La decisión es la esperada
  2. Cada afirmación cita una fuente del contexto
  3. No incluye cifras no presentes en los documentos
- Evaluar en RAGAS con dataset JSON en `data/evaluation/ragas_dataset.json`
