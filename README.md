# Requirement → API Copilot 🚀

Requirement → API Copilot is a powerful full-stack tool that transforms messy product requirements into structured technical specifications. Using Google Gemini 2.0, it generates modules, user stories, API endpoints, and database schemas in seconds.

## ✨ Features

- **AI-Powered Generation**: Deep analysis of raw text into technical blueprints.
- **Refinement Loop**: Chat-based interface to iterate on generated specs.
- **Robust Integration**: Built with FastAPI and React, optimized for Gemini 2.0.
- **Technical Specs**:
  - 📦 **Modules**: Clear functional breakdown.
  - 📖 **User Stories**: BDD-style stories with acceptance criteria.
  - 🔌 **API Endpoints**: Full RESTful definitions.
  - 🗄️ **Database Schema**: Relational tables and logic.
- **Dark Mode**: Premium glass-morphism aesthetic.

## 🛠️ Tech Stack

- **Frontend**: React 19, TypeScript, Tailwind CSS, Vite
- **Backend**: Python 3.9+, FastAPI, Pydantic
- **AI Engine**: Google Gemini 2.0 (with exponential backoff handling)

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- Google AI Studio API Key (Gemini)

### 1. Backend Setup
1. Navigate to the backend: `cd backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure Environment:
   ```bash
   cp .env.example .env
   ```
4. Set your `GEMINI_API_KEY` in `.env`.
5. Run the server: `python -m uvicorn main:app --reload`

### 2. Frontend Setup
1. Navigate to the frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Start the UI: `npm run dev`

## 📖 Usage
1. Enter your product idea in the text area.
2. Click **Generate Specification**.
3. Use the tabs to explore different technical layers.
4. Click **Refine Spec** to adjust details or add missing features.

---
*Created with ❤️ for builders.*
