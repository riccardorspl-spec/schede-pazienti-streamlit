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
    layout="wide",
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

def carica_database():
    """Carica tutti i pazienti da Google Sheets"""
    try:
        worksheet = get_google_sheet()
        if not worksheet:
            return {}
        
        # Ottieni tutti i record
        records = worksheet.get_all_records()
        
        # Converti in dizionario con codice come chiave
        db = {}
        for record in records:
            codice = record.get('codice')
            if codice:
                db[codice] = {
                    'nome': record.get('nome', ''),
                    'motivo': record.get('motivo', ''),
                    'data_creazione': record.get('data_creazione', ''),
                    'scheda': json.loads(record.get('scheda', '[]')),
                    'progressi': json.loads(record.get('progressi', '{}')),
                    'note': json.loads(record.get('note', '{}'))
                }
        
        return db
    except Exception as e:
        st.error(f"Errore caricamento database: {e}")
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
                json.dumps(data.get('note', {}), ensure_ascii=False)
            ])
        
        # Cancella tutto tranne l'intestazione
        worksheet.clear()
        
        # Scrivi intestazione
        worksheet.append_row(['codice', 'nome', 'motivo', 'data_creazione', 'scheda', 'progressi', 'note'])
        
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
    
    if paziente_code not in db:
        st.error("❌ Codice paziente non valido!")
        st.stop()
    
    paziente_data = db[paziente_code]
    
    # Header con logo
    logo_path = os.path.join(BASE_DIR, "logo.png")
    if os.path.exists(logo_path):
        col_logo, col_title = st.columns([1, 3])
        with col_logo:
            st.image(logo_path, width=150)
        with col_title:
            st.title(f"💪 Ciao {paziente_data['nome']}!")
            st.markdown(f"**🩺 Motivo:** {paziente_data['motivo']}")
            st.markdown(f"**📅 Data scheda:** {paziente_data['data_creazione']}")
    else:
        st.title(f"💪 Ciao {paziente_data['nome']}!")
        st.markdown(f"**🩺 Motivo:** {paziente_data['motivo']}")
        st.markdown(f"**📅 Data scheda:** {paziente_data['data_creazione']}")
    st.divider()
    
    # Banner installazione app
    st.info("""
    📱 **Consiglio**: Aggiungi questa pagina alla Home del tuo telefono per un accesso più rapido!
    
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
        st.metric("📋 Totale esercizi", totale)
    with col2:
        st.metric("✅ Completati", completati)
    with col3:
        progresso = int((completati / totale) * 100) if totale > 0 else 0
        st.metric("📊 Progresso", f"{progresso}%")
    
    st.progress(progresso / 100)
    st.divider()
    
    # Lista esercizi interattiva con card moderne
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
                <h3 style='color: #1e3c72; margin-bottom: 1rem;'>🏋️ {idx+1}. {ex['nome']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                img_path = trova_immagine(ex['nome'])
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
            
            with col_info:
                st.markdown(f"**📝 Descrizione:** {ex['descrizione']}")
                st.markdown(f"**🔢 Serie:** `{ex['serie']}` | **🔁 Ripetizioni:** `{ex['ripetizioni']}`")
                
                # Badge difficoltà con colori
                difficolta = ex.get('difficoltà', 'N/A')
                color = {"Facile": "#4caf50", "Medio": "#ff9800", "Difficile": "#f44336"}.get(difficolta, "#9e9e9e")
                st.markdown(f"**📈 Difficoltà:** <span style='background:{color};color:white;padding:0.25rem 0.75rem;border-radius:20px;font-weight:600;'>{difficolta}</span>", unsafe_allow_html=True)
            
            # Video embedded
            if "youtube.com" in ex["link_video"] or "youtu.be" in ex["link_video"]:
                st.video(ex["link_video"])
            else:
                video_path = os.path.join(VIDEO_DIR, f"{ex['nome']}.mp4")
                if os.path.exists(video_path):
                    st.video(video_path)
                else:
                    st.info("📹 Video non disponibile")
            
            # Checkbox "fatto" con salvataggio automatico
            checkbox_key = f"check_{paziente_code}_{ex['nome']}"
            is_done = paziente_data["progressi"].get(ex["nome"], False)
        
        fatto = st.checkbox("✅ Esercizio completato", value=is_done, key=checkbox_key)
        
        if fatto != is_done:
            paziente_data["progressi"][ex["nome"]] = fatto
            db[paziente_code] = paziente_data
            salva_database(db)
            if fatto:
                st.success("💪 Ben fatto! Esercizio segnato come completato")
                st.balloons()
            else:
                st.info("Esercizio rimosso dai completati")
        
        # Note paziente
        note_key = f"note_{paziente_code}_{ex['nome']}"
        note_salvate = paziente_data.get("note", {}).get(ex["nome"], "")
        
        with st.expander("📝 Aggiungi note personali"):
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
                st.success("✅ Nota salvata!")
        
        st.divider()
    
    # Messaggio finale
    if completati == totale and totale > 0:
        st.success("🎉 Complimenti! Hai completato tutti gli esercizi! 🎉")
        st.balloons()

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
    # INPUT PAZIENTE
    # --------------------------------------------------
    col1, col2 = st.columns(2)
    
    with col1:
        nome_paziente = st.text_input("👤 Nome e cognome paziente")
    
    with col2:
        motivo = st.text_input("🩺 Motivo della visita")
    
    st.divider()
    
    # --------------------------------------------------
    # SELEZIONE ESERCIZI
    # --------------------------------------------------
    distretto = st.selectbox(
        "🎯 Seleziona distretto",
        sorted(df["distretto"].unique())
    )
    
    # Mostra esercizi del distretto selezionato + esercizi "generale"
    df_distretto = df[(df["distretto"] == distretto) | (df["distretto"] == "generale")]
    
    esercizi_scelti = st.multiselect(
        "📋 Seleziona esercizi",
        df_distretto["nome"].tolist()
    )
    
    scheda = []
    for nome in esercizi_scelti:
        row = df_distretto[df_distretto["nome"] == nome].iloc[0]
        
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
            serie = st.number_input(f"Serie – {nome}", 1, 10, default_serie)
        with c2:
            rip = st.number_input(f"Ripetizioni – {nome}", 1, 30, default_rip)
        
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
        canvas.drawCentredString(A4[0]/2, 1.0*cm, "📧 info@riccardorispoli.it  •  📱 +39 XXX XXX XXXX")
        
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
                <font name="Helvetica-Bold" size="10" color="#2a5298">🔢 Serie:</font> 
                <font name="Helvetica-Bold" size="12" color="#1e3c72">{ex['serie']}</font>
                &nbsp;&nbsp;&nbsp;&nbsp;
                <font name="Helvetica-Bold" size="10" color="#2a5298">🔁 Ripetizioni:</font> 
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
            if st.button("📄 Genera PDF", type="primary"):
                pdf = genera_pdf(scheda)
                filename = f"{nome_paziente.replace(' ', '_')}_esercizi.pdf"
                st.download_button(
                    "⬇️ Scarica PDF",
                    pdf,
                    file_name=filename,
                    mime="application/pdf"
                )
        
        with col_btn2:
            if st.button("🔗 Crea link paziente", type="primary"):
                # Salva nel database
                db = carica_database()
                codice = genera_codice_paziente(nome_paziente)
                
                db[codice] = {
                    "nome": nome_paziente,
                    "motivo": motivo,
                    "scheda": scheda,
                    "data_creazione": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "progressi": {},
                    "note": {}
                }
                
                salva_database(db)
                
                # Mostra link con parametro corto per PWA
                app_url = "https://schede-pazienti-studiosauro.streamlit.app"
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
    st.subheader("📊 Pazienti registrati")
    
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
                
                app_url = "https://schede-pazienti-studiosauro.streamlit.app"
                link_paziente = f"{app_url}?p={codice}"
                st.code(link_paziente, language=None)
                
                if st.button(f"🗑️ Elimina paziente", key=f"del_{codice}"):
                    del db[codice]
                    salva_database(db)
                    st.rerun()
    else:
        st.info("Nessun paziente registrato ancora")
