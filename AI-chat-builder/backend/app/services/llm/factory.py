from app.services.llm.base import BaseLLMProvider
from app.services.llm.grok_provider import GrokProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.together_provider import TogetherProvider


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    PROVIDERS = {
        "together": TogetherProvider,
        "grok": GrokProvider,
        "gemini": GeminiProvider,
        "groq": GroqProvider,
    }
    
    @staticmethod
    def get_provider(provider_name: str, api_key: str) -> BaseLLMProvider:
        """
        Get an instance of the specified provider
        
        Args:
            provider_name: Name of the provider (groq, gemini, together)
            api_key: API key for the provider
            
        Returns:
            Instance of the provider
            
        Raises:
            ValueError: If provider_name is not supported
        """
        provider_class = LLMProviderFactory.PROVIDERS.get(provider_name.lower())
        
        if not provider_class:
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers: {', '.join(LLMProviderFactory.PROVIDERS.keys())}"
            )
        
        return provider_class(api_key)
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available provider names"""
        return list(LLMProviderFactory.PROVIDERS.keys())
