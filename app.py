import streamlit as st
import pandas as pd
import os
import io
import qrcode
import json
import hashlib
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

# --------------------------------------------------
# STREAMLIT CONFIG + PWA
# --------------------------------------------------
st.set_page_config(
    page_title="Riccardo Rispoli - Fisioterapia", 
    layout="centered",
    page_icon="💪",
    initial_sidebar_state="collapsed"
)

# PWA Manifest e Meta Tags per installabilità
st.markdown("""
<head>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="RR Fisioterapia">
    <link rel="apple-touch-icon" href="./app/static/logo.png">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#1e3c72">
    <link rel="manifest" href="./manifest.json">
</head>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CUSTOM CSS - DESIGN MODERNO BLU
# --------------------------------------------------
st.markdown("""
<style>
    /* Importa font moderno */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Sfondo gradiente blu */
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Contenitore principale */
    .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    
    /* Testo principale - SCURO su sfondo bianco */
    .main, p, span, div, label {
        color: #333333 !important;
    }
    
    /* Titoli */
    h1, h2, h3 {
        color: #1e3c72 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Bottoni primari */
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(30, 60, 114, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Forza testo bianco nei bottoni */
    .stButton > button p,
    .stButton > button span,
    .stButton > button div {
        color: white !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(30, 60, 114, 0.4) !important;
        color: white !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div,
    .stNumberInput > div > div > input {
        border: 2px solid #e0e0e0 !important;
        border-radius: 10px !important;
        padding: 0.75rem !important;
        transition: border-color 0.3s ease !important;
        color: #1e3c72 !important;
        font-weight: 600 !important;
    }
    
    /* Text color for input labels */
    .stTextInput > label,
    .stSelectbox > label,
    .stMultiSelect > label,
    .stNumberInput > label {
        color: #1e3c72 !important;
        font-weight: 600 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #2a5298 !important;
        box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.1) !important;
    }
    
    /* Card esercizi */
    .exercise-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #2a5298;
        transition: all 0.3s ease;
    }
    
    .exercise-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #1e3c72 !important;
        font-weight: 700 !important;
    }
    
    /* Divider */
    hr {
        border-color: #2a5298 !important;
        opacity: 0.3 !important;
    }
    
    /* Success messages */
    .stSuccess {
        background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #f5f7fa !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        color: #1e3c72 !important;
    }
    
    /* Checkbox */
    .stCheckbox > label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #1e3c72 !important;
    }
    
    /* Video container */
    iframe {
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATABASE PAZIENTI (GOOGLE SHEETS)
# --------------------------------------------------
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage

# Setup Google Sheets
def get_google_sheet():
    """Connessione a Google Sheets usando secrets"""
    try:
        # Credenziali da Streamlit secrets
        credentials_dict = dict(st.secrets["gcp_service_account"])
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        client = gspread.authorize(credentials)
        
        # Apri il foglio usando l'ID
        sheet_id = st.secrets["sheet_id"]
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        
        return worksheet
    except Exception as e:
        st.error(f"Errore connessione Google Sheets: {e}")
        return None

# --------------------------------------------------
# CLOUD STORAGE (VIDEO PAZIENTI)
# --------------------------------------------------
BUCKET_NAME = "schede-pazienti-video"

def get_storage_client():
    """Connessione a Cloud Storage"""
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(credentials_dict)
        client = storage.Client(credentials=credentials, project=credentials_dict['project_id'])
        return client
    except Exception as e:
        st.error(f"Errore connessione Cloud Storage: {e}")
        return None

def upload_video_to_cloud(file_data, paziente_code, esercizio_nome, timestamp):
    """Upload video su Cloud Storage"""
    try:
        client = get_storage_client()
        if not client:
            return None
        
        bucket = client.bucket(BUCKET_NAME)
        
        # Nome file unico: paziente_esercizio_timestamp.ext
        file_extension = file_data.name.split('.')[-1]
        blob_name = f"{paziente_code}/{esercizio_nome.replace(' ', '_')}_{timestamp}.{file_extension}"
        
        blob = bucket.blob(blob_name)
        
        # Upload
        file_data.seek(0)
        blob.upload_from_file(file_data, content_type=file_data.type)
        
        # Rendi accessibile (signed URL valido 7 giorni)
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(days=365),
            method="GET"
        )
        
        return {
            "blob_name": blob_name,
            "url": url,
            "size_mb": round(file_data.size / (1024*1024), 2)
        }
    except Exception as e:
        st.error(f"Errore upload video: {e}")
        return None

def get_video_url(blob_name):
    """Ottieni URL firmato per visualizzare video"""
    try:
        client = get_storage_client()
        if not client:
            return None
        
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        # URL valido 7 giorni
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(days=7),
            method="GET"
        )
        
        return url
    except Exception as e:
        return None

def delete_video_from_cloud(blob_name):
    """Elimina video da Cloud Storage"""
    try:
        client = get_storage_client()
        if not client:
            return False
        
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.delete()
        
        return True
    except Exception as e:
        st.error(f"Errore eliminazione video: {e}")
        return False
        
# --------------------------------------------------
# EMAIL NOTIFICATIONS (GRATIS con Gmail)
# --------------------------------------------------
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def invia_email_notifica(destinatario, oggetto, corpo):
    """Invia email usando Gmail SMTP"""
    try:
        # Usa email hardcoded
        sender_email = "riccardo.rspl@gmail.com"
        
        # Prova a prendere password da secrets
        try:
            sender_password = st.secrets.get("email_password", "")
            if not sender_password:
                return False
        except:
            return False
        
        # Crea messaggio
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = destinatario
        msg['Subject'] = oggetto
        
        msg.attach(MIMEText(corpo, 'html'))
        
        # Invia via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        # Silenzioso per non bloccare l'app
        return False

def notifica_video_caricato(nome_paziente, esercizio):
    """Notifica fisioterapista quando paziente carica video"""
    email_fisio = "riccardo.rspl@gmail.com"
    oggetto = f"Nuovo video da {nome_paziente}"
    corpo = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #1e3c72;">Nuovo video caricato</h2>
        <p><strong>Paziente:</strong> {nome_paziente}</p>
        <p><strong>Esercizio:</strong> {esercizio}</p>
        <p>Accedi alla dashboard per visualizzare il video e lasciare feedback.</p>
        <p><a href="https://schede-pazienti-studiosauro.streamlit.app" style="background:#1e3c72;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Vai alla dashboard</a></p>
    </body>
    </html>
    """
    return invia_email_notifica(email_fisio, oggetto, corpo)
    
@st.cache_data(ttl=60)  # Cache per 60 secondi
def carica_database():
    """Carica tutti i pazienti da Google Sheets"""
    try:
        worksheet = get_google_sheet()
        if not worksheet:
            st.warning("[!] Impossibile connettersi a Google Sheets")
            return {}
        
        # Ottieni tutti i record
        records = worksheet.get_all_records()
        
        if not records:
            st.info("ℹ️ Nessun paziente nel database")
            return {}
        
        # Converti in dizionario con codice come chiave
        db = {}
        for idx, record in enumerate(records):
            try:
                codice = record.get('codice', '').strip()
                if not codice:
                    continue
                
                # Parse JSON con gestione errori
                try:
                    scheda = json.loads(record.get('scheda', '[]')) if record.get('scheda') else []
                except:
                    scheda = []
                
                try:
                    progressi = json.loads(record.get('progressi', '{}')) if record.get('progressi') else {}
                except:
                    progressi = {}
                
                try:
                    note = json.loads(record.get('note', '{}')) if record.get('note') else {}
                except:
                    note = {}
                
                try:
                    storico = json.loads(record.get('storico', '{}')) if record.get('storico') else {}
                except:
                    storico = {}
                
                db[codice] = {
                    'nome': record.get('nome', ''),
                    'motivo': record.get('motivo', ''),
                    'data_creazione': record.get('data_creazione', ''),
                    'scheda': scheda,
                    'progressi': progressi,
                    'note': note,
                    'storico': storico
                }
            except Exception as e:
                st.warning(f"[!] Errore caricamento riga {idx+2}: {e}")
                continue
        
        return db
    except Exception as e:
        st.error(f"❌ Errore caricamento database: {e}")
        import traceback
        st.code(traceback.format_exc())
        return {}

def salva_database(db):
    """Salva l'intero database su Google Sheets"""
    try:
        worksheet = get_google_sheet()
        if not worksheet:
            return False
        
        # Prepara i dati per Google Sheets
        rows = []
        for codice, data in db.items():
            rows.append([
                codice,
                data.get('nome', ''),
                data.get('motivo', ''),
                data.get('data_creazione', ''),
                json.dumps(data.get('scheda', []), ensure_ascii=False),
                json.dumps(data.get('progressi', {}), ensure_ascii=False),
                json.dumps(data.get('note', {}), ensure_ascii=False),
                json.dumps(data.get('storico', {}), ensure_ascii=False)
            ])
        
        # Cancella tutto tranne l'intestazione
        worksheet.clear()
        
        # Scrivi intestazione CON storico
        worksheet.append_row(['codice', 'nome', 'motivo', 'data_creazione', 'scheda', 'progressi', 'note', 'storico'])
        
        # Scrivi i dati
        if rows:
            worksheet.append_rows(rows)
        
        return True
    except Exception as e:
        st.error(f"Errore salvataggio database: {e}")
        return False

def genera_codice_paziente(nome_paziente):
    """Genera un codice univoco per il paziente"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{nome_paziente}{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]

# --------------------------------------------------
# LOAD CSV
# --------------------------------------------------
@st.cache_data
def load_csv():
    df = pd.read_csv("esercizi.csv")
    df = df.fillna("")
    df["distretto"] = df["distretto"].astype(str)
    return df

df = load_csv()

# --------------------------------------------------
# ROUTING: FISIOTERAPISTA vs PAZIENTE
# --------------------------------------------------
# Supporta sia ?paziente=xxx che p=xxx (più corto per URL installabili)
query_params = st.query_params
paziente_code = query_params.get("p", None) or query_params.get("paziente", None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
VIDEO_DIR = os.path.join(BASE_DIR, "videos")

def trova_immagine(nome_esercizio):
    nome_norm = nome_esercizio.strip().lower().replace(" ", "")
    if not os.path.exists(IMAGE_DIR):
        return None
    for file in os.listdir(IMAGE_DIR):
        file_norm = os.path.splitext(file)[0].strip().lower().replace(" ", "")
        if nome_norm == file_norm:
            return os.path.join(IMAGE_DIR, file)
    return None

# --------------------------------------------------
# MODALITÀ PAZIENTE
# --------------------------------------------------
if paziente_code:
    db = carica_database()
    
    # DEBUG - Mostra info di debug (rimuovere dopo aver sistemato)
    with st.expander("🔍 DEBUG INFO (per te, non per il paziente)"):
        st.write(f"**Codice cercato:** `{paziente_code}`")
        st.write(f"**Codici nel database:** `{list(db.keys())}`")
        st.write(f"**Numero pazienti:** {len(db)}")
        if db:
            st.write("**Primo paziente (esempio):**")
            first_code = list(db.keys())[0]
            st.json({first_code: db[first_code]})
    
    if paziente_code not in db:
        st.error("❌ Codice paziente non valido!")
        st.warning(f"Il codice `{paziente_code}` non è stato trovato nel database.")
        st.info(f"Codici disponibili: {', '.join(list(db.keys())[:5])}...")
        st.stop()
    
    paziente_data = db[paziente_code]
    
    # Header con logo
    logo_path = os.path.join(BASE_DIR, "logo.png")
    if os.path.exists(logo_path):
        col_logo, col_title = st.columns([1, 3])
        with col_logo:
            st.image(logo_path, width=150)
        with col_title:
            st.title(f"Benvenuto, {paziente_data['nome']}!")
            st.markdown(f"**Motivo visita:** {paziente_data['motivo']}")
            st.markdown(f"**Data scheda:** {paziente_data['data_creazione']}")
    else:
        st.title(f"Benvenuto, {paziente_data['nome']}!")
        st.markdown(f"**Motivo visita:** {paziente_data['motivo']}")
        st.markdown(f"**Data scheda:** {paziente_data['data_creazione']}")
    st.divider()
    
    # Banner installazione app
    st.info("""
    [SUGGERIMENTO]: Aggiungi questa pagina alla Home del tuo telefono per un accesso più rapido!
    
    • **iPhone**: Safari → Condividi → "Aggiungi a Home"  
    • **Android**: Chrome → Menu (⋮) → "Installa app"
    """)
    
    # Carica progressi
    if "progressi" not in paziente_data:
        paziente_data["progressi"] = {}
    
    # Mostra esercizi
    scheda = paziente_data["scheda"]
    
    # Statistiche
    totale = len(scheda)
    completati = sum(1 for ex in scheda if paziente_data["progressi"].get(ex["nome"], False))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale esercizi", totale)
    with col2:
        st.metric("Completati", completati)
    with col3:
        progresso = int((completati / totale) * 100) if totale > 0 else 0
        st.metric("Progresso", f"{progresso}%")
    
    st.progress(progresso / 100)
    st.divider()
    
    # --------------------------------------------------
    # GRAFICI E ANALISI
    # --------------------------------------------------
    st.subheader("I tuoi progressi")
    
    # Raccolta dati per i grafici
    storico_data = paziente_data.get("storico", {})
    
    # Calcola tutte le date uniche e conta esercizi per data
    date_conteggio = {}
    tutte_date = []
    
    for esercizio_nome, date_list in storico_data.items():
        for data in date_list:
            tutte_date.append(data)
            if data in date_conteggio:
                date_conteggio[data] += 1
            else:
                date_conteggio[data] = 1
    
    # Ordina le date
    if tutte_date:
        tutte_date_uniche = sorted(list(set(tutte_date)), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
    else:
        tutte_date_uniche = []
    
    # Calcola streak (giorni consecutivi)
    def calcola_streak(date_list):
        if not date_list:
            return 0
        
        date_obj = [datetime.strptime(d, "%d/%m/%Y") for d in date_list]
        date_obj_sorted = sorted(date_obj, reverse=True)
        
        streak = 1
        oggi = datetime.now()
        
        # Check se l'ultima data è oggi o ieri
        ultima = date_obj_sorted[0]
        diff_giorni = (oggi - ultima).days
        
        if diff_giorni > 1:
            return 0  # Streak interrotto
        
        # Conta giorni consecutivi
        for i in range(len(date_obj_sorted) - 1):
            diff = (date_obj_sorted[i] - date_obj_sorted[i + 1]).days
            if diff == 1:
                streak += 1
            else:
                break
        
        return streak
    
    streak_attuale = calcola_streak(tutte_date_uniche)
    
    # Mostra streak con badge
    if streak_attuale > 0:
        st.success(f"🔥 **Streak attuale: {streak_attuale} {'giorno' if streak_attuale == 1 else 'giorni'} consecutivi!** Continua così! 💪")
    else:
        st.info("[INFO] Inizia il tuo streak completando un esercizio oggi!")
    
    # Bottone Report PDF
    st.markdown("---")
    if st.button("📄 Genera Report Progresso", type="secondary", use_container_width="stretch"):
        with st.spinner("Generazione report in corso..."):
            report_pdf = genera_report_progresso(paziente_data, paziente_code)
            st.download_button(
                "⬇️ Scarica Report PDF",
                report_pdf,
                file_name=f"Report_{paziente_data['nome'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width="stretch"
            )
    st.markdown("---")
    
    # TAB per diversi grafici
    tab1, tab2 = st.tabs(["📈 Andamento allenamenti", "📊 Dettaglio esercizi"])
    
    with tab1:
        if tutte_date_uniche:
            # Grafico a linee - Esercizi per giorno
            import pandas as pd
            
            # Prepara dati per il grafico
            date_per_grafico = []
            conteggio_per_grafico = []
            
            for data in tutte_date_uniche:
                date_per_grafico.append(data)
                conteggio_per_grafico.append(date_conteggio[data])
            
            df_grafico = pd.DataFrame({
                "Data": date_per_grafico,
                "Esercizi completati": conteggio_per_grafico
            })
            
            st.line_chart(df_grafico.set_index("Data"), height=300, use_container_width="stretch")
            
            # Statistiche aggiuntive
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Giorni totali allenamento", len(tutte_date_uniche))
            with col_stat2:
                media_esercizi = sum(conteggio_per_grafico) / len(conteggio_per_grafico)
                st.metric("Media esercizi/giorno", f"{media_esercizi:.1f}")
            with col_stat3:
                st.metric("Totale ripetizioni", sum(conteggio_per_grafico))
        else:
            st.info("📈 Il grafico apparirà quando inizierai a completare gli esercizi!")
    
    with tab2:
        # Grafico a barre - Completamento per esercizio
        if storico_data:
            st.markdown("**Quante volte hai fatto ogni esercizio:**")
            
            for esercizio in scheda:
                nome = esercizio["nome"]
                volte = len(storico_data.get(nome, []))
                
                # Barra di progresso personalizzata
                col_nome, col_barra, col_num = st.columns([3, 5, 1])
                with col_nome:
                    st.markdown(f"**{nome}**")
                with col_barra:
                    # Calcola percentuale rispetto al massimo
                    max_volte = max([len(v) for v in storico_data.values()]) if storico_data else 1
                    percentuale = (volte / max_volte) if max_volte > 0 else 0
                    st.progress(percentuale)
                with col_num:
                    st.markdown(f"**{volte}x**")
        else:
            st.info("📊 I dettagli appariranno quando completi gli esercizi!")
    
    st.divider()
    
    # Lista esercizi interattiva con card moderne
    st.subheader("I tuoi esercizi")
    for idx, ex in enumerate(scheda):
        # Card container con styling
        with st.container():
            st.markdown(f"""
            <div style='
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-left: 5px solid #2a5298;
            '>
                <h3 style='color: #1e3c72; margin-bottom: 1rem;'> {idx+1}. {ex['nome']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                img_path = trova_immagine(ex['nome'])
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width="stretch")
            
            with col_info:
                st.markdown(f"**Descrizione:** {ex['descrizione']}")
                st.markdown(f"   • Serie: {ex['serie']} | Ripetizioni: {ex['ripetizioni']}")
                
                # Badge difficoltà con colori
                difficolta = ex.get('difficoltà', 'N/A')
                color = {"Facile": "#4caf50", "Medio": "#ff9800", "Difficile": "#f44336"}.get(difficolta, "#9e9e9e")
                st.markdown(f"**Difficoltà:** <span style='background:{color};color:white;padding:0.25rem 0.75rem;border-radius:20px;font-weight:600;'>{difficolta}</span>", unsafe_allow_html=True)
     # Video embedded
                     
                video_link = ex["link_video"]

                # FIX: Converti YouTube Shorts in link normale
                if "/shorts/" in video_link:
                    video_id = video_link.split("/shorts/")[1].split("?")[0]
                    video_link = f"https://www.youtube.com/watch?v={video_id}"

                if "youtube.com" in video_link or "youtu.be" in video_link:
                    st.video(video_link)
                else:
                    video_path = os.path.join(VIDEO_DIR, f"{ex['nome']}.mp4")
                    if os.path.exists(video_path):
                        st.video(video_path)
                    else:
                        st.info("Video non disponibile")
```

---
            
            # Sistema contatore con storico date
            if "storico" not in paziente_data:
                paziente_data["storico"] = {}
            
            if ex["nome"] not in paziente_data["storico"]:
                paziente_data["storico"][ex["nome"]] = []
            
            storico_esercizio = paziente_data["storico"][ex["nome"]]
            volte_fatto = len(storico_esercizio)
            
            # Mostra statistiche
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.metric("Volte completato", volte_fatto)
            with col_stat2:
                if storico_esercizio:
                    ultima_volta = storico_esercizio[-1]
                    st.metric("Ultima volta", ultima_volta)
                else:
                    st.metric("Ultima volta", "Mai")
            
            # Bottone per segnare come fatto OGGI
            oggi = datetime.now().strftime("%d/%m/%Y")
            
            # Check se già fatto oggi
            gia_fatto_oggi = oggi in storico_esercizio
            
            if gia_fatto_oggi:
                st.success(f"✅ Già completato oggi ({oggi})! Ben fatto! 💪")
                
                # Bottone per annullare se per errore
                if st.button(f"Annulla completamento di oggi", key=f"undo_{paziente_code}_{ex['nome']}"):
                    paziente_data["storico"][ex["nome"]].remove(oggi)
                    db[paziente_code] = paziente_data
                    salva_database(db)
                    st.rerun()
            else:
                if st.button(f"Segna come completato oggi", key=f"done_{paziente_code}_{ex['nome']}", type="primary"):
                    # Aggiungi data di oggi
                    paziente_data["storico"][ex["nome"]].append(oggi)
                    
                    # Aggiorna anche il vecchio sistema progressi (per compatibilità)
                    if "progressi" not in paziente_data:
                        paziente_data["progressi"] = {}
                    paziente_data["progressi"][ex["nome"]] = True
                    
                    db[paziente_code] = paziente_data
                    salva_database(db)
                    st.success("🎉 Esercizio completato registrato!")
                    st.rerun()
            
            # Mostra storico completo (ultime 10 date)
            if volte_fatto > 0:
                with st.expander(f"📊 Storico completo ({volte_fatto} volte)"):
                    ultimi_10 = storico_esercizio[-10:][::-1]  # Ultimi 10, dal più recente
                    for data in ultimi_10:
                        st.markdown(f"✅ {data}")
                    if volte_fatto > 10:
                        st.caption(f"... e altre {volte_fatto - 10} volte")
        
        # Note paziente
        note_key = f"note_{paziente_code}_{ex['nome']}"
        note_salvate = paziente_data.get("note", {}).get(ex["nome"], "")
        
        with st.expander("Aggiungi note personali"):
            note = st.text_area(
                "Note o feedback su questo esercizio",
                value=note_salvate,
                key=note_key,
                height=100
            )
            if st.button(f"Salva nota", key=f"save_{note_key}"):
                if "note" not in paziente_data:
                    paziente_data["note"] = {}
                paziente_data["note"][ex["nome"]] = note
                db[paziente_code] = paziente_data
                salva_database(db)
                st.success("✓ Nota salvata!")
        
        # Upload video esecuzione
        with st.expander("📹 Carica video della tua esecuzione"):
            st.markdown("""
            **Carica un video mentre esegui l'esercizio**  
            Il fisioterapista lo vedrà e potrà darti feedback sulla tua tecnica.
            """)
            
            # Info video caricati
            if "video_pazienti" not in paziente_data:
                paziente_data["video_pazienti"] = {}
            
            if ex["nome"] not in paziente_data["video_pazienti"]:
                paziente_data["video_pazienti"][ex["nome"]] = []
            
            video_list = paziente_data["video_pazienti"][ex["nome"]]
            
            # Mostra video già caricati
            if video_list:
                st.markdown(f"**Video caricati ({len(video_list)}):**")
                for vid_idx, video_data in enumerate(video_list):
                    col_vid_info, col_vid_del = st.columns([4, 1])
                    with col_vid_info:
                        st.markdown(f"**{vid_idx + 1}.** Caricato il {video_data['data']} ({video_data.get('size_mb', 'N/A')} MB)")
                        
                        # Mostra video se disponibile
                        if video_data.get('blob_name'):
                            video_url = get_video_url(video_data['blob_name'])
                            if video_url:
                                st.video(video_url)
                        
                        if video_data.get('commento'):
                            st.caption(f"💬 \"{video_data['commento']}\"")
                        if video_data.get('feedback_fisio'):
                            st.info(f"**Feedback fisioterapista:** {video_data['feedback_fisio']}")
                    with col_vid_del:
                        if st.button("🗑️", key=f"del_vid_{paziente_code}_{ex['nome']}_{vid_idx}"):
                            # Elimina da cloud
                            if video_data.get('blob_name'):
                                delete_video_from_cloud(video_data['blob_name'])
                            # Elimina da database
                            paziente_data["video_pazienti"][ex["nome"]].pop(vid_idx)
                            db[paziente_code] = paziente_data
                            salva_database(db)
                            st.rerun()
                st.divider()
            
            # Form upload nuovo video
            st.markdown("**Carica nuovo video:**")
            
            uploaded_file = st.file_uploader(
                "Seleziona video (MP4, MOV, AVI - max 200MB)",
                type=['mp4', 'mov', 'avi'],
                key=f"upload_{paziente_code}_{ex['nome']}"
            )
            
            video_commento = st.text_area(
                "Aggiungi un commento (opzionale)",
                placeholder="Es: Prima volta che provo, il ginocchio fa ancora male...",
                key=f"commento_vid_{paziente_code}_{ex['nome']}",
                height=80
            )
            
            if uploaded_file is not None:
                # Preview video
                st.video(uploaded_file)
                
                # Info dimensione
                file_size_mb = uploaded_file.size / (1024*1024)
                if file_size_mb > 200:
                    st.error("⚠️ File troppo grande! Max 200MB")
                else:
                    st.caption(f"Dimensione: {file_size_mb:.2f} MB")
                
                if st.button("Carica video", key=f"upload_btn_{paziente_code}_{ex['nome']}", type="primary"):
                    with st.spinner("Caricamento in corso..."):
                        # Upload su Cloud Storage
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        cloud_data = upload_video_to_cloud(uploaded_file, paziente_code, ex['nome'], timestamp)
                        
                        if cloud_data:
                            # Salva info video nel database
                            video_info = {
                                "nome_file": uploaded_file.name,
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "commento": video_commento,
                                "feedback_fisio": "",
                                "blob_name": cloud_data['blob_name'],
                                "size_mb": cloud_data['size_mb']
                            }
                            
                            paziente_data["video_pazienti"][ex["nome"]].append(video_info)
                            db[paziente_code] = paziente_data
                            salva_database(db)
                            
                            st.success("✓ Video caricato con successo!")
                            st.info("Il fisioterapista riceverà una notifica e potrà vedere il video.")
                            st.rerun()
                        else:
                            st.error("Errore durante l'upload. Riprova.")
        
        st.divider()
    
    # Messaggio finale
    if completati == totale and totale > 0:
        st.success("Complimenti! Hai completato tutti gli esercizi!")

# --------------------------------------------------
# MODALITÀ FISIOTERAPISTA (creazione schede)
# --------------------------------------------------
else:
    # Header con logo per fisioterapista
    logo_path = os.path.join(BASE_DIR, "logo.png")
    if os.path.exists(logo_path):
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
            st.image(logo_path, width=120)
        with col_title:
            st.title("🏥 Riccardo Rispoli - Fisioterapia")
            st.markdown("**Area Fisioterapista** · Crea schede personalizzate per i tuoi pazienti")
    else:
        st.title("🏥 Programma esercizi personalizzato")
        st.markdown("**Area Fisioterapista** - Crea schede per i tuoi pazienti")
    
    st.divider()
    
    # --------------------------------------------------
    # DASHBOARD STATISTICHE
    # --------------------------------------------------
    st.subheader("📊 Dashboard Statistiche")
    
    db_stats = carica_database()
    
    if db_stats:
        # Calcola metriche
        totale_pazienti = len(db_stats)
        
        # Compliance media
        compliance_list = []
        pazienti_inattivi = []
        video_da_vedere = 0
        
        oggi = datetime.now()
        
        for codice, data in db_stats.items():
            # Compliance
            tot_ex = len(data.get("scheda", []))
            compl_ex = sum(1 for ex in data.get("scheda", []) if data.get("progressi", {}).get(ex["nome"], False))
            if tot_ex > 0:
                compliance_list.append((compl_ex / tot_ex) * 100)
            
            # Inattività (nessun esercizio negli ultimi 7 giorni)
            storico = data.get("storico", {})
            tutte_date = []
            for date_list in storico.values():
                tutte_date.extend(date_list)
            
            if tutte_date:
                date_obj = [datetime.strptime(d, "%d/%m/%Y") for d in tutte_date]
                ultima_data = max(date_obj)
                giorni_inattivo = (oggi - ultima_data).days
                if giorni_inattivo > 7:
                    pazienti_inattivi.append((data.get('nome', 'N/A'), giorni_inattivo))
            elif len(tutte_date) == 0 and data.get('data_creazione'):
                # Mai fatto esercizi
                pazienti_inattivi.append((data.get('nome', 'N/A'), 999))
            
            # Video da vedere
            video_pazienti = data.get("video_pazienti", {})
            for ex_videos in video_pazienti.values():
                for video in ex_videos:
                    if not video.get('feedback_fisio'):
                        video_da_vedere += 1
        
        compliance_media = sum(compliance_list) / len(compliance_list) if compliance_list else 0
        
        # Mostra metriche
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("👥 Totale pazienti", totale_pazienti)
        with col_m2:
            st.metric("📊 Compliance media", f"{compliance_media:.0f}%")
        with col_m3:
            st.metric("⚠️ Pazienti inattivi", len(pazienti_inattivi))
        with col_m4:
            st.metric("📹 Video da vedere", video_da_vedere)
        
        # Pazienti inattivi (se ci sono)
        if pazienti_inattivi:
            with st.expander(f"⚠️ Pazienti inattivi ({len(pazienti_inattivi)})"):
                for nome, giorni in sorted(pazienti_inattivi, key=lambda x: x[1], reverse=True):
                    if giorni == 999:
                        st.markdown(f"- **{nome}**: Mai iniziato")
                    else:
                        st.markdown(f"- **{nome}**: Inattivo da {giorni} giorni")
        
        st.divider()
    else:
        st.info("Nessun paziente registrato ancora")
    
    st.divider()
    
    # --------------------------------------------------
    # INPUT PAZIENTE
    # --------------------------------------------------
    col1, col2 = st.columns(2)
    
    with col1:
        nome_paziente = st.text_input("Nome e cognome paziente")
    
    with col2:
        motivo = st.text_input("🩺 Motivo della visita")
    
    st.divider()
    
    # --------------------------------------------------
    # TEMPLATE SCHEDE
    # --------------------------------------------------
    st.subheader("Template Schede")
    
    # Template predefiniti con distretto associato
    TEMPLATES = {
        "Nessun template (selezione manuale)": {
            "esercizi": [],
            "distretto": None
        },
        "Lombalgia acuta": {
            "esercizi": [
                {"nome": "Ponte glutei", "serie": 3, "ripetizioni": 12},
                {"nome": "Plank", "serie": 3, "ripetizioni": 30},
                {"nome": "Respirazione diaframmatica", "serie": 3, "ripetizioni": 10}
            ],
            "distretto": "schiena"
        },
        "Spalla dolorosa": {
            "esercizi": [
                {"nome": "Rotazioni spalla", "serie": 3, "ripetizioni": 10},
                {"nome": "Elevazioni laterali braccia", "serie": 3, "ripetizioni": 12},
                {"nome": "Stretching globale", "serie": 2, "ripetizioni": 30}
            ],
            "distretto": "spalla"
        },
        "Ginocchio post-trauma": {
            "esercizi": [
                {"nome": "Squat corpo libero", "serie": 3, "ripetizioni": 10},
                {"nome": "Affondi", "serie": 3, "ripetizioni": 10},
                {"nome": "Ponte glutei", "serie": 3, "ripetizioni": 12}
            ],
            "distretto": "ginocchio"
        },
        "Cervicalgia": {
            "esercizi": [
                {"nome": "Stretch laterale collo", "serie": 3, "ripetizioni": 10},
                {"nome": "Rotazioni cervicali", "serie": 3, "ripetizioni": 5},
                {"nome": "Respirazione diaframmatica", "serie": 3, "ripetizioni": 10}
            ],
            "distretto": "collo"
        },
        "Riabilitazione Core": {
            "esercizi": [
                {"nome": "Plank", "serie": 3, "ripetizioni": 30},
                {"nome": "Crunch", "serie": 3, "ripetizioni": 15},
                {"nome": "Ponte glutei", "serie": 3, "ripetizioni": 12}
            ],
            "distretto": "addome"
        }
    }
    
    # Selectbox template
    template_scelto = st.selectbox(
        "Scegli un template o seleziona manualmente",
        list(TEMPLATES.keys())
    )
    
    # Estrai dati template
    template_data = TEMPLATES[template_scelto]
    esercizi_template = template_data["esercizi"]
    distretto_suggerito = template_data["distretto"]
    
    if esercizi_template:
        st.success(f"✅ Template '{template_scelto}' caricato! Distretto auto-selezionato: **{distretto_suggerito}**")
        
        # Mostra preview template
        with st.expander("👁️ Preview esercizi del template"):
            for ex in esercizi_template:
                st.markdown(f"- **{ex['nome']}**: {ex['serie']} serie x {ex['ripetizioni']} rip")
    
    st.divider()
    
    # --------------------------------------------------
    # SELEZIONE ESERCIZI
    # --------------------------------------------------
    
    # Auto-selezione distretto basata sul template
    distretti_disponibili = sorted(df["distretto"].unique())
    
    if distretto_suggerito and distretto_suggerito in distretti_disponibili:
        # Pre-seleziona il distretto del template
        index_distretto = distretti_disponibili.index(distretto_suggerito)
    else:
        # Default: primo distretto
        index_distretto = 0
    
    distretto = st.selectbox(
        "Seleziona distretto",
        distretti_disponibili,
        index=index_distretto
    )
    
    # Mostra esercizi del distretto selezionato + esercizi "generale"
    df_distretto = df[(df["distretto"] == distretto) | (df["distretto"] == "generale")]
    
    # Se ha scelto un template, pre-seleziona SOLO gli esercizi disponibili nel distretto
    if esercizi_template:
        # Filtra solo esercizi che esistono nel distretto selezionato
        esercizi_disponibili = df_distretto["nome"].tolist()
        esercizi_template_nomi = [ex["nome"] for ex in esercizi_template if ex["nome"] in esercizi_disponibili]
        
        if esercizi_template_nomi:
            st.info(f"[INFO] {len(esercizi_template_nomi)} esercizi del template trovati nel distretto '{distretto}'")
        
        # Mostra warning se alcuni esercizi del template non sono disponibili
        esercizi_mancanti = [ex["nome"] for ex in esercizi_template if ex["nome"] not in esercizi_disponibili]
        if esercizi_mancanti:
            st.warning(f"[!] Alcuni esercizi del template non sono in questo distretto: {', '.join(esercizi_mancanti)}")
    else:
        esercizi_template_nomi = []
    
    esercizi_scelti = st.multiselect(
        "Seleziona esercizi",
        df_distretto["nome"].tolist(),
        default=esercizi_template_nomi
    )
    
    scheda = []
    for nome in esercizi_scelti:
        row = df_distretto[df_distretto["nome"] == nome].iloc[0]
        
        # Cerca se questo esercizio è nel template per usare i suoi valori
        template_ex = next((ex for ex in esercizi_template if ex["nome"] == nome), None)
        
        if template_ex:
            # Usa valori del template
            default_serie = template_ex["serie"]
            default_rip = template_ex["ripetizioni"]
        else:
            # Gestione sicura di serie e ripetizioni (possono essere vuote nel CSV)
            try:
                default_serie = int(row.get("serie", 3)) if row.get("serie") and str(row.get("serie")).strip() else 3
            except (ValueError, TypeError):
                default_serie = 3
            
            try:
                default_rip = int(row.get("ripetizioni", 10)) if row.get("ripetizioni") and str(row.get("ripetizioni")).strip() else 10
            except (ValueError, TypeError):
                default_rip = 10
        
        c1, c2 = st.columns(2)
        with c1:
            serie = st.number_input(f"Serie – {nome}", 1, 10, default_serie, key=f"serie_{nome}")
        with c2:
            rip = st.number_input(f"Ripetizioni – {nome}", 1, 30, default_rip, key=f"rip_{nome}")
        
        scheda.append({
            "nome": row["nome"],
            "descrizione": row["descrizione"],
            "link_video": row["link_video"],
            "difficoltà": row.get("difficoltà", ""),
            "distretto": row["distretto"],
            "serie": serie,
            "ripetizioni": rip
        })
    
    st.divider()
    
    # --------------------------------------------------
    # GENERA PDF MODERNO
    # --------------------------------------------------
    def draw_background_and_footer(canvas, doc):
        """Disegna sfondo e footer con design moderno"""
        # Sfondo bianco pulito (opzionale: sfondo.png se presente)
        bg_path = os.path.join(BASE_DIR, "background.png")
        if os.path.exists(bg_path):
            canvas.drawImage(bg_path, 0, 0, width=A4[0], height=A4[1], preserveAspectRatio=True, mask='auto')
        
        # Footer moderno
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColorRGB(0.4, 0.4, 0.4)
        
        # Linea separatore footer
        canvas.setStrokeColorRGB(0.12, 0.24, 0.45)  # Blu brand
        canvas.setLineWidth(1)
        canvas.line(2*cm, 1.8*cm, A4[0]-2*cm, 1.8*cm)
        
        # Testo footer
        canvas.drawCentredString(A4[0]/2, 1.3*cm, "Riccardo Rispoli – Fisioterapista OMPT")
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0]/2, 1.0*cm, "📧 riccardo.rspl@gmail.com  •  📱 +39 3313552300")
        
        # Numero pagina
        canvas.setFont("Helvetica-Bold", 8)
        page_num = canvas.getPageNumber()
        canvas.drawRightString(A4[0]-2*cm, 1.3*cm, f"Pagina {page_num}")
        
        canvas.restoreState()
    
    def genera_pdf(scheda):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=1.5*cm,
            bottomMargin=2.5*cm
        )
    
        # Stili moderni personalizzati
        styles = getSampleStyleSheet()
        
        # Titolo principale
        styles.add(ParagraphStyle(
            name="ModernTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=colors.HexColor("#1e3c72"),
            spaceAfter=12,
            leading=28
        ))
        
        # Sottotitolo
        styles.add(ParagraphStyle(
            name="Subtitle",
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#666666"),
            spaceAfter=20
        ))
        
        # Titolo esercizio
        styles.add(ParagraphStyle(
            name="ExerciseTitle",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor("#1e3c72"),
            spaceAfter=8,
            leading=16
        ))
        
        # Testo descrizione
        styles.add(ParagraphStyle(
            name="Description",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#333333"),
            leading=14,
            spaceAfter=8
        ))
        
        # Info esercizio (serie/rip)
        styles.add(ParagraphStyle(
            name="ExerciseInfo",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor("#2a5298"),
            spaceAfter=4
        ))
        
        story = []
    
        # ============ HEADER MODERNO ============
        logo_path = os.path.join(BASE_DIR, "logo.png")
        
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=4*cm, height=4*cm, kind="proportional")
            
            # Info paziente a destra del logo
            info_text = f"""
            <para align="left" spaceBefore="0">
            <font name="Helvetica-Bold" size="11" color="#1e3c72">PAZIENTE:</font>
            <font name="Helvetica" size="11" color="#333333"> {nome_paziente}</font><br/>
            <font name="Helvetica-Bold" size="11" color="#1e3c72">MOTIVO:</font>
            <font name="Helvetica" size="11" color="#333333"> {motivo}</font><br/>
            <font name="Helvetica-Bold" size="11" color="#1e3c72">DATA:</font>
            <font name="Helvetica" size="11" color="#333333"> {datetime.now().strftime("%d/%m/%Y")}</font>
            </para>
            """
            
            info_box = Paragraph(info_text, styles["Normal"])
            
            header_table = Table(
                [[logo, info_box]],
                colWidths=[5*cm, 12*cm],
                style=[
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING", (0,0), (-1,-1), 0),
                    ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ]
            )
            story.append(header_table)
        else:
            # Solo testo se non c'è logo
            story.append(Paragraph("Programma Esercizi Personalizzato", styles["ModernTitle"]))
            story.append(Paragraph(f"Paziente: {nome_paziente} | Motivo: {motivo}", styles["Subtitle"]))
        
        # Linea separatore sotto header
        story.append(Spacer(1, 10))
        separator_line = Table(
            [[""]],
            colWidths=[17*cm],
            style=[
                ("LINEABOVE", (0,0), (-1,-1), 2, colors.HexColor("#2a5298")),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 0)
            ]
        )
        story.append(separator_line)
        story.append(Spacer(1, 20))
    
        # ============ ESERCIZI CON LAYOUT MODERNO ============
        for idx, ex in enumerate(scheda):
            # Numerazione esercizio
            num_badge = Paragraph(
                f'<para align="center"><font name="Helvetica-Bold" size="16" color="white">#{idx+1}</font></para>',
                styles["Normal"]
            )
            
            # Titolo esercizio
            titolo = Paragraph(f"<b>{ex['nome']}</b>", styles["ExerciseTitle"])
            
            # Descrizione
            descrizione = Paragraph(ex['descrizione'], styles["Description"])
            
            # Info serie e ripetizioni con icone
            info_serie_rip = Paragraph(
                f"""
                <para>
                <font name="Helvetica-Bold" size="10" color="#2a5298">Serie:</font> 
                <font name="Helvetica-Bold" size="12" color="#1e3c72">{ex['serie']}</font>
                &nbsp;&nbsp;&nbsp;&nbsp;
                <font name="Helvetica-Bold" size="10" color="#2a5298">Ripetizioni:</font> 
                <font name="Helvetica-Bold" size="12" color="#1e3c72">{ex['ripetizioni']}</font>
                </para>
                """,
                styles["Normal"]
            )
            
            # Difficoltà con badge colorato
            difficolta = ex.get('difficoltà', 'N/A')
            color_map = {
                "Facile": "#4caf50",
                "Medio": "#ff9800", 
                "Difficile": "#f44336"
            }
            diff_color = color_map.get(difficolta, "#9e9e9e")
            
            badge_difficolta = Paragraph(
                f'<para><font name="Helvetica-Bold" size="9" color="white" backColor="{diff_color}"> {difficolta.upper()} </font></para>',
                styles["Normal"]
            )
            
            # Immagine esercizio
            img_path = trova_immagine(ex['nome'])
            if img_path and os.path.exists(img_path):
                esercizio_img = Image(img_path, width=5*cm, height=5*cm, kind="proportional")
            else:
                # Placeholder se non c'è immagine
                esercizio_img = Paragraph(
                    '<para align="center"><font size="40" color="#cccccc">📷</font><br/><font size="8" color="#999999">Immagine<br/>non disponibile</font></para>',
                    styles["Normal"]
                )
            
            # QR Code
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(ex["link_video"])
            qr.make(fit=True)
            qr_img_pil = qr.make_image(fill_color="black", back_color="white")
            qr_buf = io.BytesIO()
            qr_img_pil.save(qr_buf, format='PNG')
            qr_buf.seek(0)
            qr_img = Image(qr_buf, width=3*cm, height=3*cm)
            
            # Label QR
            qr_label = Paragraph(
                '<para align="center"><font name="Helvetica" size="7" color="#666666">Scansiona per<br/>vedere il video</font></para>',
                styles["Normal"]
            )
            
            # Colonna sinistra: Badge numero + Info esercizio
            left_content = [
                [num_badge],
                [titolo],
                [descrizione],
                [Spacer(1, 8)],
                [info_serie_rip],
                [Spacer(1, 4)],
                [badge_difficolta]
            ]
            
            left_table = Table(
                left_content,
                colWidths=[9*cm],
                style=[
                    ("LEFTPADDING", (0,0), (-1,-1), 0),
                    ("RIGHTPADDING", (0,0), (-1,-1), 0),
                    ("TOPPADDING", (0,0), (-1,-1), 2),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                    # Badge colorato
                    ("BACKGROUND", (0,0), (0,0), colors.HexColor("#2a5298")),
                    ("ALIGN", (0,0), (0,0), "CENTER"),
                    ("VALIGN", (0,0), (0,0), "MIDDLE"),
                    ("TOPPADDING", (0,0), (0,0), 8),
                    ("BOTTOMPADDING", (0,0), (0,0), 8),
                ]
            )
            
            # Colonna destra: Immagine + QR
            right_content = [
                [esercizio_img],
                [Spacer(1, 8)],
                [qr_img],
                [qr_label]
            ]
            
            right_table = Table(
                right_content,
                colWidths=[5*cm],
                style=[
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING", (0,0), (-1,-1), 0),
                    ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ]
            )
            
            # Card esercizio completa
            exercise_card = Table(
                [[left_table, right_table]],
                colWidths=[9.5*cm, 5.5*cm],
                style=[
                    ("BOX", (0,0), (-1,-1), 1.5, colors.HexColor("#2a5298")),
                    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f8f9fa")),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING", (0,0), (-1,-1), 12),
                    ("RIGHTPADDING", (0,0), (-1,-1), 12),
                    ("TOPPADDING", (0,0), (-1,-1), 12),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 12),
                ]
            )
            
            story.append(KeepTogether([exercise_card]))
            story.append(Spacer(1, 15))
            
            # PageBreak ogni 3 esercizi
            if (idx + 1) % 3 == 0 and idx < len(scheda) - 1:
                story.append(PageBreak())
    
        # Build PDF
        doc.build(
            story,
            onFirstPage=draw_background_and_footer,
            onLaterPages=draw_background_and_footer
        )
    
        buffer.seek(0)
        return buffer
    
    # --------------------------------------------------
    # BOTTONI AZIONI
    # --------------------------------------------------
    if scheda and nome_paziente:
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Genera PDF", type="primary"):
                pdf = genera_pdf(scheda)
                filename = f"{nome_paziente.replace(' ', '_')}_esercizi.pdf"
                st.download_button(
                    "⬇️ Scarica PDF",
                    pdf,
                    file_name=filename,
                    mime="application/pdf"
                )
        
        with col_btn2:
            if st.button("Crea link paziente", type="primary"):
                # Salva nel database
                db = carica_database()
                codice = genera_codice_paziente(nome_paziente)
                
                db[codice] = {
                    "nome": nome_paziente,
                    "motivo": motivo,
                    "scheda": scheda,
                    "data_creazione": datetime.now().strftime("%d/%m/%Y"),
                    "progressi": {},
                    "note": {},
                    "video_pazienti": {}
                }
                
                salva_database(db)
                
                # Mostra link con parametro corto per PWA
                app_url = "https://schede-pazienti-app.streamlit.app"
                link_paziente = f"{app_url}?p={codice}"
                link_completo = f"{app_url}?paziente={codice}"  # Backup
                
                st.success(f"✅ Scheda creata per {nome_paziente}!")
                
                # Link principale (corto per installazione)
                st.markdown("### 📱 Link per il paziente:")
                st.code(link_paziente, language=None)
                st.markdown("""
                **Come inviare al paziente:**
                1. Copia il link qui sopra
                2. Invialo via WhatsApp/SMS/Email
                3. Il paziente può **aggiungerlo alla Home** del telefono:
                   - **iPhone**: Safari → Condividi → "Aggiungi a Home"
                   - **Android**: Chrome → ⋮ → "Installa app"
                """)
                
                # Link alternativo lungo
                with st.expander("🔗 Link alternativo (lungo)"):
                    st.code(link_completo, language=None)
                
                # QR Code per il link
                qr = qrcode.make(link_paziente)
                qr_buf = io.BytesIO()
                qr.save(qr_buf, format="PNG")
                qr_buf.seek(0)
                st.image(qr_buf, caption="QR Code per accesso rapido", width=300)
    
    # --------------------------------------------------
    # GESTIONE PAZIENTI ESISTENTI
    # --------------------------------------------------
    st.divider()
    st.subheader("Pazienti registrati")
    
    db = carica_database()
    
    if db:
        for codice, data in db.items():
            with st.expander(f"👤 {data['nome']} - {data['motivo']} ({data['data_creazione']})"):
                st.markdown(f"**Codice:** `{codice}`")
                
                totale = len(data["scheda"])
                completati = sum(1 for ex in data["scheda"] if data.get("progressi", {}).get(ex["nome"], False))
                progresso = int((completati / totale) * 100) if totale > 0 else 0
                
                st.progress(progresso / 100)
                st.markdown(f"**Progresso:** {completati}/{totale} esercizi completati ({progresso}%)")
                
                # Link paziente
                app_url = "https://schede-pazienti-app.streamlit.app"
                link_paziente = f"{app_url}?p={codice}"
                st.code(link_paziente, language=None)
                
                # Ottieni URL dinamicamente
                import streamlit as st
                app_url = st.get_option("browser.serverAddress") or "https://schede-pazienti-app.streamlit.app" 

                # Dettaglio esercizi con note e statistiche
                st.markdown("---")
                st.markdown("### 📋 Dettaglio esercizi:")
                
                for idx, ex in enumerate(data["scheda"]):
                    nome_ex = ex["nome"]
                    is_done = data.get("progressi", {}).get(nome_ex, False)
                    nota_paziente = data.get("note", {}).get(nome_ex, "")
                    
                    # Storico esercizio
                    storico_esercizio = data.get("storico", {}).get(nome_ex, [])
                    volte_fatto = len(storico_esercizio)
                    
                    # Status icon basato su storico
                    if volte_fatto > 0:
                        icon = "✅"
                        status_text = f"(fatto {volte_fatto} {'volta' if volte_fatto == 1 else 'volte'})"
                    else:
                        icon = "⬜"
                        status_text = "(non ancora fatto)"
                    
                    st.markdown(f"**{idx+1}. {icon} {nome_ex}** {status_text}")
                    st.markdown(f"   • **Serie:** {ex['serie']} | **Ripetizioni:** {ex['ripetizioni']}")
                    
                    # Mostra ultime date se presente
                    if volte_fatto > 0:
                        ultima_volta = storico_esercizio[-1]
                        st.markdown(f"   • Ultima volta: **{ultima_volta}**")
                        
                        # Mostra tutte le date in un expander
                        if volte_fatto > 1:
                            with st.expander(f"   📊 Tutte le date ({volte_fatto} volte)"):
                                ultimi_date = storico_esercizio[::-1]  # Dal più recente
                                for data_es in ultimi_date:
                                    st.markdown(f"   • {data_es}")
                    
                    # Mostra note del paziente se presenti
                    if nota_paziente:
                        st.info(f"**Nota del paziente:** {nota_paziente}")
                    
                    # Mostra video caricati dal paziente
                    video_list = data.get("video_pazienti", {}).get(nome_ex, [])
                    if video_list:
                        with st.expander(f"   📹 Video caricati dal paziente ({len(video_list)})"):
                            for vid_idx, video_data in enumerate(video_list):
                                st.markdown(f"**Video {vid_idx + 1}** - Caricato il {video_data['data']} ({video_data.get('size_mb', 'N/A')} MB)")
                                
                                # Mostra video
                                if video_data.get('blob_name'):
                                    video_url = get_video_url(video_data['blob_name'])
                                    if video_url:
                                        st.video(video_url)
                                    else:
                                        st.warning("Video non disponibile")
                                
                                if video_data.get('commento'):
                                    st.markdown(f"💬 *\"{video_data['commento']}\"*")
                                
                                # Feedback del fisioterapista
                                current_feedback = video_data.get('feedback_fisio', '')
                                feedback = st.text_area(
                                    "Il tuo feedback:",
                                    value=current_feedback,
                                    key=f"feedback_{codice}_{nome_ex}_{vid_idx}",
                                    height=80,
                                    placeholder="Es: Ottima esecuzione! Presta attenzione all'allineamento del ginocchio..."
                                )
                                
                                if st.button("Salva feedback", key=f"save_fb_{codice}_{nome_ex}_{vid_idx}"):
                                    data["video_pazienti"][nome_ex][vid_idx]["feedback_fisio"] = feedback
                                    db[codice] = data
                                    salva_database(db)
                                    st.success("✓ Feedback salvato! Il paziente lo vedrà.")
                                
                                st.markdown("---")
                    
                    st.markdown("")  # Spazio
                
                # Bottone elimina
                st.markdown("---")
                if st.button(f"Elimina paziente", key=f"del_{codice}"):
                    del db[codice]
                    salva_database(db)
                    st.rerun()
    else:
        st.info("Nessun paziente registrato ancora")
