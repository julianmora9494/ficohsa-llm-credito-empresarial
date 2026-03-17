"""
Gestión del cliente LLM usando Azure OpenAI GPT-4o.
Centraliza la inicialización y configuración del modelo de lenguaje.
"""
from typing import Optional

from langchain_openai import AzureChatOpenAI

from src.config.settings import Settings, get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMManager:
    """
    Manager para el cliente Azure OpenAI.
    Implementa lazy loading para inicializar el cliente solo cuando se necesita.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Inicializa el manager sin conectar al cliente todavía.

        Args:
            settings: Configuración del sistema. Si es None, usa el singleton global.
        """
        self._settings = settings or get_settings()
        self._client: Optional[AzureChatOpenAI] = None
        logger.info("LLMManager inicializado (cliente en lazy load)")

    @property
    def client(self) -> AzureChatOpenAI:
        """
        Retorna el cliente AzureChatOpenAI, inicializándolo si es necesario.
        Patrón lazy loading: el cliente se crea solo cuando se usa por primera vez.
        """
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> AzureChatOpenAI:
        """Construye e inicializa el cliente Azure OpenAI."""
        logger.info(
            "Inicializando cliente Azure OpenAI: deployment=%s, api_version=%s",
            self._settings.azure_openai_deployment_name,
            self._settings.azure_openai_api_version,
        )
        return AzureChatOpenAI(
            azure_deployment=self._settings.azure_openai_deployment_name,
            azure_endpoint=self._settings.azure_openai_endpoint,
            api_key=self._settings.azure_openai_key,
            api_version=self._settings.azure_openai_api_version,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            top_p=self._settings.llm_top_p,
        )

    def invoke(self, prompt: str) -> str:
        """
        Invoca el LLM con un prompt y retorna la respuesta como texto.

        Args:
            prompt: Prompt completo a enviar al modelo.

        Returns:
            Texto de respuesta del modelo.
        """
        logger.debug("Invocando LLM con prompt de %d caracteres", len(prompt))
        response = self.client.invoke(prompt)
        return response.content

    def get_client_for_chain(self) -> AzureChatOpenAI:
        """
        Retorna el cliente para usar en cadenas LangChain (LCEL, etc).

        Returns:
            Instancia de AzureChatOpenAI lista para chaining.
        """
        return self.client
