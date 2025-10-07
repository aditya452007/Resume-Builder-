# import os
# import re
# import papermill as pm
# import streamlit as st
# import json, requests
# from openai import OpenAI
# import unicodedata
# from fpdf import FPDF
# from IPython.display import display, HTML, IFrame, FileLink


# # --- Configuration for Papermill ---
# OUTPUT_PDF = "resume.pdf"


# # --- Openrouter Api Key ---
# OPENROUTER_API_KEY = f"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"


# # --- check api connection ---
# def open_ai():
#     try:
#         client = OpenAI(
#             base_url="https://openrouter.ai/api/v1",
#             api_key=OPENROUTER_API_KEY
#         )
#         return client
#     except TypeError:
#         print("🔴 ERROR: OPENROUTER_API_KEY environment variable not set.")
        
#         exit()



# # --- Page Config (must be called before other Streamlit UI) ---
# st.set_page_config(page_title="AI Resume Builder", layout="centered")

# st.title("📄 AI Resume Builder")
# st.write("Fill in your details below. Your information will be processed into a polished resume.")


# # --- Helper Functions ---
# def sanitize_filename(name: str) -> str:
#     """Creates a safe, valid filename from a user's name."""
#     name = (name or "").strip()
#     # keep letters, numbers, dash, underscore; replace spaces with underscore
#     safe = re.sub(r"[^\w\-. ]", "", name).replace(" ", "_")
#     return safe or "resume"

# def validate_inputs(phone: str, email: str, linkedin: str, portfolio: str):
#     """Validates the format of key personal info fields."""
#     errors = []
#     phone_digits = re.sub(r"\D", "", (phone or ""))
#     if not re.fullmatch(r"\d{10}", phone_digits):
#         errors.append("📞 Phone number must contain exactly 10 digits.")
    
#     if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", (email or "").strip()):
#         errors.append("✉️ Please enter a valid email address.")
    
#     if linkedin:
#         ln = linkedin.strip()
#         if not (ln.startswith("https://www.linkedin.com/") or ln.startswith("https://linkedin.com/")):
#             errors.append("🔗 LinkedIn URL must start with 'https://linkedin.com/'.")
            
#     if portfolio:
#         pf = portfolio.strip()
#         if not pf.startswith("http://") and not pf.startswith("https://"):
#             errors.append("💻 Portfolio/GitHub URL must start with 'http://' or 'https://'.")
            
#     return errors



# # --- Call Gemini ---
# def call_gemini(user_input):
#     MODEL = "google/gemini-2.0-flash-experimental:(free)"
#     client_gemini = open_ai()
#     task = """Analyze the candidate resume data provided.
#     - Perform ATS-focused analysis
#     - Extract skills, education, projects, work experience, extracurriculars
#     - Identify hidden strengths and reframe weaknesses into strengths
#     - Quantify achievements where possible
#     - Return structured JSON only, no text outside JSON
#     """

#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 f"You are a world-class Career Strategist and Resume Analyst with deep expertise in talent acquisition and Applicant Tracking Systems (ATS). Your task is to perform a deep analysis of a candidate's profile against a specific job description. You must identify areas where the candidate is underselling themselves and transform their raw information into high-impact, quantified achievements.user_input : {user_input}"
#             ),
#         },
#         {
#             "role": "user",
#             "content": task,
#         }
#     ]

#     response = client_gemini.chat.completions.create(
#             model=MODEL,
#             messages=messages
#     )
#     # Get the assistant's reply from the response
#     assistant_reply_gemini = response.choices[0].message.content
#     return assistant_reply_gemini


# # --- Resume Pdf ---
# def resume_pdf():
#     # Simple Markdown -> PDF renderer with a safe fallback to plain-text PDF (avoids latin-1 errors)
#     # Usage: put your markdown string in `md` (this notebook already has assistant_reply_Z_ai)

#     # Use existing notebook variable if present
#     try:
#         md = call_gemini()
#     except NameError:
#         md = "# Hello\nThis is a sample markdown."

#     # Replace common problematic unicode and force-safe latin-1 fallback
#     def sanitize_for_fpdf(s: str) -> str:
#         if not s:
#             return s
#         repl = {
#             '\u2022': '-', '\u2013': '-', '\u2014': '--',
#             '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
#         }
#         for k, v in repl.items():
#             s = s.replace(k, v)
#         s = unicodedata.normalize('NFKD', s)
#         # drop characters that can't be encoded to latin-1 (safe fallback for FPDF core fonts)
#         s = s.encode('latin-1', 'ignore').decode('latin-1')
#         return s

#     # Minimal inline parsing: code ``, bold **, italic *
#     inline_pat = re.compile(r'(`[^`]+`)|(\*\*[^\*]+\*\*)|(\*[^\*]+\*)|(\[([^\]]+)\]\([^\)]+\))')
#     def render_paragraph(pdf: FPDF, text: str, base_size=12):
#         # split into tokens, write each with style changes
#         pos = 0
#         line_h = max(4, base_size * 0.45 + 2)
#         for m in inline_pat.finditer(text):
#             if m.start() > pos:
#                 pdf.set_font("Arial", size=base_size)
#                 pdf.set_text_color(0, 0, 0)
#                 pdf.write(line_h, text[pos:m.start()])
#             token = m.group(0)
#             if token.startswith('`') and token.endswith('`'):
#                 pdf.set_font("Courier", size=max(8, base_size - 1))
#                 pdf.set_text_color(80, 80, 80)
#                 pdf.write(line_h, token[1:-1])
#             elif token.startswith('**') and token.endswith('**'):
#                 pdf.set_font("Arial", style='B', size=base_size)
#                 pdf.write(line_h, token[2:-2])
#             elif token.startswith('*') and token.endswith('*'):
#                 pdf.set_font("Arial", style='I', size=base_size)
#                 pdf.write(line_h, token[1:-1])
#             elif token.startswith('['):  # link -> display text only
#                 text_only = m.group(5) or token
#                 pdf.set_font("Arial", size=base_size)
#                 pdf.set_text_color(0, 0, 180)
#                 pdf.write(line_h, text_only)
#                 pdf.set_text_color(0, 0, 0)
#             pos = m.end()
#         if pos < len(text):
#             pdf.set_font("Arial", size=base_size)
#             pdf.set_text_color(0, 0, 0)
#             pdf.write(line_h, text[pos:])
#         pdf.ln(line_h + 1)

#     def markdown_to_pdf(md_text: str, out_fname="output.pdf"):
#         # First attempt: render a simple styled markdown -> pdf
#         pdf = FPDF()
#         pdf.set_auto_page_break(True, margin=15)
#         pdf.add_page()
#         pdf.set_font("Arial", size=12)

#         in_code = False
#         code_buf = []
#         for raw in md_text.splitlines():
#             line = raw.rstrip('\n')
#             # code fence handling
#             if line.strip().startswith("```"):
#                 if not in_code:
#                     in_code = True
#                     code_buf = []
#                 else:
#                     # flush code block
#                     pdf.set_font("Courier", size=9)
#                     pdf.set_fill_color(245, 245, 245)
#                     # write each code line in monospace; use multi_cell to keep line breaks
#                     for c in code_buf:
#                         pdf.set_x(12)
#                         pdf.multi_cell(0, 5, c)
#                     pdf.ln(2)
#                     pdf.set_font("Arial", size=12)
#                     in_code = False
#                 continue

#             if in_code:
#                 code_buf.append(line)
#                 continue

#             # horizontal rule
#             if re.match(r'^[\-\*_]{3,}\s*$', line.strip()):
#                 y = pdf.get_y() + 3
#                 pdf.set_line_width(0.6)
#                 pdf.line(10, y, pdf.w - 10, y)
#                 pdf.ln(6)
#                 pdf.set_line_width(0.2)
#                 continue

#             # heading
#             m = re.match(r'^\s{0,3}(#{1,6})\s+(.*)$', line)
#             if m:
#                 lvl = len(m.group(1))
#                 text = m.group(2).strip()
#                 sizes = {1:16, 2:14, 3:12, 4:11, 5:10, 6:10}
#                 size = sizes.get(lvl, 12)
#                 pdf.set_font("Arial", style='B', size=size)
#                 render_paragraph(pdf, text, base_size=size)
#                 pdf.ln(1)
#                 pdf.set_font("Arial", size=12)
#                 continue

#             # unordered list
#             ul = re.match(r'^\s*[\-\*\+]\s+(.*)$', line)
#             if ul:
#                 content = ul.group(1).strip()
#                 pdf.set_x(12)
#                 pdf.set_font("Arial", style='B', size=12)
#                 pdf.write(5, "- ")
#                 pdf.set_font("Arial", size=12)
#                 render_paragraph(pdf, content, base_size=12)
#                 continue

#             # ordered list
#             ol = re.match(r'^\s*\d+\.\s+(.*)$', line)
#             if ol:
#                 content = ol.group(1).strip()
#                 pdf.set_x(12)
#                 pdf.write(5, "1. ")
#                 render_paragraph(pdf, content, base_size=12)
#                 continue

#             # blank line
#             if line.strip() == "":
#                 pdf.ln(4)
#                 continue

#             # normal paragraph (with inline)
#             render_paragraph(pdf, line, base_size=12)

#         # try to output; FPDF core fonts require latin-1 encoding
#         try:
#             pdf_out = pdf.output(dest='S')  # bytes or str
#             pdf_bytes = pdf_out.encode('latin-1') if isinstance(pdf_out, str) else pdf_out
#             with open(out_fname, "wb") as f:
#                 f.write(pdf_bytes)
#             return out_fname
#         except Exception as e:
#             # Fallback: strip markdown to plain text, sanitize, and regenerate simple PDF
#             text = md_text
#             # minimal markdown removal: headings/markers, code fences, links -> text
#             text = re.sub(r'```.*?```', '', text, flags=re.S)  # remove fenced code entirely for fallback
#             text = re.sub(r'[#>*`]', '', text)
#             text = re.sub(r'\[(.*?)\]\([^\)]+\)', r'\1', text)  # [text](url) -> text
#             text = sanitize_for_fpdf(text)
#             pdf2 = FPDF()
#             pdf2.set_auto_page_break(True, margin=15)
#             pdf2.add_page()
#             pdf2.set_font("Arial", size=12)
#             for line in text.splitlines():
#                 # ensure no very long words break layout badly
#                 pdf2.multi_cell(0, 6, line)
#             pdf_out = pdf2.output(dest='S')
#             pdf_bytes = pdf_out.encode('latin-1') if isinstance(pdf_out, str) else pdf_out
#             with open(out_fname, "wb") as f:
#                 f.write(pdf_bytes)
#             return out_fname

#     # Generate PDF
#     fname = markdown_to_pdf(md, out_fname="resume.pdf")
#     display(HTML(f'<a href="{fname}" download style="font-size:14px">Download {fname}</a>'))
#     try:
#         display(IFrame(fname, width=800, height=600))
#     except Exception:
#         display(FileLink(fname))

#     return "Saved:", fname




# # --- Resume Input Form ---
# with st.form("resume_form"):
#     st.header("👤 Personal Information")
#     name = st.text_input("Full Name *")
#     email = st.text_input("Email Address *")
#     phone = st.text_input("Phone Number (10 digits) *")
#     linkedin = st.text_input("LinkedIn Profile URL")
#     portfolio = st.text_input("Portfolio / GitHub URL")

#     st.header("🛠 Skills")
#     skills = st.text_area("List your skills (comma-separated) *")

#     st.header("🎓 Education")
#     education = st.text_area("Enter your education details (degree, school, year, GPA, etc.)")

#     st.header("💼 Work Experience")
#     work_experience = st.text_area("Enter your work experience (role, company, dates, achievements)")

#     st.header("📂 Projects")
#     projects = st.text_area("Enter your projects (name, tech stack, description, outcomes)")

#     st.header("📜 Certifications")
#     certifications = st.text_area("Enter your certifications (name, org, year, credential link)")

#     st.header("🌐 Extracurricular Activities")
#     extracurriculars = st.text_area("Enter your extracurricular activities, volunteering, leadership roles, etc.")

#     st.header("📝 Career Objective")
#     career_objective = st.text_area("Write a short summary / objective for your resume")

#     st.markdown("Fields marked with `*` are essential for the best results.")
#     submitted = st.form_submit_button("🚀 Generate Resume")



# # --- Post-Submission Logic ---
# if submitted:
#     # Essential fields check
#     if not name or not email or not skills:
#         st.warning("Please fill in all essential fields marked with an asterisk (*).")
#         st.stop()

#     # Detailed format validation
#     errors = validate_inputs(phone, email, linkedin, portfolio)
#     if errors:
#         for error in errors:
#             st.error(error)
#     else:
#         # If validation passes, create the dictionary and run the notebook
#         user_input = {
#             "name": name,
#             "email": email,
#             "phone": phone,
#             "linkedin": linkedin,
#             "portfolio": portfolio,
#             "skills": skills,
#             "education": education,
#             "work_experience": work_experience,
#             "projects": projects,
#             "certifications": certifications,
#             "extracurriculars": extracurriculars,
#             "career_objective": career_objective,
#         }
#         call_gemini(user_input)
#         with st.spinner("🤖 AI is analyzing your profile and building your resume... This may take a moment."):
#             try :

#                 resume = resume_pdf()




# --------------------------------------------------------------------------------------------------


import os
import re
import streamlit as st
import json
from openai import OpenAI
import unicodedata
from fpdf import FPDF

# --- Configuration ---
# BEST PRACTICE: Use Streamlit Secrets to store your API key
# Create a file .streamlit/secrets.toml and add:
OPENROUTER_API_KEY = f"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"

# try:
#     OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
# except (FileNotFoundError, KeyError):
#     st.error("🔴 ERROR: API key not found. Please add it to your Streamlit secrets.")
#     st.stop()


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
    
    if linkedin:
        ln = linkedin.strip()
        if not (ln.startswith("https://www.linkedin.com/") or ln.startswith("https://linkedin.com/")):
            errors.append("🔗 LinkedIn URL must start with 'https://linkedin.com/'.")
            
    if portfolio:
        pf = portfolio.strip()
        if not pf.startswith("http://") and not pf.startswith("https://"):
            errors.append("💻 Portfolio/GitHub URL must start with 'http://' or 'https://'.")
            
    return errors


# --- Core AI and PDF Functions ---
def call_gemini(user_input: dict):
    """Calls the Gemini model via OpenRouter to generate resume markdown."""
    client = get_openai_client()
    model = "z-ai/glm-4.5-air:free" # Updated model for better performance

    system_prompt = (
        "You are a world-class Career Strategist and Resume Analyst with deep expertise in "
        "talent acquisition and Applicant Tracking Systems (ATS). Your task is to analyze a "
        "candidate's raw information and transform it into a high-impact, professional resume "
        "in Markdown format. Focus on using action verbs, quantifying achievements, and structuring "
        "the content logically. Ensure the output is clean, well-formatted Markdown."
    )
    
    user_prompt = (
        "Analyze the following candidate data and generate a complete, professional resume in Markdown format. "
        "Structure it with clear sections (Summary, Skills, Experience, Education, Projects). "
        "Rewrite descriptions to be achievement-oriented. Do not include any text other than the markdown resume itself.\n\n"
        f"Candidate Data:\n```json\n{json.dumps(user_input, indent=2)}\n```"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"🔴 An error occurred while contacting the AI model: {e}")
        return None

# def generate_pdf_from_markdown(md_text: str) -> bytes:
#     """
#     Converts a markdown string into a PDF and returns its content as bytes.
#     This function is heavily refactored from the original to be self-contained and return bytes.
#     """
#     pdf = FPDF()
#     pdf.set_auto_page_break(True, margin=15)
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)

#     # Sanitize text for FPDF's core fonts (latin-1)
#     def sanitize_for_fpdf(s: str) -> str:
#         s = s or ""
#         repl = {
#             '\u2022': '*', '\u2013': '-', '\u2014': '--', '\u2018': "'",
#             '\u2019': "'", '\u201c': '"', '\u201d': '"',
#         }
#         for k, v in repl.items():
#             s = s.replace(k, v)
#         return s.encode('latin-1', 'replace').decode('latin-1')

#     for line in md_text.splitlines():
#         line = sanitize_for_fpdf(line)
        
#         # Heading 1
#         if line.startswith("# "):
#             pdf.set_font("Arial", 'B', 16)
#             pdf.multi_cell(0, 10, line[2:].strip())
#             pdf.ln(4)
#         # Heading 2
#         elif line.startswith("## "):
#             pdf.set_font("Arial", 'B', 14)
#             pdf.multi_cell(0, 9, line[3:].strip())
#             pdf.ln(3)
#         # Unordered list
#         elif line.startswith("* ") or line.startswith("- "):
#             pdf.set_font("Arial", '', 12)
#             pdf.cell(5) # Indent
#             pdf.multi_cell(0, 6, f"\u2022 {line[2:].strip()}")
#             pdf.ln(1)
#         # Horizontal rule
#         elif re.match(r'^[\-\*_]{3,}\s*$', line.strip()):
#             pdf.ln(2)
#             pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
#             pdf.ln(2)
#         # Paragraph
#         else:
#             pdf.set_font("Arial", '', 12)
#             pdf.multi_cell(0, 6, line.strip())
#             pdf.ln(2)
            
#     # Return PDF content as bytes
#     return pdf.output(dest='S').encode('latin-1')


def generate_pdf_from_markdown(md_text: str, font_path: str = 'DejaVuSans.ttf') -> bytes:
    """
    A definitive, UTF-8 compatible PDF generator using fpdf2 and a Unicode font.
    This is the most robust solution against encoding errors.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    
    # --- Add Unicode Font Support ---
    # The 'uni=True' parameter is crucial for fpdf2's UTF-8 mode.
    try:
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.add_font('DejaVu', 'B', font_path, uni=True) # Add bold variant if needed
        pdf.add_font('DejaVu', 'I', font_path, uni=True) # Add italic variant if needed
    except RuntimeError:
        # Handle case where font file is not found
        st.error(f"🔴 FONT ERROR: The font file '{font_path}' was not found. Please download it.")
        return b"" # Return empty bytes
        
    pdf.set_font('DejaVu', '', 12)
    pdf.add_page()

    # --- Styled Text Helper (works with UTF-8) ---
    def write_styled_text(text: str):
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                pdf.set_font('DejaVu', 'B')
                pdf.write(pdf.h, part[2:-2])
            elif part.startswith('*') and part.endswith('*'):
                pdf.set_font('DejaVu', 'I')
                pdf.write(pdf.h, part[1:-1])
            else:
                pdf.set_font('DejaVu', '')
                pdf.write(pdf.h, part)
        pdf.ln()

    # --- Main Parsing Loop ---
    # No sanitization needed! We can process the raw text.
    for line in md_text.splitlines():
        line = line.strip()
        if not line:
            pdf.ln(2)
            continue

        if line.startswith("# "):
            pdf.set_font("DejaVu", 'B', 16)
            pdf.multi_cell(0, 10, line[2:])
            pdf.ln(4)
        elif line.startswith("## "):
            pdf.set_font("DejaVu", 'B', 14)
            pdf.multi_cell(0, 9, line[3:])
            pdf.ln(3)
        elif line.startswith(("* ", "- ")):
            # We can now use the actual Unicode bullet character!
            pdf.cell(5)
            pdf.set_font("DejaVu", '', 12)
            pdf.multi_cell(0, 6, f"\u2022 {line[2:]}")
            pdf.ln(1)
        elif re.match(r'^[\-\*_]{3,}\s*$', line):
            pdf.ln(2)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(2)
        else:
            pdf.set_font("DejaVu", '', 12)
            write_styled_text(line)
            pdf.ln(2)
    
    # output() returns bytes directly, no encoding needed on our end.
    return pdf.output()

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
    work_experience = st.text_area("Enter your work experience. For each job, include: Role, Company, Dates, and 2-3 bullet points on key achievements.", height=200)

    st.header("📂 Projects")
    projects = st.text_area("Describe 1-2 key projects. Include: Project Name, Tech Stack, and a brief description of its purpose and your role.", height=150)

    st.header("🎓 Education")
    education = st.text_area("Enter your education details (e.g., B.S. in Computer Science, University Name, 2020-2024)")

    st.markdown("Fields marked with `*` are essential for the best results.")
    submitted = st.form_submit_button("🚀 Generate My Resume")


# --- Post-Submission Logic ---
if submitted:
    # Essential fields check
    if not name or not email or not skills:
        st.warning("Please fill in all essential fields: Name, Email, and Skills.")
        st.stop()

    # Detailed format validation
    errors = validate_inputs(phone, email, linkedin, portfolio)
    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    # If validation passes, create the dictionary and run the generation process
    user_input = {
        "name": name, "email": email, "phone": phone, "linkedin": linkedin,
        "portfolio": portfolio, "skills": skills, "education": education,
        "work_experience": work_experience, "projects": projects,
        "career_objective": career_objective,
    }
    
    with st.spinner("🤖 AI is analyzing your profile and building your resume..."):
        markdown_resume = call_gemini(user_input)

        if markdown_resume:
            pdf_bytes = generate_pdf_from_markdown(markdown_resume)
            
            st.success("🎉 Your AI-powered resume is ready!")

            # Provide download button
            file_name = f"{sanitize_filename(name)}_Resume.pdf"
            st.download_button(
                label="📥 Download Resume as PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
            )
            
            # Display the PDF in the app
            st.pdf(pdf_bytes)

            # Optional: Show the raw markdown for review
            with st.expander("📄 View Raw Markdown"):
                st.markdown(markdown_resume)
