from typing import List, Dict, AsyncGenerator
import httpx
from app.services.llm.base import BaseLLMProvider


class TogetherProvider(BaseLLMProvider):
    """Together.ai API provider implementation"""
    
    BASE_URL = "https://api.together.xyz/v1"
    
    PRICING = {
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.0006, "output": 0.0006},
        "meta-llama/Llama-3-70b-chat-hf": {"input": 0.0009, "output": 0.0009},
        "meta-llama/Llama-3-8b-chat-hf": {"input": 0.0002, "output": 0.0002},
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": {"input": 0.0002, "output": 0.0002},
        "Qwen/Qwen2.5-7B-Instruct-Turbo": {"input": 0.0002, "output": 0.0002},
        "togethercomputer/llama-2-70b-chat": {"input": 0.0009, "output": 0.0009},
    }

    def _get_model_candidates(self, requested_model: str) -> List[str]:
        fallback = [
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "Qwen/Qwen2.5-7B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "meta-llama/Llama-3-8b-chat-hf",
        ]
        ordered = [requested_model, *fallback]
        unique: List[str] = []
        for model in ordered:
            if model and model not in unique:
                unique.append(model)
        return unique
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Together.ai"""
        requested_model = config.get("model", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            for model in self._get_model_candidates(requested_model):
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens", 1000),
                    "stream": True,
                }

                try:
                    async with client.stream(
                        "POST",
                        f"{self.BASE_URL}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    ) as response:
                        if response.status_code == 402:
                            last_error = Exception(
                                "Together.ai billing/quota issue (402). Add credits or use a free/available model in Together account."
                            )
                            continue
                        response.raise_for_status()

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break

                                try:
                                    import json
                                    chunk = json.loads(data)
                                    if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                                        yield chunk["choices"][0]["delta"]["content"]
                                except json.JSONDecodeError:
                                    continue
                        return
                except Exception as e:
                    last_error = e
                    continue

        raise Exception(f"Together.ai API error: {str(last_error) if last_error else 'Unknown Together error'}")
    
    async def generate_response_non_streaming(
        self,
        messages: List[Dict[str, str]],
        config: Dict
    ) -> Dict:
        """Generate non-streaming response from Together.ai"""
        requested_model = config.get("model", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            for model in self._get_model_candidates(requested_model):
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens", 1000),
                    "stream": False,
                }

                try:
                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )
                    if response.status_code == 402:
                        last_error = Exception(
                            "Together.ai billing/quota issue (402). Add credits or use a free/available model in Together account."
                        )
                        continue
                    response.raise_for_status()
                    data = response.json()

                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "model": data.get("model", model),
                    }
                except Exception as e:
                    last_error = e
                    continue

        raise Exception(f"Together.ai API error: {str(last_error) if last_error else 'Unknown Together error'}")
    
    async def test_connection(self) -> bool:
        """Test Together.ai API connection"""
        test_models = [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "meta-llama/Llama-3-8b-chat-hf",
            "meta-llama/Llama-3-70b-chat-hf",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for model_name in test_models:
                try:
                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=self.headers,
                        json={
                            "model": model_name,
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 5,
                        }
                    )
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue

        return False
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for Together.ai API"""
        pricing = self.PRICING.get(model, self.PRICING["mistralai/Mixtral-8x7B-Instruct-v0.1"])
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        
        cost = (input_tokens / 1000 * pricing["input"]) + \
               (output_tokens / 1000 * pricing["output"])
        return round(cost, 6)
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count"""
        return len(text) // 4
