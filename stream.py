import re
import streamlit as st
import json
from openai import OpenAI
import base64
from fpdf import FPDF # Using the standard fpdf library


# --- PROFESSIONAL: API Key Configuration via Streamlit Secrets ---
try:
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
except (FileNotFoundError, KeyError):
    st.error("🔴 ERROR: OPENROUTER_API_KEY not found. Please add it to your Streamlit secrets.")
    st.info("Create a file at .streamlit/secrets.toml and add the line: OPENROUTER_API_KEY = 'your_key_here'")
    st.stop()


# --- API Client Initialization ---
def get_openai_client():
    """Initializes and returns the OpenAI client for OpenRouter."""
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        return client
    except Exception as e:
        st.error(f"🔴 ERROR: Could not initialize OpenAI client: {e}")
        st.stop()


# --- Page Config (must be the first Streamlit command) ---
st.set_page_config(page_title="AI Resume Builder", layout="centered")

st.title("📄 AI Resume Builder")
st.write("Fill in your details below. The AI will process them into a polished, ATS-friendly resume.")


# --- Helper Functions ---
def sanitize_filename(name: str) -> str:
    """Creates a safe, valid filename from a user's name."""
    name = (name or "").strip()
    safe_name = re.sub(r"[^\w\-. ]", "", name).replace(" ", "_")
    return safe_name or "resume"

def validate_inputs(phone: str, email: str, linkedin: str, portfolio: str):
    """Validates the format of key personal info fields."""
    errors = []
    phone_digits = re.sub(r"\D", "", (phone or ""))
    if phone and not re.fullmatch(r"\d{10}", phone_digits):
        errors.append("📞 Phone number must contain exactly 10 digits.")
    
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", (email or "").strip()):
        errors.append("✉️ Please enter a valid email address.")
    
    if linkedin and not (linkedin.strip().startswith("https://www.linkedin.com/") or linkedin.strip().startswith("https://linkedin.com/")):
        errors.append("🔗 LinkedIn URL must start with 'https://linkedin.com/'.")
        
    if portfolio and not (portfolio.strip().startswith("http://") or portfolio.strip().startswith("https://")):
        errors.append("💻 Portfolio/GitHub URL must start with 'http://' or 'https://'.")
            
    return errors


def call_ai_model(user_input: dict):
    """Calls the AI model via OpenRouter to generate resume markdown."""
    client = get_openai_client()
    model = "z-ai/glm-4.5-air:free"

    system_prompt = (
        "You are a world-class Career Strategist and Resume Analyst. Your task is to transform a "
        "candidate's raw information into a high-impact, professional resume in Markdown format. "
        "Focus on using action verbs, quantifying achievements, and structuring the content logically."
    )
    
    user_prompt = (
        "Analyze the following JSON data and generate an enhanced, professional resume in Markdown format. "
        "You MUST expand on the provided information to make the resume more comprehensive. Add relevant technical and "
        "professional skills based on the candidate's profile. Elaborate on the project and experience bullet points "
        "with more plausible details. Add a 'Personal Details' section with fields like 'Languages' or 'Nationality' if appropriate.\n\n"
        "**CRITICAL INSTRUCTION: Your entire response must ONLY be the raw Markdown content of the resume.** "
        "Do not include any introductory sentences, explanations, or closing remarks. The very first line of your "
        "output must be the candidate's name in Markdown (e.g., '# Aaditya Thakur').\n\n"
        f"Candidate Data:\n```json\n{json.dumps(user_input, indent=2)}\n```"
    )

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    try:
        response = client.chat.completions.create(model=model, messages=messages)
        # Clean up any potential markdown code fences the model might add around the whole text
        content = response.choices[0].message.content
        if content.startswith("```markdown"):
            content = content.strip("```markdown\n")
        if content.startswith("```"):
            content = content.strip("```\n")
        return content
    except Exception as e:
        st.error(f"🔴 An error occurred while contacting the AI model: {e}")
        return None

def generate_pdf_from_markdown(md_text: str) -> str:
    """
    A hardened PDF generator using standard fpdf that sanitizes text for latin-1
    compatibility and supports markdown styling including headings, lists, code blocks,
    and inline bold/italic with word wrapping.
    """
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", '', 12)

        def sanitize_for_fpdf(s: str) -> str:
            # [This helper function remains unchanged]
            s = s or ""
            repl = {
                '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
                '\u2013': '-', '\u2014': '--', '\u2022': chr(149),
                '\u2026': '...', '\u00a9': '(c)', '\u00ae': '(R)',
                '\u2122': 'TM', '\u20ac': 'EUR', '\u00a3': 'GBP',
            }
            for k, v in repl.items():
                s = s.replace(k, v)
            return s.encode('latin-1', 'ignore').decode('latin-1')

        def write_wrapping_styled_text(text: str, indent: int = 0):
            """
            NEW: This function handles both inline styling (bold/italic) and word wrapping.
            It processes text word by word, checking if it fits on the current line.
            """
            # Set initial X position for the line, considering indentation
            initial_x = pdf.get_x() + indent
            pdf.set_x(initial_x)
            
            parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
            for part in parts:
                style = ''
                content = part
                if part.startswith('**') and part.endswith('**'):
                    style = 'B'
                    content = part[2:-2]
                elif part.startswith('*') and part.endswith('*'):
                    style = 'I'
                    content = part[1:-1]
                
                pdf.set_font("Arial", style)
                sanitized_content = sanitize_for_fpdf(content)

                # Process word by word for wrapping
                for word in sanitized_content.split(' '):
                    word_width = pdf.get_string_width(word + ' ')
                    if pdf.get_x() + word_width > pdf.w - pdf.r_margin:
                        pdf.ln()
                        pdf.set_x(initial_x) # Re-apply indent on new line
                    pdf.write(5, word + ' ')
            pdf.ln()

        # [Code block handling and other parts of the function remain largely the same]
        in_code_block = False
        code_buffer = []

        for line in md_text.splitlines():
            # [Code block logic is unchanged]
            if line.strip().startswith("```"):
                if not in_code_block: in_code_block = True
                else:
                    in_code_block = False
                    pdf.set_font("Courier", size=10)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.multi_cell(0, 5, sanitize_for_fpdf("\n".join(code_buffer)), border=0, fill=True)
                    pdf.set_font("Arial", '', 12)
                    pdf.set_fill_color(255, 255, 255)
                    pdf.ln(4)
                    code_buffer = []
                continue
            if in_code_block:
                code_buffer.append(line)
                continue

            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Headings H1-H6 (using multi_cell is fine as they are uniformly styled)
            heading_match = re.match(r'^(#{1,6})\s+(.*)$', stripped_line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                sizes = {1: 18, 2: 16, 3: 14, 4: 12, 5: 11, 6: 10}
                pdf.set_font("Arial", 'B', sizes.get(level, 12))
                pdf.multi_cell(0, 7 + (6 - level), sanitize_for_fpdf(text))
                pdf.ln(2)
                pdf.set_font("Arial", '', 12)
                continue

            # [Horizontal Rule logic is unchanged]
            if re.match(r'^[\-\*_]{3,}\s*$', stripped_line):
                pdf.ln(2)
                pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                pdf.ln(2)
                continue
            
            # --- CORRECTED LIST AND PARAGRAPH HANDLING ---

            # Unordered List
            ul_match = re.match(r'^\s*[\*\-\+]\s+(.*)$', stripped_line)
            if ul_match:
                content = ul_match.group(1)
                pdf.cell(5)  # Indent for bullet
                pdf.set_font("Arial", 'B')
                pdf.write(5, f"{chr(149)} ")
                pdf.set_font("Arial", '')
                # Use the new wrapping and styling function
                write_wrapping_styled_text(content, indent=10)
                continue

            # Ordered List
            ol_match = re.match(r'^\s*(\d+)\.\s+(.*)$', stripped_line)
            if ol_match:
                number = ol_match.group(1)
                content = ol_match.group(2)
                pdf.cell(5)  # Indent for number
                pdf.write(5, f"{number}. ")
                # Use the new wrapping and styling function
                write_wrapping_styled_text(content, indent=10)
                continue

            # Default paragraph
            write_wrapping_styled_text(stripped_line)
        
        # [Final code block flush and fallback logic are unchanged]
        if in_code_block and code_buffer:
            pdf.set_font("Courier", size=10)
            pdf.set_fill_color(240, 240, 240)
            pdf.multi_cell(0, 5, sanitize_for_fpdf("\n".join(code_buffer)), border=0, fill=True)

        return pdf.output(dest='S')

    except Exception as e:
        # Create a fallback PDF with the error message for debugging
        pdf2 = FPDF()
        pdf2.set_auto_page_break(True, margin=15)
        pdf2.add_page()
        pdf2.set_font("Arial", size=12)
        pdf2.multi_cell(0, 6, f"An error occurred during PDF generation: {e}\n\nRaw Markdown Input:\n{md_text}")
        return pdf2.output(dest='S')


# --- Streamlit Input Form ---
with st.form("resume_form"):
    st.header("👤 Personal Information")
    name = st.text_input("Full Name *")
    email = st.text_input("Email Address *")
    phone = st.text_input("Phone Number (10 digits)")
    linkedin = st.text_input("LinkedIn Profile URL")
    portfolio = st.text_input("Portfolio / GitHub URL")

    st.header("📝 Career Objective / Summary")
    career_objective = st.text_area("Write a short summary about your professional goals. (2-3 sentences)")

    st.header("🛠 Skills")
    skills = st.text_area("List your skills (e.g., Python, Streamlit, Data Analysis, Project Management)")

    st.header("💼 Work Experience")
    work_experience = st.text_area("For each job, include: Role, Company, Dates, and 2-3 bullet points on key achievements.", height=200)

    st.header("📂 Projects")
    projects = st.text_area("Describe 1-2 key projects. Include: Project Name, Tech Stack, and a brief description.", height=150)

    st.header("🎓 Education")
    education = st.text_area("Enter your education details (e.g., B.S. in Computer Science, University Name, 2020-2024)")

    st.markdown("Fields marked with `*` are essential for the best results.")
    submitted = st.form_submit_button("🚀 Generate My Resume")


# --- Post-Submission Logic ---
if submitted:
    if not name or not email or not skills:
        st.warning("Please fill in all essential fields: Name, Email, and Skills.")
        st.stop()

    errors = validate_inputs(phone, email, linkedin, portfolio)
    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    user_input = {
        "name": name, "email": email, "phone": phone, "linkedin": linkedin,
        "portfolio": portfolio, "skills": skills, "education": education,
        "work_experience": work_experience, "projects": projects,
        "career_objective": career_objective,
    }
    
    with st.spinner("🤖 AI is analyzing your profile and building your resume..."):
        markdown_resume = call_ai_model(user_input)

        if not markdown_resume:
            st.error("🔴 The AI failed to generate a resume. Please try again.")
            st.stop()

        # The variable name is changed to pdf_str to be more accurate
        pdf_str = generate_pdf_from_markdown(markdown_resume) 
        
        if not pdf_str:
            st.error("🔴 The app failed to generate a PDF. Please try again.")
            st.stop()

        st.success("🎉 Your AI-powered resume is ready!")

        file_name = f"{sanitize_filename(name)}_Resume.pdf"
        st.download_button(
            label="📥 Download Resume as PDF",
            data=pdf_str.encode('latin-1'), # Encode here for the download button
            file_name=file_name,
            mime="application/pdf",
        )
        
        # --- FIX FOR TypeError ---
        # 1. Encode the string to bytes. 2. Encode bytes to base64. 3. Decode for HTML.
        base64_pdf = base64.b64encode(pdf_str.encode('latin-1')).decode('utf-8')
        
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        with st.expander("📄 View Raw Markdown"):
            st.markdown(markdown_resume)