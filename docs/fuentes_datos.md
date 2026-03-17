# Fuentes de Datos — FicoCrédito AI

Documentación de todas las fuentes públicas validadas para alimentar el sistema RAG.
Todas las URLs fueron verificadas en marzo 2026 y son de acceso gratuito.

---

## Prioridad de implementación

| Prioridad | Fuente | Por qué |
|---|---|---|
| 🔴 CRÍTICA | BCH API (Honduras) | 10,000+ series, acceso programático REST |
| 🔴 CRÍTICA | SIB Guatemala – Boletín Mensual | Crédito desglosado por 7 sectores, mora |
| 🔴 CRÍTICA | SECMCA – Reportes Mensuales | Indicadores comparables 7 países |
| 🟠 ALTA | CNBS Honduras | Central crediticia + estados financieros |
| 🟠 ALTA | BANGUAT Indicadores GT | 12M registros, IA nativa, descarga directa |
| 🟠 ALTA | SIBOIF Nicaragua | Historial 2008+, mora por institución |
| 🟡 MEDIA | BCN Nicaragua – Informe Mensual | Datos sectoriales compilados |
| 🟡 MEDIA | CEPALSTAT API | Contexto macroeconómico regional |
| 🟢 COMPLEMENTARIA | ICEFI | Análisis fiscal/presupuesto público |
| 🟢 COMPLEMENTARIA | World Bank DataBank | Benchmarking regional |

---

## Honduras

### Banco Central de Honduras (BCH)

**Portal:** https://www.bch.hn/estadisticas-y-publicaciones-economicas

#### BCH Web API ← PRIORITARIA
- **URL:** https://bchapi-am.developer.azure-api.net/
- **Tipo:** REST API documentada
- **Acceso:** Registro gratuito → API key
- **Formatos:** JSON, XML, CSV, HTML
- **Series disponibles:** 10,000+
- **Actualización:** Diaria (tipo de cambio), Mensual (sectoriales)
- **Contenido relevante para crédito:**
  - IMAE desglosado por rama: agropecuario, industrial, comercio, servicios
  - Crédito del sistema financiero por sector económico
  - Tasas de interés activas y pasivas
  - Tipo de cambio
- **Integración:** `src/ingestion/scrapers/bch_api_scraper.py`
- **Documentación legal:** https://www.bch.hn/marco-legal/terminos-condiciones-uso-web-api

#### BCH IMAE (Índice Mensual de Actividad Económica)
- **URL:** https://www.bch.hn/estadisticas-y-publicaciones-economicas/sector-real/indice-mensual-de-actividad-economica
- **Frecuencia:** Mensual
- **Tipo:** PDF + Excel descargable
- **Sectores cubiertos:**
  - Agropecuario (café, granos básicos, caña de azúcar, ganadería, acuicultura)
  - Industrial manufacturero (alimentos, bebidas, cemento, arneses)
  - Comercio (mayorista y minorista)
  - Servicios financieros y telecomunicaciones

#### BCH Reportes Dinámicos
- **URL:** https://www.bch.hn/estadisticas-y-publicaciones-economicas/reportes-dinamicos
- **Tipo:** Dashboard interactivo + descarga CSV/Excel
- **Frecuencia:** Mensual
- **Contenido:** Sector real, monetario, externo, fiscal, precios

---

### CNBS (Comisión Nacional de Bancos y Seguros)

**Portal:** https://www.cnbs.gob.hn

#### Publicaciones CNBS ← PRIORITARIA
- **URL:** https://publicaciones.cnbs.gob.hn/
- **Tipo:** PDF + Excel
- **Frecuencia:** Mensual, trimestral, anual
- **Contenido:**
  - Cartera de crédito por sector económico
  - Tasa de mora por institución y sector
  - Liquidez y solvencia del sistema bancario
  - Estados financieros consolidados

#### Portal Analítico CNBS
- **URL:** https://analitica.cnbs.gob.hn/
- **Tipo:** Dashboard
- **Contenido:** Indicadores financieros consolidados del sistema

#### Central de Información Crediticia
- **URL:** https://www.cnbs.gob.hn/central-de-informacion-crediticia/
- **Tipo:** Base de datos de riesgos crediticios
- **Utilidad:** Historial de mora empresarial, clasificación de deudores

---

## Guatemala

### Banco de Guatemala (BANGUAT)

**Portal:** https://banguat.gob.gt

#### Indicadores GT ← PRIORITARIA
- **URL:** https://banguat.gob.gt/indicadoresgt/
- **Tipo:** Plataforma web con IA nativa (AVI)
- **Contenido:** 12 millones+ registros económicos
- **Características:**
  - Asistente virtual que responde en lenguaje natural
  - Generación automática de gráficos y tablas
  - Descarga directa múltiples formatos
- **Datos disponibles:** Inflación, tipo de cambio, crecimiento, remesas, balanza de pagos

#### PIB Regional y Departamental
- **URL:** https://banguat.gob.gt/page/producto-interno-bruto-regional-y-departamental
- **Tipo:** Dashboard + Excel descargable
- **Cobertura:** 22 departamentos, 8 regiones, 17 actividades económicas
- **Series:** Desde 2013
- **Descarga directa:** https://banguat.gob.gt/page/cuadros-estadisticos-por-departamento-2013-2023-0

#### Informes de Política Monetaria
- **URL:** https://banguat.gob.gt/sites/default/files/banguat/Publica/comunica/informe_pol_mon_mar2025.pdf
- **Tipo:** PDF
- **Frecuencia:** Trimestral

---

### SIB (Superintendencia de Bancos de Guatemala)

**Portal:** https://www.sib.gob.gt

#### Boletín Mensual de Estadísticas ← PRIORITARIA
- **URL:** https://www.sib.gob.gt/web/sib/Boletn-Mensual-de-Estadisticas
- **Tipo:** PDF descargable
- **Frecuencia:** Mensual
- **Contenido:**
  - Crédito por sector (Consumo 50.8%, Comercio 14.3%, Manufactura 7.1%, Construcción 7%, Agro 2.8%)
  - Calidad de cartera y mora
  - Liquidez, solvencia, rentabilidad
  - Grupos financieros

#### Indicadores Financieros
- **URL:** https://www.sib.gob.gt/web/sib/indicadores_financieros
- **Tipo:** Dashboard + tablas descargables
- **Contenido:** Tasas de interés, evolución cartera, indicadores por sector

#### Informe de Estabilidad Financiera
- **URL:** https://www.sib.gob.gt/web/sib/informacion_sistema_financiero/estabilidad
- **Tipo:** PDF
- **Frecuencia:** Trimestral

---

## Nicaragua

### Banco Central de Nicaragua (BCN)

**Portal:** https://www.bcn.gob.ni

#### Estadísticas BCN
- **URL:** https://www.bcn.gob.ni/estadisticas
- **Tipo:** Portal centralizado
- **Contenido sectorial:**
  - Producción agropecuaria (café, granos, ganadería, acuicultura, pesca)
  - Producción industrial (hidrocarburos, minería, manufactura)
  - Zonas francas
  - Telecomunicaciones y transporte

#### Informe Financiero Mensual ← PRIORITARIA
- **URL:** https://bcn.gob.ni/publicaciones/informe_financiero
- **Tipo:** PDF descargable
- **Frecuencia:** Mensual
- **Contenido:**
  - Cartera de crédito por sector
  - Indicadores de calidad de cartera (mora, provisiones)
  - Liquidez, rentabilidad, solvencia

#### Informe de Estabilidad Financiera
- **URL:** https://www.bcn.gob.ni/publicaciones/informe-de-estabilidad-financiera-de-abril-2024
- **Tipo:** PDF
- **Frecuencia:** Semestral

---

### SIBOIF (Superintendencia de Bancos)

**Portal:** https://www.superintendencia.gob.ni

#### Estadísticas Dashboard ← PRIORITARIA
- **URL:** https://www.superintendencia.gob.ni/consultas/estadisticas
- **Tipo:** Dashboard interactivo + descarga
- **Frecuencia:** Mensual
- **Histórico:** Desde 2008
- **Filtros:** Institución, tipo de institución, tipo de reporte, período

---

## Fuentes Regionales

### SECMCA (Secretaría Ejecutiva del Consejo Monetario Centroamericano)

**Portal:** https://www.secmca.org
**Cobertura:** Costa Rica, El Salvador, Guatemala, Honduras, Nicaragua, Panamá, R. Dominicana

#### Reporte Mensual de Actividad Económica ← PRIORITARIA
- **URL:** https://www.secmca.org/informe/reporte-mensual-de-actividad-economica/
- **Tipo:** PDF + Excel (desde jun 2024 también BI interactivo)
- **Frecuencia:** Mensual
- **Contenido:** IMAE por país, desglose sectorial, tendencias regionales

#### Reporte Mensual de Indicadores Bancarios ← PRIORITARIA
- **URL:** https://www.secmca.org/informe/reporte-mensual-de-indicadores-bancarios/
- **Tipo:** PDF + Excel
- **Frecuencia:** Mensual
- **Contenido:** Crédito, depósitos, tasas de interés, mora — todos los países

#### Reportes Trimestrales
- **URL:** https://www.secmca.org/periodo_informe/trimestral/
- **Incluye:** Balanza de pagos, revisión de políticas monetarias, evaluaciones de riesgo

---

### CEPALSTAT

**Portal:** https://estadisticas.cepal.org/cepalstat/
**API:** https://statistics.cepal.org/portal/cepalstat/open-data.html?lang=es

- **Tipo:** API REST sin autenticación
- **Formatos:** JSON, XML, CSV
- **Contenido:** Cuentas nacionales, comercio exterior, indicadores sociales
- **Uso recomendado:** Contexto macroeconómico regional + validación

---

## Calendario de ingestión recomendado

```
DIARIO:
  - BCH API → Tipo de cambio (serie: TC_REF)

MENSUAL (días 5-10 del mes siguiente):
  - BCH IMAE → Excel de actividad económica sectorial
  - CNBS → Boletín mensual de estadísticas
  - SIB Guatemala → Boletín mensual
  - SIBOIF Nicaragua → Dashboard estadísticas
  - BCN Nicaragua → Informe financiero mensual
  - SECMCA → Actividad económica + indicadores bancarios

TRIMESTRAL:
  - SECMCA → Balanza de pagos + evaluaciones de riesgo
  - SIB Guatemala → Estabilidad financiera
  - BCN Nicaragua → Estabilidad financiera
  - BANGUAT → Informe de política monetaria

ANUAL:
  - BCH → Memoria anual
  - BANGUAT → Informe anual
  - CEPAL → Estudio económico regional
```

---

## Notas de implementación

### PDFs vs APIs
- **Preferir APIs/Excel** cuando estén disponibles (BCH API, CEPALSTAT API)
- **PDFs** requieren pdfplumber + post-procesamiento → usar `src/ingestion/document_loader.py`
- **Dashboards interactivos** (SIB, SIBOIF, BANGUAT) → descarga manual o Playwright

### Control de versiones de documentos
- Guardar con fecha en nombre: `sib_guatemala_boletin_2026_02.pdf`
- Metadata en chunk: `{"fuente": "SIB Guatemala", "periodo": "2026-02", "url": "..."}`

### Grounding en respuestas
Cada chunk debe incluir en metadata:
```json
{
  "fuente": "Banco Central de Honduras",
  "seccion": "IMAE - Sector Agropecuario",
  "periodo": "Enero 2026",
  "url_origen": "https://www.bch.hn/...",
  "fecha_descarga": "2026-02-10"
}
```
