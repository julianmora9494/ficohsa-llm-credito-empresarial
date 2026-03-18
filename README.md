# FicoCrédito AI — Asistente LLM de Crédito Empresarial

Asistente de inteligencia artificial para apoyar el análisis de crédito empresarial en **Banco Ficohsa**. Combina información financiera interna de empresas con contexto externo del sector económico centroamericano para generar dictámenes crediticios razonados y trazables.

> **Nota**: El sistema apoya al oficial de crédito, no reemplaza su criterio. El dictamen es una recomendación, no una decisión autónoma.

---

## Tabla de contenidos

- [Objetivo](#objetivo)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Estructura de carpetas](#estructura-de-carpetas)
- [Fuentes de datos](#fuentes-de-datos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Cómo ejecutar el sistema](#cómo-ejecutar-el-sistema)
- [Tecnologías utilizadas](#tecnologías-utilizadas)
- [Restricciones importantes](#restricciones-importantes)

---

## Objetivo

Dado un expediente de empresa solicitante (estados financieros + sector de actividad), el sistema:

1. Analiza los indicadores financieros clave (liquidez, endeudamiento, flujo de caja)
2. Recupera contexto sectorial relevante desde informes oficiales centroamericanos
3. Genera un **dictamen crediticio** con tres posibles resultados:
   - `APROBAR` — la empresa muestra capacidad de pago sólida
   - `APROBAR CON CONDICIONES` — viable con garantías adicionales o ajustes
   - `RECHAZAR` — señales de riesgo que no justifican el crédito

Cada dictamen incluye justificación razonada con citas exactas de las fuentes consultadas.

---

## Arquitectura del sistema

```
Estados Financieros (Excel/PDF)    Informes de Gestión (PDF)
           │                                │
           ▼                                ▼
   ┌───────────────────────────────────────────────┐
   │              CAPA DE INGESTIÓN                │
   │    document_loader → parser → chunker         │
   └───────────────────────────────────────────────┘
                         │
                         ▼
   ┌───────────────────────────────────────────────┐
   │            CAPA DE EMBEDDINGS                 │
   │    Azure OpenAI text-embedding-3-large        │
   └───────────────────────────────────────────────┘
                         │
                         ▼
   ┌───────────────────────────────────────────────┐
   │           VECTORSTORE (FAISS)                 │
   │   sector_index │ financial_index              │
   └───────────────────────────────────────────────┘
                         │
                         ▼
   ┌───────────────────────────────────────────────┐
   │           CAPA DE RETRIEVAL                   │
   │    retriever híbrido → reranker (LLM)         │
   └───────────────────────────────────────────────┘
                         │
                         ▼
   ┌───────────────────────────────────────────────┐
   │          ANÁLISIS DE CRÉDITO                  │
   │  financial_analyzer → sector_analyzer         │
   │  risk_scorer → decision_engine                │
   └───────────────────────────────────────────────┘
                         │
                         ▼
   ┌───────────────────────────────────────────────┐
   │           CAPA DE GENERACIÓN                  │
   │   Azure OpenAI GPT (modelo o-series)          │
   │   Dictamen: APROBAR / CONDICIONES / RECHAZAR  │
   └───────────────────────────────────────────────┘
```

---

## Estructura de carpetas

```
ficohsa-llm-credito-empresarial/
│
├── data/
│   ├── raw/
│   │   ├── informes_gestion/          # Informes oficiales de BCH, Banguat, BCN, SECMCA
│   │   │   ├── honduras/              # PDFs del BCH y CNBS Honduras
│   │   │   ├── guatemala/             # PDFs de Banguat y SIB Guatemala
│   │   │   ├── nicaragua/             # PDFs del BCN y SIBOIF Nicaragua
│   │   │   └── regional/
│   │   │       └── secmca/            # PDFs y Excel de SECMCA (regional)
│   │   └── estados_financieros/       # Estados financieros de empresas (carga manual)
│   │       └── [nombre_empresa]/      # Subcarpeta por empresa analizada
│   ├── processed/
│   │   ├── chunks/                    # Chunks generados tras el procesamiento
│   │   └── evidences/                 # Evidencias recuperadas por el RAG
│   └── vectorstore/
│       └── faiss_index/               # Índices FAISS persistidos
│           ├── sector_index/          # Índice de informes de gestión
│           └── financial_index/       # Índice de estados financieros
│
├── src/
│   ├── config/                        # Settings Pydantic + prompts del sistema
│   │   └── prompts/
│   ├── ingestion/                     # Carga, parseo y chunking de documentos
│   │   └── scrapers/                  # Scrapers para BCH API, SIB Guatemala, SECMCA
│   ├── embeddings/                    # Vectorización via Azure OpenAI
│   ├── vectorstore/                   # FAISS: indexación y búsqueda
│   ├── retrieval/                     # Recuperación híbrida + reranking
│   ├── credit/                        # Analizadores financiero, sectorial y motor de decisión
│   ├── llm/                           # Cliente Azure OpenAI GPT
│   ├── pipeline/                      # Orquestador RAG completo
│   ├── services/                      # Capa de servicio de alto nivel
│   └── utils/                         # Logger, helpers, validadores
│
├── scripts/
│   ├── download_sources.py            # Descarga automática de fuentes públicas
│   ├── ingest_documents.py            # Indexa documentos en FAISS
│   └── demo_analisis_credito.py       # Demo con empresa ficticia de ejemplo
│
├── tests/                             # Tests con pytest
├── notebooks/                         # Notebooks de exploración y evaluación
├── prompts/                           # Prompts del sistema versionados
├── docs/                              # Documentación técnica
├── logs/                              # Logs de ejecución (no versionados)
│
├── .env.example                       # Variables de entorno requeridas (plantilla)
├── .gitignore
├── requirements.txt
├── CLAUDE.md                          # Instrucciones para el asistente Claude Code
├── test_services.py                   # Diagnóstico de conectividad de servicios
└── README.md                          # Este archivo
```

---

## Fuentes de datos

El sistema utiliza **dos tipos de fuentes**:

### 1. Informes de gestión (contexto sectorial) — descarga automática

Documentos públicos de instituciones financieras oficiales centroamericanas. Se descargan con `scripts/download_sources.py`.

#### Honduras

| Documento | Institución | Método de obtención | URL / Notas |
|---|---|---|---|
| Informe de Estabilidad Financiera (dic 2024) | Banco Central de Honduras (BCH) | Descarga directa PDF | `bch.hn/estadisticos/EF/LIBINFORMEEF/` |
| Memoria Anual 2024 | BCH | Descarga directa PDF | `bch.hn/estadisticos/GIE/LIBMemoria/` |
| Programa Monetario 2025–2026 | BCH | Descarga directa PDF | `bch.hn/estadisticos/AM/LIBPROGRAMA MONETARIO/` |
| Informe de Coyuntura Financiero (dic 2024) | CNBS | Descarga directa PDF | `investigacioneinformes.cnbs.gob.hn` |
| Indicadores de crédito (BCH API) | BCH | **API REST** (requiere API key gratuita) | Registro: `bchapi-am.developer.azure-api.net` |

#### Guatemala

| Documento | Institución | Método de obtención | URL / Notas |
|---|---|---|---|
| Informe de Estabilidad Financiera (dic 2025) | Banguat + SIB Guatemala | Descarga directa PDF | `banguat.gob.gt/sites/default/files/banguat/Publica/` |
| Memoria de Labores 2024 | Banguat | Descarga directa PDF | `banguat.gob.gt/sites/default/files/banguat/memoria/` |
| Informe de Política Monetaria (sep 2024) | Banguat | Descarga directa PDF | `banguat.gob.gt/sites/default/files/banguat/Publica/comunica/` |
| Boletín Mensual Estadístico | SIB Guatemala | **Web scraping** (bloqueado — 403) | `sib.gob.gt` bloquea scrapers automatizados; descarga manual desde el portal |

#### Nicaragua

| Documento | Institución | Método de obtención | URL / Notas |
|---|---|---|---|
| Informe de Estabilidad Financiera (oct 2024) | Banco Central de Nicaragua (BCN) | Descarga directa PDF | `bcn.gob.ni/sites/default/files/documentos/` |
| Informe Anual 2024 | BCN | Descarga directa PDF | `bcn.gob.ni/sites/default/files/documentos/` |
| Informe de Gestión | SIBOIF | Descarga directa PDF | `siboif.gob.ni` — timeout frecuente, descarga manual alternativa |

#### Regional (Centroamérica)

| Documento | Institución | Método de obtención | URL / Notas |
|---|---|---|---|
| Informe Económico Regional 2023–2024 | SECMCA | Descarga directa PDF | `secmca.org/wp-content/uploads/` |
| Reportes mensuales de actividad económica (IMAE) | SECMCA | Descarga directa PDF | Patrón: `secmca.org/wp-content/uploads/[año]/[mes]/ReporteActividad-[año]-[mes].pdf` |
| Indicadores bancarios (Excel) | SECMCA | **Web scraping** | `secmca.org` — scraped con BeautifulSoup |

> **Limitaciones conocidas de scrapers**:
> - **SIB Guatemala** bloquea con 403 a scrapers. Requiere descarga manual desde `sib.gob.gt`.
> - **SIBOIF Nicaragua** tiene timeouts frecuentes. Si falla, descargar manualmente desde `siboif.gob.ni/nosotros/informacion-publica/informe-gestion`.
> - **BCH API** requiere registro gratuito en el portal de desarrolladores del BCH para obtener API key.

---

### 2. Estados financieros de empresas — casos de ejemplo reales

Para demostración y pruebas del sistema se utilizan estados financieros de empresas **reales, legalmente constituidas**, con documentos financieros **públicos y auditados**, obtenidos desde bolsas de valores, reguladores o sitios corporativos oficiales.

Estos archivos son de uso legítimo (documentos públicos) y **no contienen datos de clientes de Ficohsa**. Se organizan en `data/raw/estados_financieros/[pais]/[empresa]/`.

---

#### Honduras — ALUTECH, S.A. de C.V.

| Campo | Detalle |
|---|---|
| Empresa | Alutech, S.A. de C.V. |
| Sector | **Industria manufacturera** — láminas de zinc, canales de acero, drywall |
| Sede | San Pedro Sula, Cortés, Honduras |
| Por qué es pública | Emisora de bonos corporativos registrada en la Bolsa Centroamericana de Valores (BCV) |
| Regulador | BCV Honduras (`bcv.hn`) + Moody's Local Honduras |

| Archivo | Contenido | Año | Ubicación | Método de obtención |
|---|---|---|---|---|
| `alutech_ef_marzo_2022.pdf` | Estados financieros separados auditados (balance, resultados, flujo) | 2022 (mar) | `data/raw/estados_financieros/honduras/alutech_sa/` — **indexado en FAISS** | Descarga directa PDF desde BCV (`bcv.hn`) |
| `alutech_calificacion_riesgo_2024_TEST.pdf` | Informe de calificación de riesgo con datos financieros 2023-2024 | 2024 | `data/test/` — **para prueba manual en UI** | Descarga directa PDF desde Moody's Local HN |

---

#### Guatemala — Ciudad Comercial, S.A. (Paseo Cayalá)

| Campo | Detalle |
|---|---|
| Empresa | Ciudad Comercial, S.A. (subsidiaria de Paseo Comercial Developments, Inc.) |
| Sector | **Construcción e inmobiliario comercial** — desarrollo y arrendamiento del Centro Comercial Paseo Cayalá |
| Sede | Ciudad de Guatemala, Guatemala |
| Por qué es pública | Emisora de pagarés registrada en el Registro del Mercado de Valores y Mercancías (RMVM) de Guatemala |
| Regulador | RMVM Guatemala (`rmvm.gob.gt`) |

| Archivo | Contenido | Año | Ubicación | Método de obtención |
|---|---|---|---|---|
| `ciudad_comercial_ef_auditados_2023_TEST.pdf` | Estados financieros auditados bajo NIIF (52 páginas — balance, resultados, flujo, notas) | 2022–2023 | `data/test/` — **para prueba manual en UI** | Descarga directa PDF desde RMVM (`rmvm.gob.gt`) |

---

#### Nicaragua — Corporación Agrícola, S.A. y Subsidiarias (AGRICORP)

| Campo | Detalle |
|---|---|
| Empresa | Corporación Agrícola, S.A. y Subsidiarias |
| Nombre comercial | AGRICORP |
| Sector | **Agroindustria** — compra, procesamiento y distribución de arroz, sal, semolina y alimentos de consumo masivo |
| Sede | Managua, Nicaragua |
| Por qué es pública | Emisora registrada en la Bolsa de Valores de Nicaragua (BVDN) y supervisada por SIBOIF; publica estados financieros en su sitio corporativo |
| Regulador | SIBOIF + BVDN (`bolsanic.com`). Auditados por PricewaterhouseCoopers (PwC) |

| Archivo | Contenido | Año | Ubicación | Método de obtención |
|---|---|---|---|---|
| `agricorp_ef_auditados_2022.pdf` | Estados financieros consolidados auditados (71 páginas) | 2022 | `data/raw/estados_financieros/nicaragua/agricorp_sa/` — **indexado en FAISS** | Descarga directa PDF desde `agricorp.com.ni` |
| `agricorp_ef_auditados_2023.pdf` | Estados financieros consolidados auditados (66 páginas) | 2023 | `data/raw/estados_financieros/nicaragua/agricorp_sa/` — **indexado en FAISS** | Descarga directa PDF desde `agricorp.com.ni` |
| `agricorp_ef_auditados_2024_TEST.pdf` | Estados financieros consolidados auditados (75 páginas) | 2024 | `data/test/` — **para prueba manual en UI** | Descarga directa PDF desde `agricorp.com.ni` |

---

#### Estructura de carpetas de estados financieros

```
data/raw/estados_financieros/
├── honduras/
│   └── alutech_sa/
│       └── alutech_ef_marzo_2022.pdf          # EF auditados mar 2022 (BCV) — INDEXADO
├── guatemala/
│   └── ciudad_comercial_sa/
│       └── (vacío — EF movido a data/test/)
└── nicaragua/
    └── agricorp_sa/
        ├── agricorp_ef_auditados_2022.pdf     # EF consolidados 2022 (PwC) — INDEXADO
        └── agricorp_ef_auditados_2023.pdf     # EF consolidados 2023 (PwC) — INDEXADO

data/test/                                      # PDFs reservados para prueba manual desde la UI
├── alutech_calificacion_riesgo_2024_TEST.pdf  # Honduras — Informe Moody's 2024
├── ciudad_comercial_ef_auditados_2023_TEST.pdf # Guatemala — EF NIIF 2023 (RMVM)
└── agricorp_ef_auditados_2024_TEST.pdf        # Nicaragua — EF consolidados 2024 (PwC)
```

---

#### Agregar estados financieros de clientes reales (uso en producción)

En producción, el oficial de crédito carga los estados financieros del cliente directamente en la carpeta correspondiente:

```
data/raw/estados_financieros/
└── [pais]/
    └── [nombre_empresa_normalizado]/
        ├── balance_general_2023.xlsx
        ├── estado_resultados_2023.xlsx
        └── flujo_caja_2023.pdf
```

> **Regla crítica**: Los datos financieros reales de clientes de Ficohsa **nunca se commitean al repositorio**. La carpeta `data/raw/estados_financieros/` está en `.gitignore` para entornos de producción. Los archivos de ejemplo del repositorio son únicamente documentos públicos.

---

## Instalación

### Requisitos previos
- Python 3.11+
- Acceso a Azure OpenAI con deployments de:
  - GPT (modelo de razonamiento)
  - text-embedding (modelo de embeddings)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/ficohsa/ficohsa-llm-credito-empresarial.git
cd ficohsa-llm-credito-empresarial

# 2. Crear entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Azure OpenAI
```

---

## Configuración

Editar el archivo `.env` con las credenciales de Azure OpenAI:

```env
# LLM (modelo de razonamiento)
AZURE_OPENAI_KEY=tu-api-key
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=nombre-deployment-gpt
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Embeddings
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=nombre-deployment-embeddings

# Opcional: API del BCH Honduras
BCH_API_KEY=tu-api-key-bch
```

Ver [.env.example](.env.example) para la lista completa.

---

## Cómo ejecutar el sistema

### Paso 0 — Verificar conectividad

```bash
.venv/Scripts/python test_services.py
```

Verifica que Azure OpenAI (LLM + embeddings), el logger y los módulos internos estén OK.

---

### Paso 1 — Descargar fuentes públicas (informes de gestión)

```bash
.venv/Scripts/python scripts/download_sources.py --fuente todas
```

Opciones:
```bash
--fuente todas          # Descarga BCH, SIB Guatemala y SECMCA
--fuente bch            # Solo BCH Honduras (requiere BCH_API_KEY en .env)
--fuente sib            # Solo SIB Guatemala
--fuente secmca         # Solo SECMCA regional
--max-reportes 5        # Número máximo de reportes por fuente (default: 3)
--fecha-inicio 2023-01-01  # Fecha inicio para BCH API
```

Los archivos se guardan en `data/raw/informes_gestion/[pais]/`.

---

### Paso 2 — Indexar documentos en FAISS

```bash
# Indexar informes de gestión sectoriales (sector_index)
.venv/Scripts/python scripts/ingest_documents.py --tipo sector

# Indexar estados financieros de empresas (financial_index) — opcional
.venv/Scripts/python scripts/ingest_documents.py --tipo financiero
```

> **Nota**: El `financial_index` es opcional en el flujo actual. La interfaz Streamlit
> lee el documento subido directamente sin pasar por FAISS. El `sector_index` es crítico
> y debe estar actualizado.

Genera los índices en `data/vectorstore/faiss_index/sector_index/` y `financial_index/`.

---

### Paso 3 — Iniciar la interfaz Streamlit

```bash
.venv/Scripts/streamlit run app.py
```

Abre el navegador en **`http://localhost:8501`**.

**Flujo de uso:**

1. En el panel izquierdo ingresa: **nombre de empresa**, sector y país de operación.
2. **Sube el estado financiero** — PDF, DOCX o TXT (balance general, EF auditados, informe de calificación, etc.)
3. Presiona **Analizar crédito**.
4. El sistema extrae el texto del documento, lo cruza contra los informes de gestión
   indexados del país seleccionado y genera el dictamen crediticio.

**Archivos de prueba disponibles** en `data/test/`:

| Archivo | Empresa | País | Contenido |
|---|---|---|---|
| `alutech_calificacion_riesgo_2024_TEST.pdf` | Alutech S.A. | Honduras | Informe Moody's 2024 con EF 2023-2024 |
| `ciudad_comercial_ef_auditados_2023_TEST.pdf` | Ciudad Comercial S.A. | Guatemala | EF NIIF auditados 2022-2023 |
| `agricorp_ef_auditados_2024_TEST.pdf` | AGRICORP S.A. | Nicaragua | EF consolidados auditados 2024 |

**Demo CLI sin UI (empresa ficticia):**
```bash
.venv/Scripts/python scripts/demo_analisis_credito.py
```

---

## Cómo actualizar la base de conocimiento

La base de conocimiento tiene dos índices FAISS independientes. Cada uno se actualiza
de forma separada.

---

### Actualizar informes de gestión (sector_index)

Úsalo cuando: publican nuevos informes un banco central (BCH, Banguat, BCN) o un regulador
(CNBS, SIB, SIBOIF) o cuando quieres agregar nuevas fuentes sectoriales.

**Paso 1 — Coloca el nuevo PDF en la carpeta del país correspondiente:**
```
data/raw/informes_gestion/
├── honduras/    ← aquí los del BCH y CNBS
├── guatemala/   ← aquí los de Banguat y SIB
└── nicaragua/   ← aquí los del BCN y SIBOIF
```

**Paso 2 — Re-indexa el sector_index completo:**
```bash
.venv/Scripts/python scripts/ingest_documents.py --tipo sector
```

> ⚠️ Esto **reconstruye el índice desde cero** con todos los PDFs del directorio.
> El proceso puede tomar varios minutos según el volumen de documentos.
> Respeta el rate limit de Azure OpenAI S0 (50 chunks/lote, pausa de 12 segundos entre lotes).

**Chunks esperados por país (referencia actual):**
| País | Documentos indexados | Chunks aprox. |
|---|---|---|
| Honduras | BCH IEF dic-2024, Memoria 2024, Prog. Monetario 2025-26, CNBS Coyuntura dic-2024 | ~1,200 |
| Guatemala | Banguat IEF dic-2025, Memoria 2024, Pol. Monetaria sep-2024 | ~800 |
| Nicaragua | BCN IEF oct-2024, Informe Anual 2024 | ~990 |

---

### Actualizar estados financieros de referencia (financial_index)

> **Contexto importante**: En el flujo principal de Streamlit, el usuario sube el PDF directamente
> y el sistema lo analiza sin necesidad de indexación previa. El `financial_index` es un índice
> de referencia para empresas frecuentes y para el script demo CLI.

**Cuándo re-indexar**: cuando cambias los PDFs en `data/raw/estados_financieros/`
(por ejemplo, si mueves archivos a `data/test/`, agregas nuevos EF o eliminas existentes).

**Paso 1 — Coloca los PDFs en la carpeta de la empresa:**
```
data/raw/estados_financieros/
└── [pais]/
    └── [nombre_empresa]/
        ├── balance_general_2024.pdf
        └── estado_resultados_2024.pdf
```

**Paso 2 — Re-indexa solo los financieros:**
```bash
.venv/Scripts/python scripts/ingest_documents.py --tipo financiero
```

**Estado actual del financial_index (post-separación de archivos de prueba):**
| Empresa | País | Archivos indexados |
|---|---|---|
| Alutech S.A. | Honduras | `alutech_ef_marzo_2022.pdf` |
| AGRICORP S.A. | Nicaragua | `agricorp_ef_auditados_2022.pdf`, `agricorp_ef_auditados_2023.pdf` |
| Ciudad Comercial S.A. | Guatemala | *(vacío — el único PDF fue movido a `data/test/`)* |

> Si quieres que Guatemala tenga referencia en el financial_index, copia
> `data/test/ciudad_comercial_ef_auditados_2023_TEST.pdf` de vuelta a
> `data/raw/estados_financieros/guatemala/ciudad_comercial_sa/` y re-indexa.

---

### Re-indexar todo desde cero

```bash
.venv/Scripts/python scripts/ingest_documents.py --tipo todos
```

---

## Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| LLM | Azure OpenAI (modelo o-series GPT) |
| Embeddings | Azure OpenAI text-embedding-3-large (1536 dim) |
| Vector Store | FAISS (faiss-cpu) |
| Orquestación RAG | LangChain |
| Configuración | Pydantic BaseSettings |
| Parseo de documentos | pdfplumber, python-docx, python-pptx, openpyxl |
| Web scraping | BeautifulSoup4, requests |
| Evaluación RAG | RAGAS (faithfulness, answer_relevancy, context_precision) |
| Interfaz (demo) | Streamlit + Plotly |
| Testing | pytest + pytest-cov |
| Logging | Python logging con rotación de archivos |

---

## Restricciones importantes

1. **Sin datos reales de clientes**: Ningún estado financiero real debe commitearse al repositorio. La carpeta `data/raw/estados_financieros/` está en `.gitignore`.
2. **Solo Azure OpenAI**: No usar OpenAI directo ni AWS Bedrock. El banco opera sobre infraestructura Azure.
3. **Trazabilidad obligatoria**: Toda afirmación del dictamen debe citar fuente y sección del documento recuperado.
4. **Control de alucinaciones**: Si el sistema no tiene datos suficientes para concluir, debe responder "información insuficiente para concluir", no inventar.
5. **Sin `.env` real en git**: Solo commitear `.env.example` con valores de ejemplo.

---

## Equipo y contexto

**Área responsable**: Data Science & GenAI — Banco Ficohsa
**Uso previsto**: Uso interno del área de Riesgo Crediticio y Banca Empresarial
**Entorno de producción**: Azure (Functions, Blob Storage, AI Search)
