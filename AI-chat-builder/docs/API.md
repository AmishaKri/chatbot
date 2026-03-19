# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your-token>
```

## Endpoints

### Authentication

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "organization_name": "My Company",
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {...},
  "organization": {...}
}
```

### Chatbots

#### List Chatbots
```http
GET /chatbots/
Authorization: Bearer <token>
```

#### Create Chatbot
```http
POST /chatbots/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Customer Support Bot",
  "system_prompt": "You are a helpful customer support assistant.",
  "welcome_message": "Hello! How can I help you today?",
  "tone": "professional",
  "provider": "groq",
  "model_name": "llama3-70b-8192",
  "temperature": 0.7,
  "max_tokens": 1000,
  "streaming_enabled": true
}
```

#### Get Chatbot
```http
GET /chatbots/{chatbot_id}
Authorization: Bearer <token>
```

#### Update Chatbot
```http
PUT /chatbots/{chatbot_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": true
}
```

#### Delete Chatbot
```http
DELETE /chatbots/{chatbot_id}
Authorization: Bearer <token>
```

### API Keys

#### List API Keys
```http
GET /api-keys/
Authorization: Bearer <token>
```

#### Add API Key
```http
POST /api-keys/
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "groq",
  "api_key": "gsk_...",
  "is_default": true
}
```

#### Test API Key
```http
POST /api-keys/{key_id}/test
Authorization: Bearer <token>
```

### Chat

#### Send Message
```http
POST /chat/{chatbot_id}/message
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "session_id": "optional-session-id",
  "user_identifier": "optional-user-id"
}
```

Response: Server-Sent Events (SSE) stream

### Knowledge Base

#### Upload Document
```http
POST /knowledge/upload?chatbot_id={chatbot_id}
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file-data>
```

#### List Documents
```http
GET /knowledge/documents?chatbot_id={chatbot_id}
Authorization: Bearer <token>
```

### Analytics

#### Get Overview
```http
GET /analytics/overview
Authorization: Bearer <token>
```

#### Get Provider Usage
```http
GET /analytics/usage?days=30
Authorization: Bearer <token>
```

#### Get Cost Breakdown
```http
GET /analytics/costs?days=30
Authorization: Bearer <token>
```

### Public Endpoints

#### Public Chat (for embedded widget)
```http
POST /public/chat/{chatbot_id}
Content-Type: application/json

{
  "message": "Hello",
  "session_id": "optional-session-id"
}
```

#### Get Bot Config
```http
GET /public/bot/{chatbot_id}/config
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- Public endpoints: 100 requests/minute per IP
- Authenticated endpoints: 1000 requests/minute per organization

## Streaming Responses

Chat endpoints return Server-Sent Events (SSE):

```
data: {"type": "chunk", "content": "Hello", "session_id": "..."}

data: {"type": "chunk", "content": " there!", "session_id": "..."}

data: {"type": "done", "session_id": "...", "tokens_used": 42}
```
