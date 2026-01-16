import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# --- CONFIGURATION ---
# On utilise le modèle le plus standard et stable
MODEL_NAME = "gemini-pro"

def extract_text_from_pdf(file):
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()
        return text
    except Exception as e:
        return f"Erreur lecture PDF: {str(e)}"

def analyze_cv(cv_text, job_desc, api_key):
    # URL mise à jour pour le modèle 1.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Prompt simplifié et robuste
    prompt = f"""
    Analyse ce CV pour le poste ci-dessous.
    POSTE: {job_desc}
    CV: {cv_text}
    
    Réponds UNIQUEMENT avec ce JSON strict:
    {{
        "nom": "Nom du candidat",
        "score": 50,
        "avis": "Ton avis en une phrase",
        "points_forts": ["point 1", "point 2"],
        "points_faibles": ["point 1", "point 2"]
    }}
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # SI ERREUR GOOGLE (404, 400, etc.)
        if response.status_code != 200:
            return {"error": True, "details": f"Erreur Google ({response.status_code}): {response.text}"}
            
        # SI SUCCÈS
        result_json = response.json()
        raw_text = result_json['candidates'][0]['content']['parts'][0]['text']
        clean_json = raw_text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_json)
        
    except Exception as e:
        return {"error": True, "details": f"Erreur Python : {str(e)}"}

# --- INTERFACE ---
st.set_page_config(layout="wide")
st.title("🤖 Recruteur IA v2 (Debug Mode)")

# Vérification Clé API
api_key = st.text_input("Votre Clé API Gemini", type="password")

col1, col2 = st.columns(2)
with col1: 
    job = st.text_area("Description du poste", height=200)
with col2: 
    cv = st.file_uploader("CV (PDF)", type="pdf")

if st.button("Lancer l'analyse"):
    if not api_key or not job or not cv:
        st.warning("Il manque des informations (Clé, Poste ou CV).")
    else:
        with st.spinner("Analyse en cours..."):
            cv_text = extract_text_from_pdf(cv)
            res = analyze_cv(cv_text, job, api_key)
            
            # Affichage des résultats ou de l'erreur précise
            if "error" in res:
                st.error("❌ OUPS, UNE ERREUR EST SURVENUE")
                st.code(res["details"]) # Affiche le message technique exact
            else:
                st.balloons()
                st.header(f"Note : {res.get('score', 0)}/100")
                st.subheader(f"Candidat : {res.get('nom', 'Inconnu')}")
                st.info(res.get('avis'))
                
                c1, c2 = st.columns(2)
                with c1:
                    st.success("Points Forts")
                    for p in res.get('points_forts', []): st.write(f"- {p}")
                with c2:
                    st.error("Points Faibles")
                    for p in res.get('points_faibles', []): st.write(f"- {p}")
