import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

def analyze_cv(cv_text, job_desc, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": f"Tu es recruteur. Analyse ce CV pour ce poste.\nPOSTE: {job_desc}\nCV: {cv_text}\nRéponds en JSON: {{'nom': '...', 'score': 0-100, 'avis': '...'}}"}]}]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'].replace("```json", "").replace("```", ""))
    except:
        return {"nom": "Erreur", "score": 0, "avis": "Erreur API"}

st.title("Recruteur IA")
api_key = st.text_input("Clé API Google Gemini", type="password")
col1, col2 = st.columns(2)
with col1: job = st.text_area("Offre d'emploi")
with col2: cv = st.file_uploader("CV (PDF)", type="pdf")

if st.button("Analyser") and cv and job and api_key:
    res = analyze_cv(extract_text_from_pdf(cv), job, api_key)
    st.header(f"{res.get('score')}/100 - {res.get('nom')}")
    st.write(res.get('avis'))
