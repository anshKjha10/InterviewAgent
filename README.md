# 🎯 PrepAI — AI-Powered Interview Preparation Assistant

**PrepAI** is a modern, full-stack web application designed to help job seekers practice mock interviews, analyze their resumes, receive instant per-answer evaluations, and follow a personalized 4-week study roadmap. 

Powered by **Flask**, **SQLite**, and **Groq LLaMA 3.3 70B**, PrepAI delivers a fast, responsive, and resume-anchored interview practice experience.

---

## 🌟 Key Features

* **📄 Instant PDF Resume Parsing**: Upload any PDF resume to extract skills, experience, education, and candidate summary using `pypdf`.
* **⚡ DB-Backed Analysis Caching**: Resume analysis results are cached in SQLite for instant (`<1ms`) reloads without re-calling the LLM.
* **🎯 Resume-Grounded Mock Interviews**: The AI interviewer asks questions **directly anchored in your resume's listed projects, internships, experience, and tech stack**.
* **🔢 Structured 5-Question Sessions**: Every mock interview follows a fixed, predictable 5-question progression with live progress tracking (`Question 1 of 5`).
* **🎤 3 Specialized Interview Modes**:
  * **HR Interview**: Behavioral STAR-method questions tailored to your past internships and experiences.
  * **Technical Interview**: Deep technical probing into your specific tech stack, system design choices, and architecture.
  * **Coding Interview**: Domain-relevant algorithmic problems calibrated to your background.
* **⚡ Real-Time Streaming Responses**: Powered by Groq's low-latency LLaMA 3.3 70B engine using Server-Sent Events (SSE).
* **📊 Per-Answer Evaluation Cards**: Instant scoring (`1-10`), strengths, and actionable improvement feedback after each submitted answer.
* **🗺️ Personalized 4-Week Study Roadmap**: AI-generated weekly study timeline targeting your specific gaps and interview weaknesses.
* **🐳 Docker Containerization**: Fully packaged with `Dockerfile`, `.dockerignore`, and `docker-compose.yml` for effortless container deployment.
* **💎 Sleek Dark Glassmorphism UI**: Built with Vanilla CSS design tokens and **Lucide Icons** for a premium aesthetic.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Flask 3.1.3 (Blueprint Architecture, SSE Streaming) |
| **LLM Provider** | Groq SDK (`llama-3.3-70b-versatile`) |
| **PDF Extraction** | `pypdf` (Pure Python PDF parsing) |
| **Database** | SQLite3 (Resumes, Sessions, Questions, Answers, Analysis Cache) |
| **Containerization** | Docker & Docker Compose (`python:3.11-slim`) |
| **Frontend** | HTML5, Vanilla CSS3 (Glassmorphism), ES6+ JavaScript |
| **Icons** | Lucide Icons (`lucide-react` / `lucide` SVG) |
| **Environment Config** | `python-dotenv` |

---

## 📁 Project Structure

```
d:\ProjectIBM\
├── app.py                  # Main Flask application entry point & DB initializer
├── config.py               # Configuration management & environment variable loader
├── requirements.txt        # Python package dependencies
├── Dockerfile              # Docker container build specification
├── .dockerignore           # Files excluded from Docker image build
├── docker-compose.yml      # Multi-container / Docker Compose configuration
├── .env                    # Environment secrets (GROQ_API_KEY, secret keys)
├── .gitignore              # Git ignore rules
├── interview_prep.db       # SQLite database (auto-created on startup)
│
├── services/               # Core business logic services
│   ├── db.py               # SQLite schema, CRUD operations & cache management
│   ├── llm.py              # Groq LLM API integrations (streaming & non-streaming)
│   └── pdf_parser.py       # PDF text extraction module via pypdf
│
├── routes/                 # Flask REST & SSE Blueprints
│   ├── resume.py           # Resume upload, parsing & cached analysis endpoints
│   ├── interview.py        # Mock interview orchestration & SSE answer streaming
│   ├── feedback.py         # Session score breakdown & feedback aggregation
│   └── roadmap.py          # AI study roadmap generation route
│
├── prompts/                # Modular system prompt templates
│   ├── resume_analyzer.txt # Prompt for structured JSON resume analysis
│   ├── hr_interviewer.txt   # HR behavioral interviewer persona
│   ├── tech_interviewer.txt # Technical system design interviewer persona
│   ├── coding_interviewer.txt# Coding specialist interviewer persona
│   ├── evaluator.txt       # Per-answer scoring & evaluation prompt
│   └── roadmap_planner.txt # 4-week study plan generation prompt
│
└── static/                 # Frontend assets & single-page HTML templates
    ├── index.html          # Landing page & feature showcase
    ├── dashboard.html      # Prep overview, stats cards & recent sessions
    ├── upload.html         # Resume upload drag-and-drop & step progress tracker
    ├── analysis.html       # Profile analysis view (skills, strengths, roles)
    ├── interview.html      # Live 5-question mock interview chat UI
    ├── feedback.html       # Session score ring breakdown & question feedback
    ├── roadmap.html        # 4-week study roadmap timeline
    ├── css/
    │   └── style.css       # Complete dark glassmorphism styling system
    └── js/
        └── main.js         # API helpers, storage, toast notifications, Lucide icon handler
```

---

## 🐳 Containerization & Docker Setup

You can run the application as a Docker container using either **Docker CLI** or **Docker Compose**.

### Option A: Using Docker Compose (Recommended)

1. Make sure you have a `.env` file in the project root containing your Groq API key:
   ```ini
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   FLASK_SECRET_KEY=supersecretkey123
   ```

2. Build and start the container:
   ```bash
   docker compose up -d --build
   ```

3. Open **[http://localhost:5000](http://localhost:5000)** in your browser.

4. To stop the container:
   ```bash
   docker compose down
   ```

---

### Option B: Using Docker CLI Directly

1. Build the Docker image:
   ```bash
   docker build -t prepai-app .
   ```

2. Run the Docker container with your `.env` file:
   ```bash
   docker run -d \
     --name prepai_container \
     -p 5000:5000 \
     --env-file .env \
     prepai-app
   ```

3. Access the app at **[http://localhost:5000](http://localhost:5000)**.

4. Stop and remove the container:
   ```bash
   docker stop prepai_container && docker rm prepai_container
   ```

---

## 🚀 Standard Local Setup (Without Docker)

### 1. Prerequisites
- **Python 3.10** or higher installed on your system.
- A free **Groq API Key** (Get one at [console.groq.com/keys](https://console.groq.com/keys)).

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create or edit `.env` in the project root:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
FLASK_SECRET_KEY=supersecretkey123
FLASK_DEBUG=true
DB_PATH=interview_prep.db
```

### 5. Run the Application
```bash
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser!

---

## 🔌 API Route Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload-resume` | Upload PDF resume, extract text, and store in DB |
| `GET` | `/api/resume-summary` | Fetch cached JSON analysis or generate via Groq LLM |
| `GET` | `/api/resume-summary/stream` | Stream resume analysis via Server-Sent Events (SSE) |
| `POST` | `/api/mock-interview/start` | Initialize 5-question session & return Q1 grounded in resume |
| `POST` | `/api/mock-interview/answer` | Submit candidate answer → stream SSE evaluation + Q{N+1} |
| `GET` | `/api/history` | Retrieve full Q&A transcript for a given session |
| `GET` | `/api/sessions` | List all interview sessions and average scores |
| `GET` | `/api/feedback` | Retrieve complete score breakdown & evaluation for a session |
| `GET` | `/api/roadmap` | Generate 4-week study roadmap based on resume & feedback |

---

## 📄 License
This project is open-source and available under the **MIT License**.
