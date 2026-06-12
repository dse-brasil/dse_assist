from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Classe base abstrata para provedores de IA.

    Para adicionar um novo provedor:
    1. Crie um arquivo em ai_providers/ (ex: meu_provider.py)
    2. Herde desta classe e implemente os métodos abstratos
    3. Adicione o provedor no factory em ai_providers/__init__.py
    4. Configure AI_PROVIDER=meu_provider no .env
    """

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """
        Gera uma resposta a partir de um prompt.

        Args:
            prompt: A mensagem/pergunta do usuário.
            system_prompt: Instruções de sistema para o modelo.
            **kwargs: Metadados adicionais para fins de segurança/log (ex: user_id, channel).

        Returns:
            Texto gerado pelo modelo.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome amigável do provedor (ex: 'Google Gemini')."""
        pass
