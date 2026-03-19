import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"


USERS_COLLECTION = "users"
