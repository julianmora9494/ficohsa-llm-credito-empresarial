# -*- coding: utf-8 -*-
"""
FicoCredito AI - Interfaz Streamlit para analisis de credito empresarial.
Uso: .venv/Scripts/streamlit run app.py
"""
import io
import sys
from pathlib import Path

# Compatibilidad UTF-8 en Windows
# Streamlit re-ejecuta el script en cada interaccion; el try/except evita el error
# "I/O operation on closed file" cuando stdout ya fue reemplazado en una ejecucion previa.
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# ─── Configuracion de pagina ─────────────────────────────────────────────────
st.set_page_config(
    page_title="FicoCredito AI",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personalizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .decision-aprobar    { background:#d4edda; border-left:6px solid #28a745;
                           padding:16px; border-radius:6px; color:#155724; }
    .decision-condiciones{ background:#fff3cd; border-left:6px solid #ffc107;
                           padding:16px; border-radius:6px; color:#856404; }
    .decision-rechazar   { background:#f8d7da; border-left:6px solid #dc3545;
                           padding:16px; border-radius:6px; color:#721c24; }
    .decision-insuficiente{background:#e2e3e5; border-left:6px solid #6c757d;
                           padding:16px; border-radius:6px; color:#383d41; }
    .risk-badge  { background:#f8d7da; color:#721c24; padding:4px 10px;
                   border-radius:12px; font-size:0.85rem; margin:3px 0; display:block; }
    .ok-badge    { background:#d4edda; color:#155724; padding:4px 10px;
                   border-radius:12px; font-size:0.85rem; margin:3px 0; display:block; }
    .cond-badge  { background:#fff3cd; color:#856404; padding:4px 10px;
                   border-radius:12px; font-size:0.85rem; margin:3px 0; display:block; }
    .fuente-badge{ background:#e7f1ff; color:#004085; padding:3px 8px;
                   border-radius:10px; font-size:0.8rem; margin:2px; display:inline-block; }
    .disclaimer  { background:#f0f0f0; border:1px dashed #aaa; padding:10px;
                   border-radius:6px; font-size:0.82rem; color:#555; margin-top:16px; }
    .upload-zone { background:#f8f9fa; border:2px dashed #dee2e6; padding:20px;
                   border-radius:8px; text-align:center; margin-bottom:12px; }
    .info-box    { background:#e7f3ff; border-left:4px solid #0066cc;
                   padding:10px 14px; border-radius:4px; font-size:0.88rem; }
</style>
""", unsafe_allow_html=True)


# ─── Inicializacion de servicio (singleton en session_state) ─────────────────
@st.cache_resource(show_spinner="Cargando indices FAISS y modelos...")
def load_service():
    """Carga el CreditService una sola vez y lo reutiliza en toda la sesion."""
    from src.services.credit_service import CreditService
    service = CreditService()
    status = service.initialize(load_existing_indexes=True)
    return service, status


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=64)
    st.title("FicoCredito AI")
    st.caption("Analista de credito empresarial — Banco Ficohsa")
    st.divider()

    # ── Datos de la empresa ──────────────────────────────────────────────────
    st.subheader("1. Datos de la empresa")

    empresa = st.text_input("Nombre de la empresa", value="", placeholder="Ej: Alutech S.A.")
    sector = st.selectbox(
        "Sector economico",
        ["agricola", "comercio", "industria", "servicios", "construccion", "inmobiliario", "otro"],
        index=0,
    )
    pais = st.selectbox("Pais de operacion", ["Honduras", "Guatemala", "Nicaragua"], index=0)
    anio = st.number_input("Ano del analisis", min_value=2018, max_value=2025, value=2023)

    country_map = {"Honduras": "honduras", "Guatemala": "guatemala", "Nicaragua": "nicaragua"}
    country_filter = country_map[pais]

    st.divider()

    # ── Subir estado financiero ──────────────────────────────────────────────
    st.subheader("2. Estado financiero")
    st.caption("Sube el PDF, DOCX o TXT con los estados financieros de la empresa.")

    uploaded_file = st.file_uploader(
        "Seleccionar archivo",
        type=["pdf", "docx", "txt", "md"],
        help="Formatos soportados: PDF, DOCX, TXT, Markdown",
    )

    if uploaded_file:
        st.success(f"Archivo cargado: **{uploaded_file.name}**  \n({uploaded_file.size / 1024:.1f} KB)")

    st.divider()

    # ── Boton de analisis ────────────────────────────────────────────────────
    analizar = st.button(
        "Analizar credito",
        type="primary",
        use_container_width=True,
        disabled=(not uploaded_file or not empresa.strip()),
    )

    if not empresa.strip():
        st.caption("⚠️ Ingresa el nombre de la empresa.")
    if not uploaded_file:
        st.caption("⚠️ Sube el estado financiero.")


# ─── Panel principal ─────────────────────────────────────────────────────────
st.title("🏦 FicoCredito AI — Analisis de Credito Empresarial")
st.caption("Sistema de apoyo a decisiones crediticias | Banco Ficohsa | Uso interno")

# Cargar servicio
try:
    service, status = load_service()
    idx_sector = "✅ Listo" if status.get("sector") else "⚠️ No cargado"
    idx_fin    = "✅ Listo" if status.get("financial") else "ℹ️ Usando doc subido"
    st.info(f"Indice sectorial: {idx_sector}  |  Indice financiero (referencia): {idx_fin}", icon="📊")
except Exception as e:
    st.error(f"Error al cargar el servicio: {e}")
    st.stop()


# ─── Ejecutar analisis ───────────────────────────────────────────────────────
if analizar and uploaded_file and empresa.strip():
    file_bytes = uploaded_file.read()

    with st.spinner(f"Analizando **{empresa}**... leyendo documento, consultando RAG y generando dictamen..."):
        try:
            result = service.analizar_credito_desde_archivo(
                file_bytes=file_bytes,
                file_name=uploaded_file.name,
                empresa=empresa.strip(),
                sector=sector,
                pais=pais,
                anio=int(anio),
                country_filter=country_filter,
            )
        except Exception as e:
            st.error(f"Error durante el analisis: {e}")
            st.stop()

    # ─── DICTAMEN ────────────────────────────────────────────────────────────
    decision  = result["decision"]
    confianza = result["confianza"].upper()

    css_class = {
        "APROBAR":                 "decision-aprobar",
        "APROBAR CON CONDICIONES": "decision-condiciones",
        "RECHAZAR":                "decision-rechazar",
    }.get(decision, "decision-insuficiente")

    emoji = {
        "APROBAR":                 "✅",
        "APROBAR CON CONDICIONES": "⚠️",
        "RECHAZAR":                "❌",
    }.get(decision, "ℹ️")

    st.markdown(f"""
    <div class="{css_class}">
        <h2 style="margin:0">{emoji} DICTAMEN: {decision}</h2>
        <p style="margin:4px 0 0 0; font-size:0.9rem">
            Empresa: <strong>{empresa}</strong> &nbsp;|&nbsp;
            Sector: {sector} &nbsp;|&nbsp;
            Pais: {pais} &nbsp;|&nbsp;
            Ano: {anio} &nbsp;|&nbsp;
            Confianza: <strong>{confianza}</strong> &nbsp;|&nbsp;
            Fuente: <em>{uploaded_file.name}</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    st.divider()

    # ─── RESUMEN + SEÑALES ────────────────────────────────────────────────────
    col_res, col_sen = st.columns([3, 2])

    with col_res:
        st.subheader("Resumen ejecutivo")
        st.markdown(result["resumen_ejecutivo"])

        if result.get("analisis_financiero"):
            st.subheader("Analisis financiero")
            st.markdown(result["analisis_financiero"])

        if result.get("contexto_sectorial"):
            st.subheader("Contexto sectorial")
            st.markdown(result["contexto_sectorial"])

        st.subheader("Justificacion del dictamen")
        st.markdown(result["justificacion"])

    with col_sen:
        if result["seniales_riesgo"]:
            st.subheader("Senales de riesgo")
            for s in result["seniales_riesgo"]:
                st.markdown(f'<span class="risk-badge">⚠️ {s}</span>', unsafe_allow_html=True)

        if result["seniales_positivas"]:
            st.subheader("Senales positivas")
            for s in result["seniales_positivas"]:
                st.markdown(f'<span class="ok-badge">✅ {s}</span>', unsafe_allow_html=True)

        if result["condiciones"]:
            st.subheader("Condiciones requeridas")
            for c in result["condiciones"]:
                st.markdown(f'<span class="cond-badge">📋 {c}</span>', unsafe_allow_html=True)

    st.divider()

    # ─── FUENTES CONSULTADAS ──────────────────────────────────────────────────
    st.subheader("Fuentes consultadas por el RAG")
    fuentes = result.get("fuentes_consultadas", [])
    if fuentes:
        fuentes_html = " ".join(
            f'<span class="fuente-badge">📄 {f}</span>' for f in fuentes
        )
        st.markdown(fuentes_html, unsafe_allow_html=True)
    else:
        st.caption("No se recuperaron fuentes adicionales.")

    # ─── DISCLAIMER ───────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="disclaimer">⚖️ {result["disclaimer"]}</div>',
        unsafe_allow_html=True,
    )

else:
    # ─── PANTALLA DE INICIO ───────────────────────────────────────────────────
    col_info, col_guide = st.columns([1, 1])

    with col_info:
        st.markdown("""
### Como usar este sistema

1. **Ingresa el nombre** de la empresa en el panel izquierdo.
2. **Selecciona el sector** economico y el pais de operacion.
3. **Sube el estado financiero** (PDF, DOCX o TXT) — puede ser el balance
   general, estado de resultados, informe auditado o cualquier documento
   financiero de la empresa.
4. Presiona **Analizar credito**.

El sistema **leera el documento completo**, lo cruzara con los informes de gestion
de bancos centrales y reguladores de Centroamerica, y generara un dictamen
razonado con fuentes citadas.

---

### Documentos aceptados
| Tipo | Formatos |
|---|---|
| Estados financieros auditados | PDF, DOCX |
| Balances generales | PDF, DOCX |
| Estados de resultados | PDF |
| Informes de gestion internos | PDF, TXT |
| Calificaciones de riesgo | PDF |

---

> **Aviso**: Este sistema es una herramienta de apoyo. El dictamen final
> lo toma el oficial de credito con base en el analisis completo del expediente.
        """)

    with col_guide:
        st.markdown("""
### Documentos de prueba disponibles

Los siguientes archivos estan listos en `data/test/` para probar el sistema:

| Archivo | Empresa | Pais |
|---|---|---|
| `alutech_calificacion_riesgo_2024_TEST.pdf` | Alutech S.A. | Honduras |
| `ciudad_comercial_ef_auditados_2023_TEST.pdf` | Ciudad Comercial | Guatemala |
| `agricorp_ef_auditados_2024_TEST.pdf` | AGRICORP S.A. | Nicaragua |

### Base de conocimiento sectorial (RAG)

| Pais | Fuentes indexadas | Chunks |
|---|---|---|
| Honduras | BCH IEF dic-2024, Memoria Anual 2024, Prog. Monetario 2025-26, CNBS Coyuntura dic-2024 | ~1,200 |
| Guatemala | Banguat IEF dic-2025, Memoria de Labores 2024, Pol. Monetaria sep-2024 | ~800 |
| Nicaragua | BCN IEF oct-2024, Informe Anual 2024 | ~990 |

### Empresas con estados financieros indexados

| Empresa | Pais | Anos |
|---|---|---|
| AGRICORP S.A. | Nicaragua | 2022, 2023 |
| Alutech S.A. | Honduras | 2022 |
        """)

    st.info(
        "Completa los datos de la empresa y sube el estado financiero en el panel izquierdo.",
        icon="👈"
    )
