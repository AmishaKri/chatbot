import enum


class DocumentStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


DOCUMENTS_COLLECTION = "documents"
