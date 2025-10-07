# AI Resume Builder — Streamlit App ✨

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/streamlit-%E2%9A%A1-orange) ![FPDF](https://img.shields.io/badge/pdf-fpdf2-lightgrey) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

**One-click, ATS-friendly resumes** — A Streamlit web app that collects user data, sends structured prompts to an AI model (via OpenRouter), and returns a polished Markdown + PDF resume.  
Built for reliability, validation, and clean architecture.

---

## 🚀 Overview

This app transforms raw user input into professional, ATS-optimized resumes using AI.  
It integrates multiple layers — data validation, AI prompting, Markdown sanitization, and FPDF-based PDF rendering — within a streamlined Streamlit interface.

### Key Highlights
- Interactive Streamlit form for user inputs.
- Validation for email, phone, and LinkedIn/portfolio URLs.
- Secure OpenRouter API integration via Streamlit secrets.
- AI-generated resume in Markdown → converted to PDF.
- Handles Unicode sanitization and PDF encoding gracefully.
- User can **preview** and **download** their resume instantly.

---

## 🧠 Core Features

| Feature | Description |
|----------|--------------|
| **AI Resume Generation** | Structured prompts sent to OpenRouter to generate professional Markdown resumes. |
| **Input Validation** | Checks phone, email, and URLs for proper format and helpful feedback. |
| **Markdown-to-PDF Engine** | Custom implementation supporting headings, lists, bold/italic text, and code blocks. |
| **Error Handling** | Defensive code ensures the app never crashes — fallback PDFs are generated when issues occur. |
| **Security** | Reads API key from `st.secrets`, avoiding hard-coded credentials. |
| **Extendability** | Modular design allows swapping AI backends or improving PDF rendering without breaking the app. |

---

## 💼 Developer Achievements

- **End-to-End System Design:** Engineered a full AI → Markdown → PDF pipeline using Python and Streamlit.  
- **Robust API Integration:** Built `get_openai_client()` to handle OpenRouter authentication and errors seamlessly.  
- **Data Validation Logic:** Implemented `validate_inputs()` to catch invalid emails, phones, and URLs before model calls.  
- **Defensive Programming:** Designed `generate_pdf_from_markdown()` to sanitize text and prevent PDF encoding failures.  
- **Prompt Engineering:** Created dynamic system/user prompts for consistent, ATS-focused AI responses.  
- **Maintainable Architecture:** Clear modular boundaries between validation, model calls, and rendering logic.  
- **Production-Grade Reliability:** Implemented graceful failure modes, diagnostic PDFs, and safe error reporting in Streamlit.

---

## 🧩 Architecture Diagram

```
[Streamlit UI Form]
↓
[Validation Layer → validate_inputs()]
↓
[AI Client → get_openai_client()]
↓
[Prompt Builder + call_ai_model()]
↓
[Markdown Resume]
↓
[PDF Generator → generate_pdf_from_markdown()]
↓
[Download + Preview in Streamlit]
```

---
## ⚙️ How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/aditya452007/Resume-Builder-.git
```

### 2. Configure your API key
Create a file .streamlit/secrets.toml:
```
OPENROUTER_API_KEY = "or-xxxxxxxxxxxxxxxxxx"
```

### 3.Run the app
```
streamlit run stream.py
```

---
## 🧾 Core Functions

`get_openai_client()`:
Initializes the OpenAI client for OpenRouter. Stops the app with an error if API key is missing or invalid.

`sanitize_filename(name: str)`:
Creates filesystem-safe filenames (e.g., "John Doe" → "John_Doe").

`validate_inputs(phone, email, linkedin, portfolio)`:
Validates user inputs and returns a list of readable error messages.

`call_ai_model(user_input: dict)`:
Sends structured user data to the AI model, retrieves a Markdown resume, and sanitizes it for display.

`generate_pdf_from_markdown(md_text: str)`:
Converts Markdown resumes into printable PDFs, supporting bold, italics, lists, and code blocks.

---
##⚡ Limitations

* Lightweight Markdown-to-PDF (no tables or images).

* Minimal international phone/email validation.

* Model output variability — validation layer recommended.

* No persistent storage yet (session-only).

---

## 🔮 Future Improvements

Add HTML-to-PDF pipeline (WeasyPrint/wkhtmltopdf) for richer templates.

Enhance validation with international formats.

Implement user session storage (Google Sheets, DB).

Add logging and telemetry for debugging and analytics.

Build custom resume templates and theme options.

---

## 🧰 Tech Stack

Python 3.10+

Streamlit

OpenRouter API (OpenAI-compatible)

fpdf2

Regex + JSON for input validation

Base64 for inline PDF preview

---

## 🤝 Contributing

Pull requests are welcome — keep your PRs modular and add tests for new features.
