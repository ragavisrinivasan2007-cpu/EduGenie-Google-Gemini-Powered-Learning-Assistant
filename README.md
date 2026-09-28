# EduGenie — Google Gemini Powered Learning Assistant

EduGenie is a small full-stack learning assistant based on the project documentation. It uses:

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python + FastAPI
- AI/LLM: Google Gemini through the official `google-genai` SDK
- Structured AI output: Pydantic schemas for quiz and learning-path JSON
- API: REST endpoints for Q&A, explanations, summaries, quizzes, and recommendations

## Features

1. Ask EduGenie a question
2. Explain a topic
3. Summarize study text
4. Generate an interactive multiple-choice quiz
5. Generate an adaptive learning path
6. Backend health check
7. Demo mode for UI/API testing without a Gemini key

## Project structure

```text
EduGenie/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       └── gemini_service.py
├── frontend/
│   ├── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 1. Install Python

Use Python 3.11 or 3.12.

Check:

```bash
python --version
```

## 2. Open the project in VS Code

Open the `EduGenie` folder:

```bash
cd EduGenie
code .
```

If `code` is not recognized, open VS Code normally and choose **File → Open Folder**.

## 3. Create a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configure Gemini

Create `.env` from `.env.example`.

Windows:

```powershell
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=YOUR_REAL_KEY_HERE
GEMINI_MODEL=gemini-3.8-flash
DEMO_MODE=false
```

Get a Gemini API key from Google AI Studio.

### Demo mode

If you want to test the complete UI/API without using Gemini:

```env
GEMINI_API_KEY=
DEMO_MODE=true
```

Demo mode returns deterministic sample responses. Set `DEMO_MODE=false` when you want real Gemini responses.

## 6. Start the application

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## 7. Test the backend

With the server running:

```bash
python -m pytest -q
```

The tests use demo mode and do not require a Gemini API key.

## 8. Test each feature manually

### Q&A

Enter:

```text
Why is the sky blue?
```

### Explanation

Enter:

```text
Quantum computing
```

### Summary

Paste a paragraph of study material.

### Quiz

Paste:

```text
The Pythagorean theorem states that for a right-angled triangle,
a² + b² = c², where c is the hypotenuse.
```

Choose 3 questions and generate the quiz.

### Learning path

Enter:

```text
SQL
```

EduGenie will generate beginner, intermediate, and advanced learning stages when appropriate.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/qna?question=...` | AI Q&A |
| GET | `/qga?question=...` | Documentation-compatible Q&A alias |
| POST | `/explain` | Explain a topic |
| POST | `/summarize` | Summarize text |
| POST | `/quiz` | Generate MCQ quiz |
| GET | `/learn/recommendations?topic=...` | Adaptive learning path |
| GET | `/health` | Health/configuration status |

## Example API calls

Q&A:

```bash
curl "http://127.0.0.1:8000/qna?question=What%20is%20photosynthesis?"
```

Explanation:

```bash
curl -X POST "http://127.0.0.1:8000/explain" ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\":\"Photosynthesis\"}"
```

Linux/macOS equivalent:

```bash
curl -X POST "http://127.0.0.1:8000/explain" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Photosynthesis"}'
```

Quiz:

```bash
curl -X POST "http://127.0.0.1:8000/quiz" \
  -H "Content-Type: application/json" \
  -d '{"text":"The Earth revolves around the Sun.","question_count":3}'
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'google'`

Activate `.venv` and run:

```bash
pip install -r requirements.txt
```

### `GEMINI_API_KEY is not configured`

Check `.env`. It must be in the project root beside `requirements.txt`.

### Gemini model error

Change:

```env
GEMINI_MODEL=gemini-3.8-flash
```

to another model available to your Gemini API project, for example:

```env
GEMINI_MODEL=gemini-2.5-flash
```

Then restart Uvicorn.

### Port 8000 already in use

Run:

```bash
python -m uvicorn backend.main:app --reload --port 8080
```

Then open `http://127.0.0.1:8080`.

## Security notes

- Never put your Gemini API key in `frontend/app.js` or `index.html`.
- Keep the key only in `.env`.
- `.env` is excluded by `.gitignore`.
- The browser talks to FastAPI; FastAPI talks to Gemini. The API key never needs to reach the browser.
