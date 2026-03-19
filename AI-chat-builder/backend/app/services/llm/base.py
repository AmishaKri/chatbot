from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator, Optional


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from the LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Configuration dict with model, temperature, max_tokens, etc.
            
        Yields:
            Chunks of the response text
        """
        pass
    
    @abstractmethod
    async def generate_response_non_streaming(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> Dict:
        """
        Generate non-streaming response from the LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Configuration dict with model, temperature, max_tokens, etc.
            
        Returns:
            Dict with 'content', 'tokens_used', 'model'
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the API key is valid"""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for given tokens and model"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
