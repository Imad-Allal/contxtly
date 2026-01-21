# Contxtly

Contextual translator browser extension.

## Setup

```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```env
GROQ_API_KEY=your-key-here
```

Get your key at [console.groq.com](https://console.groq.com)

## Run

```bash
uvicorn main:app --reload
```

## Test

```bash
# Simple translation
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "hello", "target_lang": "de"}'

# Smart translation (with context + examples)
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "ephemeral", "context": "The ephemeral nature of cherry blossoms", "target_lang": "de", "mode": "smart"}'
```
