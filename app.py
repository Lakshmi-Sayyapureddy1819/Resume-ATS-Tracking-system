import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(prompt):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

st.title("📄 Smart ATS: Resume Evaluator")
st.text("Enhance your resume with Gemini-powered ATS suggestions")

jd = st.text_area("📌 Paste the Job Description", height=200)
uploaded_file = st.file_uploader("📁 Upload Your Resume (PDF)", type="pdf")

if st.button("🚀 Evaluate"):
    if uploaded_file is not None and jd.strip() != "":
        resume_text = input_pdf_text(uploaded_file)

        prompt = f"""
Act like a skilled ATS (Applicant Tracking System) trained in tech hiring. Evaluate this resume against the job description below.

Resume: ```{resume_text}```
Job Description: ```{jd}```

Return a JSON with:
- JD Match (percentage)
- MissingKeywords (as list)
- Profile Summary (as paragraph)
- Suggestions to Rewrite Resume (improvement tips and enhancements)

Output format:
{{
  "JD Match": "85%",
  "MissingKeywords": [...],
  "Profile Summary": "...",
  "Suggestions": "..."
}}
"""

        with st.spinner("Analyzing resume..."):
            response_text = get_gemini_response(prompt)

        try:
            parsed = json.loads(response_text)

            # 🌡️ Progress bar for JD Match
            match_percent = int(parsed["JD Match"].replace("%", ""))
            st.subheader("📊 Match Result")
            st.progress(match_percent / 100)

            # 📋 Display structured output
            st.markdown(f"""
**🎯 JD Match:** {parsed['JD Match']}

**❌ Missing Keywords:**  
{", ".join(parsed['MissingKeywords'])}

**📝 Profile Summary:**  
{parsed['Profile Summary']}

**💡 AI Suggestions to Improve Resume:**  
{parsed.get("Suggestions", "No suggestions found.")}
""")

            # 🧾 Download as JSON
            json_report = json.dumps(parsed, indent=2)
            st.download_button("⬇️ Download JSON Report", data=json_report, file_name="ats_evaluation.json", mime="application/json")

            # 🧾 Download as PDF
            from fpdf import FPDF
            pdf_report = FPDF()
            pdf_report.add_page()
            pdf_report.set_font("Arial", size=12)
            pdf_report.multi_cell(0, 10, f"JD Match: {parsed['JD Match']}")
            pdf_report.multi_cell(0, 10, "Missing Keywords: " + ", ".join(parsed['MissingKeywords']))
            pdf_report.multi_cell(0, 10, "Profile Summary:\n" + parsed['Profile Summary'])
            pdf_report.multi_cell(0, 10, "Suggestions:\n" + parsed.get("Suggestions", ""))
            pdf_path = "ats_report.pdf"
            pdf_report.output(pdf_path)

            with open(pdf_path, "rb") as file:
                st.download_button("⬇️ Download PDF Report", data=file, file_name="ats_report.pdf", mime="application/pdf")

        except Exception as e:
            st.error("❌ Failed to parse Gemini response. Try again.")
            st.text(response_text)
    else:
        st.warning("⚠️ Please upload a resume and paste the job description.")
