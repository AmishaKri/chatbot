# Setup Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd ChatBuilder
```

2. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
- Generate a secure `SECRET_KEY`
- Generate a 32-byte `ENCRYPTION_KEY` (use `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)

3. **Start all services**
```bash
docker-compose up -d
```

4. **Initialize the database**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Access the application**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Local Development Setup

### Backend

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment**
```bash
cp .env.example .env
```

5. **Start PostgreSQL and Redis** (using Docker)
```bash
docker-compose up -d postgres redis
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Start development server**
```bash
uvicorn app.main:app --reload
```

### Frontend

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Set up environment**
```bash
cp .env.example .env
```

4. **Start development server**
```bash
npm run dev
```

## API Provider Setup

### Groq

1. Sign up at https://console.groq.com
2. Create an API key
3. Add the key in the Provider Settings page

### Google Gemini

1. Sign up at https://makersuite.google.com/app/apikey
2. Create an API key
3. Add the key in the Provider Settings page

### Together.ai

1. Sign up at https://api.together.xyz
2. Create an API key
3. Add the key in the Provider Settings page

## Database Migrations

### Create a new migration
```bash
cd backend
alembic revision --autogenerate -m "description"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Troubleshooting

### Database connection issues
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify pgvector extension is installed

### Redis connection issues
- Ensure Redis is running
- Check REDIS_URL in .env

### Frontend build issues
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear build cache: `npm run build -- --force`

### Backend import errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
