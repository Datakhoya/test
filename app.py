import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# --- FONCTIONS ---

def get_available_models(api_key):
    """Demande à Google la liste exacte des modèles disponibles pour CETTE clé."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            # On ne garde que les modèles capables de générer du texte (generateContent)
            chat_models = [m['name'].replace('models/', '') for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            return chat_models
        else:
            return []
    except:
        return []

def extract_text_from_pdf(file):
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            if page.extract_text(): text += page.extract_text()
        return text
    except: return ""

def analyze_cv(model_name, cv_text, job_desc, api_key):
    # On utilise le modèle choisi par l'utilisateur
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Analyse ce CV pour le poste.
    OFFRE: {job_desc}
    CV: {cv_text}
    Réponds UNIQUEMENT avec ce JSON : {{"nom": "Nom", "score": 50, "avis": "Avis court", "points_forts": ["A", "B"], "points_faibles": ["C", "D"]}}
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            return {"error": True, "details": response.text}
        
        clean_json = response.json()['candidates'][0]['content']['parts'][0]['text'].replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"error": True, "details": str(e)}

# --- INTERFACE ---
st.set_page_config(layout="wide", page_title="Diagnostiqueur IA")

st.title("🛠️ Comparateur de CV - Mode Diagnostique")
st.info("Ce mode va scanner votre clé API pour trouver le bon modèle.")

# 1. Entrée de la Clé
api_key = st.text_input("1. Collez votre Clé API ici", type="password")

selected_model = None

# 2. Détection automatique des modèles
if api_key:
    models = get_available_models(api_key)
    if models:
        st.success(f"✅ Clé valide ! {len(models)} modèles trouvés.")
        # Liste déroulante pour choisir le modèle
        selected_model = st.selectbox("2. Choisissez un modèle dans la liste :", models, index=0)
    else:
        st.error("❌ Impossible de trouver des modèles. Vérifiez que la clé est bien copiée (sans espaces).")

# 3. L'application standard
col1, col2 = st.columns(2)
with col1: job = st.text_area("Description du poste")
with col2: cv = st.file_uploader("CV (PDF)", type="pdf")

if st.button("Lancer l'analyse") and api_key and selected_model and job and cv:
    with st.spinner(f"Analyse avec le modèle {selected_model}..."):
        cv_text = extract_text_from_pdf(cv)
        res = analyze_cv(selected_model, cv_text, job, api_key)
        
        if "error" in res:
            st.error(f"Erreur : {res['details']}")
        else:
            st.markdown("---")
            st.header(f"Score : {res.get('score')}/100")
            st.subheader(res.get('nom'))
            st.write(res.get('avis'))
            c1, c2 = st.columns(2)
            c1.success("\n".join([f"- {p}" for p in res.get('points_forts', [])]))
            c2.error("\n".join([f"- {p}" for p in res.get('points_faibles', [])]))
