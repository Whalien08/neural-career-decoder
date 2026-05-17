# ⚡ Neural Career Decoder // UPLINK

![Status](https://img.shields.io/badge/Status-Operational-22d3ee?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.0-blue?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-3.0-38B2AC?style=for-the-badge&logo=tailwind-css)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-8E75B2?style=for-the-badge&logo=google)

> **Accessing GitHub Career Core...** > A cyberpunk-themed, full-stack analytics dashboard that translates raw GitHub telemetry into a professional industry alignment matrix. 

### 🌐 Live Uplink (Deployment)
Access the live application hosted on Google Cloud Run here:
**[Launch Neural Decoder](https://github-card-frontend-236326372885.asia-south1.run.app)**

![Dashboard View](https://github.com/user-attachments/assets/3a151c78-3482-4156-b11c-91c417a530f1)
---

## 🚀 System Overview

The Neural Decoder is a high-density profiling tool designed to evaluate software engineering portfolios. It fetches public GitHub data, processes repository languages, calculates algorithmic impact scores, and utilizes Generative AI to render a secure "Neural Identity" card that can be exported as a mini-resume.

### ⚙️ Core Features
* **Generative AI Persona:** Integrates Google's Gemini AI to analyze raw coding data and synthesize a highly accurate developer personality profile.
* **Industrial Alignment Matrix:** Analyzes repository language distribution and intelligently maps the developer to specific real-world industry domains.
* **Bounty Calculation (CR):** A custom scoring algorithm that calculates a developer's base impact using repository count, followers, and total stargazers.
* **Neural Identity Export:** Utilizes `html2canvas` to bypass browser security constraints, allowing users to safely download their generated profile as a high-resolution PNG card.

---

## 🛠️ Architecture & Tech Stack

This project uses a decoupled architecture for maximum speed and localized deployment.

**Frontend (Client Node)**
* **React 18** (Standalone Babel injection for rapid deployment)
* **Tailwind CSS** (JIT compiler via CDN for neon-glassmorphism UI)
* **HTML2Canvas** (For secure DOM-to-Image rendering)

**Backend (Processing Core)**
* **Python 3 & FastAPI** (High-performance async API endpoints)
* **Google Gemini API** (Generative AI processing)
* **GitHub REST API** (Data fetching and parsing)
* **Google Cloud Run** (Serverless container deployment)

---

## 🔌 Initialization Sequence (Local Setup)

To run the Neural Decoder on your local machine, follow these steps:

### 1. Configure the Environment
Clone the repository and create a `.env` file in the main directory to hold your API keys:
```env
GITHUB_TOKEN=your_github_token_here
GOOGLE_API_KEY=your_gemini_key_here
