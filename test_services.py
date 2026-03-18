# -*- coding: utf-8 -*-
"""
Script de diagnostico para verificar que todos los servicios del sistema
estan correctamente configurados y accesibles.

Ejecutar desde la raiz del proyecto:
    .venv/Scripts/python test_services.py
"""
import sys
import os
from pathlib import Path

# Asegurar que src/ este en el path
sys.path.insert(0, str(Path(__file__).parent))

# Forzar UTF-8 en stdout para Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─── Colores para terminal ───────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

OK = f"{GREEN}[OK]{RESET}"
FAIL = f"{RED}[FAIL]{RESET}"


def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'-'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'-'*55}{RESET}")


def check(label: str, fn) -> bool:
    """Ejecuta fn(), imprime resultado y retorna True si paso."""
    try:
        result = fn()
        msg = f"  {OK}  {label}"
        if result and isinstance(result, str):
            msg += f" -- {YELLOW}{result}{RESET}"
        print(msg)
        return True
    except Exception as e:
        print(f"  {FAIL}  {label}")
        print(f"        {RED}{type(e).__name__}: {e}{RESET}")
        return False


# ─── TEST 1: Variables de entorno ────────────────────────────────────────────
section("1. Variables de entorno (.env)")

def test_dotenv():
    from dotenv import load_dotenv
    loaded = load_dotenv()
    if not loaded:
        raise RuntimeError(".env no encontrado o vacio")
    return ".env cargado"

def test_azure_key():
    key = os.getenv("AZURE_OPENAI_KEY", "")
    if not key or key == "your-azure-openai-key-here":
        raise ValueError("AZURE_OPENAI_KEY no configurada")
    return f"key ...{key[-6:]}"

def test_azure_endpoint():
    ep = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    if not ep or "your-resource" in ep:
        raise ValueError("AZURE_OPENAI_ENDPOINT no configurada")
    return ep

def test_azure_deployment():
    d = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    if not d:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME no configurada")
    return d

def test_embedding_deployment():
    d = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")
    if not d:
        raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT no configurada")
    return d

def test_api_version():
    v = os.getenv("AZURE_OPENAI_API_VERSION", "")
    if not v:
        raise ValueError("AZURE_OPENAI_API_VERSION no configurada")
    return v

env_ok = all([
    check(".env cargado", test_dotenv),
    check("AZURE_OPENAI_KEY", test_azure_key),
    check("AZURE_OPENAI_ENDPOINT", test_azure_endpoint),
    check("AZURE_OPENAI_DEPLOYMENT_NAME (LLM)", test_azure_deployment),
    check("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", test_embedding_deployment),
    check("AZURE_OPENAI_API_VERSION", test_api_version),
])


# ─── TEST 2: Settings Pydantic ───────────────────────────────────────────────
section("2. Configuracion Pydantic (Settings)")

settings = None

def test_settings_load():
    global settings
    from src.config.settings import get_settings
    settings = get_settings()
    return f"endpoint={settings.azure_openai_endpoint}"

def test_settings_paths():
    if settings is None:
        raise RuntimeError("Settings no cargado")
    paths = [
        settings.data_raw_path,
        settings.informes_gestion_path,
        settings.estados_financieros_path,
        settings.vector_store_path.parent,
        settings.log_file.parent,
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
    return f"{len(paths)} directorios verificados/creados"

settings_ok = all([
    check("Settings carga sin errores", test_settings_load),
    check("Rutas de datos creadas", test_settings_paths),
])


# ─── TEST 3: Logger ──────────────────────────────────────────────────────────
section("3. Logger")

def test_logger():
    from src.utils.logger import setup_logger
    log = setup_logger("test_services")
    log.info("Logger de prueba funcionando correctamente")
    return "logs/app.log activo"

check("Logger inicializado", test_logger)


# ─── TEST 4: LLM — Azure OpenAI ─────────────────────────────────────────────
section("4. LLM -- Azure OpenAI (GPT)")

def test_llm_client_init():
    from src.llm.llm_manager import LLMManager
    mgr = LLMManager()
    _ = mgr.client  # fuerza lazy load
    return f"deployment={mgr._settings.azure_openai_deployment_name}"

def test_llm_invoke():
    from src.llm.llm_manager import LLMManager
    mgr = LLMManager()
    response = mgr.invoke("Responde solo con la palabra: FUNCIONANDO")
    if not response or len(response.strip()) == 0:
        raise ValueError("Respuesta vacia del LLM")
    return f"Respuesta: '{response.strip()[:60]}'"

llm_ok = all([
    check("Cliente LLM inicializado", test_llm_client_init),
    check("Llamada de prueba al LLM", test_llm_invoke),
])


# ─── TEST 5: Embeddings ──────────────────────────────────────────────────────
section("5. Embeddings -- Azure OpenAI")

def test_embeddings_client():
    from src.embeddings.embeddings_manager import EmbeddingsManager
    mgr = EmbeddingsManager()
    _ = mgr.embeddings  # fuerza lazy load
    return f"deployment={mgr._settings.azure_openai_embedding_deployment}"

def test_embed_query():
    from src.embeddings.embeddings_manager import EmbeddingsManager
    mgr = EmbeddingsManager()
    vector = mgr.embed_query("empresa con buena liquidez corriente")
    dim = mgr._settings.azure_openai_embedding_dimension
    if len(vector) == 0:
        raise ValueError("Vector vacio recibido")
    return f"dim={len(vector)}, primer_valor={vector[0]:.4f}"

def test_embed_documents():
    from src.embeddings.embeddings_manager import EmbeddingsManager
    mgr = EmbeddingsManager()
    texts = [
        "El sector agricola crecio 3.2% en 2024.",
        "La liquidez corriente de la empresa es 1.8.",
    ]
    vectors = mgr.embed_documents(texts)
    if len(vectors) != 2:
        raise ValueError(f"Se esperaban 2 vectores, llegaron {len(vectors)}")
    return f"{len(vectors)} documentos vectorizados OK"

emb_ok = all([
    check("Cliente embeddings inicializado", test_embeddings_client),
    check("embed_query (1 frase)", test_embed_query),
    check("embed_documents (2 textos)", test_embed_documents),
])


# ─── TEST 6: Chunker ─────────────────────────────────────────────────────────
section("6. Chunker (DocumentChunker)")

def test_chunker():
    from src.ingestion.chunker import DocumentChunker
    from src.ingestion.document_loader import LoadedDocument, SourceCategory, DocumentType
    chunker = DocumentChunker()
    doc = LoadedDocument(
        doc_id="test-001",
        file_name="test.txt",
        file_path="test.txt",
        doc_type=DocumentType.TXT,
        source_category=SourceCategory.INFORME_GESTION,
        country="Honduras",
        pages_or_slides=1,
        raw_text="Este es un parrafo de prueba para el chunker del sistema RAG. " * 50,
        metadata={},
    )
    chunks = chunker.chunk_document(doc)
    if len(chunks) == 0:
        raise ValueError("No se generaron chunks")
    return f"{len(chunks)} chunks generados correctamente"

check("DocumentChunker funciona", test_chunker)


# ─── TEST 7: Utilidades ──────────────────────────────────────────────────────
section("7. Utilidades (helpers)")

def test_helpers():
    from src.utils.helpers import format_currency, format_percentage, sanitize_company_name
    val = format_currency(1_500_000)
    pct = format_percentage(0.75)
    nombre = sanitize_company_name("Empresa S.A. de C.V.")
    return f"currency={val}, pct={pct}, nombre={nombre}"

check("Helpers de utilidades", test_helpers)


# ─── RESUMEN ─────────────────────────────────────────────────────────────────
section("RESUMEN FINAL")

resultados = {
    "Variables de entorno": env_ok,
    "Settings Pydantic":    settings_ok,
    "LLM Azure OpenAI":     llm_ok,
    "Embeddings Azure":     emb_ok,
}

total = len(resultados)
passed = sum(1 for v in resultados.values() if v)

for nombre, ok in resultados.items():
    icon = OK if ok else FAIL
    print(f"  {icon}  {nombre}")

print(f"\n{BOLD}  Resultado: {passed}/{total} servicios operativos{RESET}")

if passed == total:
    print(f"\n{GREEN}{BOLD}  [LISTO] Sistema listo para ejecutar el pipeline completo.{RESET}\n")
    sys.exit(0)
else:
    print(f"\n{RED}{BOLD}  [ERROR] Revisar los errores anteriores antes de continuar.{RESET}\n")
    sys.exit(1)
