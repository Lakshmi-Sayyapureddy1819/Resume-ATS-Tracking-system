import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re
from fpdf import FPDF

# Load your Google API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to extract clean JSON from Gemini output
def extract_json_from_response(response_text):
    try:
        response_text = response_text.strip()
        response_text = re.sub(r"^```(json)?", "", response_text)
        response_text = re.sub(r"```$", "", response_text)
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            clean_json = match.group(0)
            return json.loads(clean_json)
        else:
            raise ValueError("No valid JSON found.")
    except Exception as e:
        raise ValueError(f"Invalid JSON: {e}")

# Read text from PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Call Gemini model
def get_gemini_response(prompt):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    return response.text

# Streamlit UI
st.set_page_config(page_title="Smart ATS", layout="centered")
st.title("📄 Smart ATS: Resume Evaluator")
st.markdown("Upload your resume and job description to get an ATS score, keyword match, and suggestions!")

jd = st.text_area("📌 Paste the Job Description", height=200)
uploaded_file = st.file_uploader("📁 Upload Your Resume (PDF)", type="pdf")

if st.button("🚀 Evaluate"):
    if uploaded_file and jd.strip():
        resume_text = input_pdf_text(uploaded_file)

        # Gemini prompt
        prompt = f"""
You are an ATS (Applicant Tracking System) expert.
Compare the resume below with the job description and return this exact JSON (no markdown, no explanation):

{{
  "JD Match": "XX%",
  "MissingKeywords": ["keyword1", "keyword2", ...],
  "Profile Summary": "Strengths and weaknesses",
  "Suggestions": "Resume improvement tips"
}}

Resume:
{resume_text}

Job Description:
{jd}
"""

        with st.spinner("Analyzing with Gemini..."):
            response_text = get_gemini_response(prompt)

        try:
            parsed = extract_json_from_response(response_text)

            # Show results
            st.subheader("📊 ATS Match Result")
            match_percent = int(parsed["JD Match"].replace("%", ""))
            st.progress(match_percent / 100)

            st.markdown(f"""
**🎯 JD Match:** {parsed['JD Match']}

**❌ Missing Keywords:**  
{", ".join(parsed['MissingKeywords'])}

**📝 Profile Summary:**  
{parsed['Profile Summary']}

**💡 Suggestions:**  
{parsed['Suggestions']}
""")

            # Download JSON
            json_data = json.dumps(parsed, indent=2)
            st.download_button("⬇️ Download JSON", json_data, "ats_report.json", "application/json")

            # Download PDF
            pdf_report = FPDF()
            pdf_report.add_page()
            pdf_report.set_font("Arial", size=12)
            pdf_report.multi_cell(0, 10, f"JD Match: {parsed['JD Match']}")
            pdf_report.multi_cell(0, 10, "Missing Keywords: " + ", ".join(parsed['MissingKeywords']))
            pdf_report.multi_cell(0, 10, "Profile Summary:\n" + parsed['Profile Summary'])
            pdf_report.multi_cell(0, 10, "Suggestions:\n" + parsed['Suggestions'])
            pdf_report.output("ats_report.pdf")

            with open("ats_report.pdf", "rb") as file:
                st.download_button("⬇️ Download PDF", file, "ats_report.pdf", "application/pdf")

        except Exception as e:
            st.error("❌ Could not parse Gemini response.")
            st.code(response_text)
    else:
        st.warning("⚠️ Please upload a resume and paste a job description.")
