from typing import List, Dict, AsyncGenerator
import httpx
from app.services.llm.base import BaseLLMProvider


class GrokProvider(BaseLLMProvider):
    """xAI Grok API provider implementation (OpenAI-compatible)."""

    CHAT_COMPLETIONS_ENDPOINTS = [
        "https://api.x.ai/v1/chat/completions",
    ]
    MODELS_ENDPOINTS = [
        "https://api.x.ai/v1/models",
    ]

    PRICING = {
        "grok-4-latest": {"input": 0.005, "output": 0.015},
        "grok-2-latest": {"input": 0.005, "output": 0.015},
        "grok-2-beta": {"input": 0.005, "output": 0.015},
    }

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: Dict,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Grok."""
        last_error: Exception | None = None
        payload = {
            "model": config.get("model", "grok-2-latest"),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1000),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for endpoint in self.CHAT_COMPLETIONS_ENDPOINTS:
                try:
                    async with client.stream(
                        "POST",
                        endpoint,
                        headers=self.headers,
                        json=payload,
                    ) as response:
                        response.raise_for_status()

                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue

                            data = line[6:]
                            if data == "[DONE]":
                                break

                            try:
                                import json

                                chunk = json.loads(data)
                                text = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                                if text:
                                    yield text
                            except Exception:
                                continue
                        return
                except Exception as e:
                    last_error = e
                    continue

        raise Exception(f"Grok API error: {str(last_error) if last_error else 'Unable to reach Grok endpoint'}")

    async def generate_response_non_streaming(
        self,
        messages: List[Dict[str, str]],
        config: Dict,
    ) -> Dict:
        """Generate non-streaming response from Grok."""
        payload = {
            "model": config.get("model", "grok-2-latest"),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1000),
            "stream": False,
        }
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            for endpoint in self.CHAT_COMPLETIONS_ENDPOINTS:
                try:
                    response = await client.post(
                        endpoint,
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()

                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "model": data.get("model", payload["model"]),
                    }
                except Exception as e:
                    last_error = e
                    continue

        raise Exception(f"Grok API error: {str(last_error) if last_error else 'Unable to reach Grok endpoint'}")

    async def test_connection(self) -> bool:
        """Test Grok API connection."""
        async with httpx.AsyncClient(timeout=20.0) as client:
            discovered_models: List[str] = []

            # Primary check: validate API key via model listing endpoint.
            for endpoint in self.MODELS_ENDPOINTS:
                try:
                    models_response = await client.get(endpoint, headers=self.headers)
                    if models_response.status_code == 200:
                        payload = models_response.json()
                        discovered_models = [
                            item.get("id") for item in payload.get("data", []) if item.get("id")
                        ]
                        if discovered_models:
                            return True
                except Exception:
                    continue

            # Fallback: attempt a minimal completion across known and discovered models.
            test_models = discovered_models + ["grok-2-latest", "grok-beta", "grok-2"]
            for endpoint in self.CHAT_COMPLETIONS_ENDPOINTS:
                for model in test_models:
                    try:
                        response = await client.post(
                            endpoint,
                            headers=self.headers,
                            json={
                                "model": model,
                                "messages": [{"role": "user", "content": "test"}],
                                "max_tokens": 5,
                            },
                        )
                        if response.status_code == 200:
                            return True
                    except Exception:
                        continue

        return False

    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for Grok API."""
        pricing = self.PRICING.get(model, self.PRICING["grok-2-latest"])
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4

        cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        return round(cost, 6)

    def count_tokens(self, text: str) -> int:
        """Approximate token count."""
        return len(text) // 4
