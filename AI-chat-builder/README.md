# Multi-Provider AI Chat Builder SaaS

A production-ready multi-tenant SaaS platform enabling businesses to create custom AI chatbots with multiple AI providers (Groq, Gemini, Together.ai), featuring RAG capabilities, embeddable widgets, and comprehensive analytics.

## 🚀 Features

- **Multi-Provider Support**: Switch between Groq, Google Gemini, and Together.ai
- **RAG System**: Upload documents for knowledge-based responses
- **Embeddable Widget**: Deploy chatbots on any website
- **Multi-Tenant**: Complete organization and user management
- **Analytics Dashboard**: Track usage, costs, and performance
- **Real-time Streaming**: Stream AI responses in real-time
- **Role-Based Access**: Owner, Admin, and Agent roles

## 🏗️ Architecture

```
Frontend (React TS) → FastAPI → AI Provider Layer → Vector DB → PostgreSQL
                                      ↓
                          [Groq | Gemini | Together.ai]
```

## 🛠️ Tech Stack

### Frontend
- React + TypeScript
- Tailwind CSS
- React Query
- Zustand
- Axios
- shadcn/ui

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL (with pgvector)
- Redis
- JWT Authentication

### AI Providers
- Groq API
- Google Gemini API
- Together.ai API

## 📦 Installation

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd ChatBuilder
```

2. Copy environment files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Configure your environment variables in `.env` files

4. Start with Docker Compose:
```bash
docker-compose up -d
```

5. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🔧 Development Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs)
- [Architecture Guide](./docs/architecture.md)
- [Deployment Guide](./docs/deployment.md)
- [Widget Integration](./docs/widget-integration.md)

## 🔐 Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/chatbuilder
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

## 🐳 Docker Deployment

```bash
docker-compose up -d --build
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.
