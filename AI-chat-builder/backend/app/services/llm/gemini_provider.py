from typing import List, Dict, AsyncGenerator
import google.generativeai as genai
import httpx
from app.services.llm.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider implementation"""

    MODEL_ALIASES = {
        "gemini-1.5-pro": "gemini-1.5-pro-latest",
        "gemini-1.5-flash": "gemini-1.5-flash-latest",
        "gemini-pro": "gemini-1.5-flash-latest",
    }
    
    PRICING = {
        "gemini-1.5-pro-latest": {"input": 0.00125, "output": 0.00375},
        "gemini-1.5-flash-latest": {"input": 0.000075, "output": 0.0003},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.00375},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
    }
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Gemini"""
        system_instruction = None
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                chat_messages.append(msg)

        prompt = self._format_messages(chat_messages, system_instruction)
        generation_config = genai.types.GenerationConfig(
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 1000),
        )

        requested_model = config.get("model", "gemini-1.5-flash-latest")
        model_candidates = self._get_model_candidates(requested_model)
        last_error: Exception | None = None

        for model_name in model_candidates:
            try:
                model = self._build_model(model_name, system_instruction)
                response = await model.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                    stream=True
                )

                async for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"Gemini API error: {str(last_error) if last_error else 'Unknown Gemini error'}")
    
    async def generate_response_non_streaming(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> Dict:
        """Generate non-streaming response from Gemini"""
        system_instruction = None
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                chat_messages.append(msg)

        prompt = self._format_messages(chat_messages, system_instruction)
        generation_config = genai.types.GenerationConfig(
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 1000),
        )

        requested_model = config.get("model", "gemini-1.5-flash-latest")
        model_candidates = self._get_model_candidates(requested_model)
        last_error: Exception | None = None

        for model_name in model_candidates:
            try:
                model = self._build_model(model_name, system_instruction)
                response = await model.generate_content_async(
                    prompt,
                    generation_config=generation_config
                )

                tokens_used = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else self.count_tokens(response.text)

                return {
                    "content": response.text,
                    "tokens_used": tokens_used,
                    "model": model_name
                }
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"Gemini API error: {str(last_error) if last_error else 'Unknown Gemini error'}")

    def _normalize_model_name(self, model_name: str) -> str:
        clean_name = (model_name or "").strip()
        if clean_name.startswith("models/"):
            clean_name = clean_name.replace("models/", "", 1)
        return self.MODEL_ALIASES.get(clean_name, clean_name)

    def _get_model_candidates(self, requested_model: str) -> List[str]:
        preferred = self._normalize_model_name(requested_model)
        fallback_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro-latest",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

        ordered = [preferred, *fallback_models]
        unique_models: List[str] = []
        for item in ordered:
            normalized = self._normalize_model_name(item)
            if normalized and normalized not in unique_models:
                unique_models.append(normalized)
        return unique_models

    def _build_model(self, model_name: str, _system_instruction: str | None):
        return genai.GenerativeModel(model_name)
    
    def _format_messages(self, messages: List[Dict[str, str]], system_instruction: str | None = None) -> str:
        """Format messages for Gemini"""
        formatted = []
        if system_instruction:
            formatted.append(f"System: {system_instruction}")
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n\n".join(formatted)
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection"""
        # Primary check: validate API key independently of specific model availability.
        model_endpoints = [
            "https://generativelanguage.googleapis.com/v1beta/models",
            "https://generativelanguage.googleapis.com/v1/models",
        ]

        async with httpx.AsyncClient(timeout=20.0) as client:
            for endpoint in model_endpoints:
                try:
                    response = await client.get(endpoint, params={"key": self.api_key})
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue

        # Fallback: try lightweight generations across common model names.
        test_models = self._get_model_candidates("gemini-1.5-flash-latest")
        for model_name in test_models:
            try:
                model = genai.GenerativeModel(model_name)
                await model.generate_content_async("test")
                return True
            except Exception:
                continue
        return False
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for Gemini API"""
        pricing_model = self._normalize_model_name(model)
        pricing = self.PRICING.get(pricing_model, self.PRICING["gemini-1.5-pro-latest"])
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        
        cost = (input_tokens / 1000 * pricing["input"]) + \
               (output_tokens / 1000 * pricing["output"])
        return round(cost, 6)
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count"""
        return len(text) // 4
