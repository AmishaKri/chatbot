from typing import List, Dict, AsyncGenerator
from groq import AsyncGroq
from app.services.llm.base import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    """Groq API provider implementation"""
    
    PRICING = {
        "llama3-70b-8192": {"input": 0.00059, "output": 0.00079},
        "llama3-8b-8192": {"input": 0.00005, "output": 0.00008},
        "mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
        "gemma-7b-it": {"input": 0.00007, "output": 0.00007},
    }
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncGroq(api_key=api_key)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Groq"""
        try:
            stream = await self.client.chat.completions.create(
                model=config.get("model", "llama3-70b-8192"),
                messages=messages,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 1000),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    async def generate_response_non_streaming(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> Dict:
        """Generate non-streaming response from Groq"""
        try:
            response = await self.client.chat.completions.create(
                model=config.get("model", "llama3-70b-8192"),
                messages=messages,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 1000),
                stream=False
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": response.model
            }
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test Groq API connection"""
        test_models = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "llama3-8b-8192"]
        for model_name in test_models:
            try:
                await self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5,
                )
                return True
            except Exception:
                continue
        return False
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for Groq API"""
        pricing = self.PRICING.get(model, self.PRICING["llama3-70b-8192"])
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        
        cost = (input_tokens / 1000 * pricing["input"]) + \
               (output_tokens / 1000 * pricing["output"])
        return round(cost, 6)
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count (Groq uses similar tokenization to GPT)"""
        return len(text) // 4
