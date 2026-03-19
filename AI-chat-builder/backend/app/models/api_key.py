import enum


class ProviderType(str, enum.Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    TOGETHER = "together"


API_KEYS_COLLECTION = "api_keys"
