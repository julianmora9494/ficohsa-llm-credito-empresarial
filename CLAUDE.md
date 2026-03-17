# ficohsa-llm-credito-empresarial

## Propósito del Sistema

Asistente LLM para **análisis de crédito empresarial** en Banco Ficohsa.
Combina información financiera interna de empresas con contexto externo del sector
económico para apoyar la toma de decisiones crediticias.

El sistema analiza:
- Estados financieros de la empresa solicitante
- Informes de gestión sectoriales (Honduras, Guatemala, Nicaragua)
- Señales de riesgo y capacidad de pago
- Contexto macroeconómico y sectorial

Salida esperada:
- Dictamen crediticio: **aprobar / aprobar con condiciones / rechazar**
- Justificación razonada y trazable con fuentes
- Señales de riesgo identificadas
- Indicadores financieros calculados

---

## Contexto del Negocio

**Cliente interno**: Área de Riesgo Crediticio y Banca Empresarial de Ficohsa.
**Perfil de empresa analizada**: Empresas medianas y grandes en Centroamérica.
**Documentos base**: Informes de gestión de Honduras, Guatemala y Nicaragua.
**Decisión de crédito**: Apoyar (no reemplazar) al oficial de crédito.

### Categorías de empresas que se analizan
- Sector agrícola (café, palma, granos básicos)
- Sector comercio (retail, distribución)
- Sector industria (manufactura, procesamiento)
- Sector servicios (transporte, logística, profesionales)
- Sector construcción e inmobiliario

### Señales clave de riesgo crediticio
- Ratio de liquidez corriente < 1.0
- Endeudamiento > 70% sobre activos totales
- Flujo de caja operativo negativo
- Sector con contracción en informes de gestión
- Concentración de ingresos en un solo cliente
- Mora histórica con el sistema financiero

---

## Arquitectura del Sistema

```
Estados Financieros + Informes de Gestión
        ↓
┌───────────────────────────────────────────┐
│           CAPA DE INGESTIÓN               │
│  document_loader → parser → chunker       │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│         CAPA DE EMBEDDINGS                │
│  Azure OpenAI text-embedding-3-small      │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│          VECTORSTORE (FAISS)              │
│  Índices separados: documentos + sector   │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│         CAPA DE RETRIEVAL                 │
│  retriever (híbrido) → reranker (LLM)    │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│         ANÁLISIS DE CRÉDITO               │
│  financial_analyzer → sector_analyzer    │
│  risk_scorer → decision_engine           │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│         CAPA DE GENERACIÓN                │
│  Azure OpenAI GPT-4o con grounding       │
│  Dictamen: aprobar / condiciones / negar │
└───────────────────────────────────────────┘
```

### Módulos src/
| Módulo | Responsabilidad |
|---|---|
| `ingestion/` | Carga, parseo y chunking de documentos |
| `embeddings/` | Vectorización via Azure OpenAI |
| `vectorstore/` | FAISS índices y búsqueda por similitud |
| `retrieval/` | Recuperación híbrida + reranking |
| `credit/` | Análisis financiero, sectorial, scoring y decisión |
| `llm/` | Cliente Azure OpenAI GPT-4o |
| `pipeline/` | Orquestador del flujo RAG completo |
| `services/` | Capa de servicio de alto nivel |
| `utils/` | Logger, helpers, validadores |
| `config/` | Settings Pydantic + Prompts del sistema |

---

## Lineamientos Técnicos

### Stack tecnológico
- **LLM**: Azure OpenAI GPT-4o (deployment configurable)
- **Embeddings**: Azure OpenAI text-embedding-3-small (1536 dim)
- **Vector Store**: FAISS (faiss-cpu)
- **Framework**: LangChain para orquestación
- **Config**: Pydantic BaseSettings con validación
- **Logging**: Python logging con rotación de archivos
- **Evaluación**: RAGAS (faithfulness, answer_relevancy, context_precision)

### Formatos de documentos soportados
- PDF (informes de gestión, estados financieros en PDF)
- PPTX (presentaciones de gestión)
- DOCX (reportes Word)
- XLSX (estados financieros en Excel)
- TXT / Markdown

### Separación de índices FAISS
- `sector_index`: Chunks de informes de gestión (contexto sectorial)
- `financial_index`: Chunks de estados financieros de empresas
- Permite búsqueda diferenciada por tipo de fuente

---

## Reglas de Estilo de Código

1. **Código en inglés**. Comentarios y docstrings en español.
2. **Type hints** en todas las funciones y clases.
3. **Dataclasses o Pydantic** para estructuras de datos.
4. **Docstrings** con propósito, parámetros y retorno.
5. **Un módulo = una responsabilidad** (Single Responsibility).
6. **Logging** en todos los módulos usando `src/utils/logger.py`.
7. **No hardcodear** endpoints, claves o rutas — todo via Settings.
8. **Manejo de errores** explícito con mensajes descriptivos.

---

## Restricciones Importantes

1. **Ningún dato real de clientes** en repositorios ni notebooks.
2. **Usar siempre Azure OpenAI** — nunca OpenAI directo ni AWS Bedrock.
3. **Control de alucinaciones obligatorio**: el asistente solo debe concluir
   basándose en evidencia recuperada. Si no hay datos suficientes, debe
   indicar "información insuficiente para concluir".
4. **Trazabilidad de fuentes**: toda afirmación del dictamen debe citar
   la fuente y sección del documento.
5. **El sistema apoya, no reemplaza**: el dictamen es una recomendación,
   no una decisión autónoma final. Siempre dejar claro esto.
6. **No commitear `.env`** con valores reales. Solo `.env.example`.
7. **No commitar datos financieros reales** de empresas en ningún archivo.
8. **Métricas de evaluación obligatorias** en todo modelo y pipeline:
   KS, AUC, precisión, recall, RAGAS metrics.

---

## Supuestos Iniciales

- Los informes de gestión son en español y formato PDF/PPTX.
- Los estados financieros siguen el formato estándar de contabilidad
  centroamericana (balance general, estado de resultados, flujo de caja).
- El usuario final es un oficial de crédito o analista de riesgo,
  no un cliente externo.
- Inicialmente, el análisis sectorial se basa en los informes de gestión
  disponibles. En el futuro se puede conectar a fuentes externas (BCH, etc.).
- Las simulaciones de ejemplo usan datos ficticios/anonimizados.
- El sistema no accede a bases de datos del banco directamente en esta fase.

---

## Variables de Entorno Requeridas

Ver `.env.example` para la lista completa.
Variables críticas:
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME` (GPT-4o)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (text-embedding-3-small)
- `AZURE_OPENAI_API_VERSION`
