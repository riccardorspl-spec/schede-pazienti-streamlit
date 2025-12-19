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
# STREAMLIT CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Programma esercizi personalizzato", layout="wide")

# --------------------------------------------------
# DATABASE PAZIENTI (JSON)
# --------------------------------------------------
DATABASE_FILE = "pazienti_database.json"

def carica_database():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salva_database(db):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def genera_codice_paziente(nome_paziente):
    """Genera un codice univoco per il paziente"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{nome_paziente}{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]

# --------------------------------------------------
# LOAD CSV
# --------------------------------------------------
@st.cache_data(ttl=60)  # Cache solo 60 secondi
def load_csv():
    df = pd.read_csv("esercizi.csv")
    df = df.fillna("")
    df["distretto"] = df["distretto"].astype(str)
    return df

df = load_csv()

# --------------------------------------------------
# ROUTING: FISIOTERAPISTA vs PAZIENTE
# --------------------------------------------------
query_params = st.query_params
paziente_code = query_params.get("paziente", None)

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
    
    # Header personalizzato
    st.title(f"💪 Ciao {paziente_data['nome']}!")
    st.markdown(f"**Motivo:** {paziente_data['motivo']}")
    st.markdown(f"**Data scheda:** {paziente_data['data_creazione']}")
    st.divider()
    
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
    
    # Lista esercizi interattiva
    for idx, ex in enumerate(scheda):
        st.markdown(f"### {idx+1}. {ex['nome']}")
        
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            img_path = trova_immagine(ex['nome'])
            if img_path and os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
        
        with col_info:
            st.markdown(f"**Descrizione:** {ex['descrizione']}")
            st.markdown(f"**🔢 Serie:** {ex['serie']} | **🔁 Ripetizioni:** {ex['ripetizioni']}")
            st.markdown(f"**📈 Difficoltà:** {ex.get('difficoltà', 'N/A')}")
        
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
    # GENERA PDF (funzioni esistenti)
    # --------------------------------------------------
    def draw_background(canvas, doc):
        bg_path = os.path.join(BASE_DIR, "background.png")
        if os.path.exists(bg_path):
            canvas.drawImage(bg_path, 0, 0, width=A4[0], height=A4[1])
    
    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0]/2, 1.2*cm, "Riccardo Rispoli – Fisioterapista OMPT")
        canvas.restoreState()
    
    def draw_background_and_footer(canvas, doc):
        draw_background(canvas, doc)
        draw_footer(canvas, doc)
    
    def genera_pdf(scheda):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
    
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="HeaderTitle", fontSize=18, leading=22))
        styles.add(ParagraphStyle(name="Bold", fontSize=11, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="Testo", fontSize=10, leading=14))
    
        story = []
    
        # Header
        logo_path = os.path.join(BASE_DIR, "logo.png")
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=3.5*cm, height=3.5*cm, kind="proportional")
        else:
            logo = Spacer(3.5*cm, 3.5*cm)
    
        title = Paragraph("<b>Programma esercizi personalizzato</b>", styles["HeaderTitle"])
        header = Table(
            [[logo, title]],
            colWidths=[4*cm, 12*cm],
            style=[
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0)
            ]
        )
        story.append(header)
        story.append(Table([[""]], colWidths=[16*cm], style=[("LINEBELOW",(0,0),(-1,-1),0.5,colors.grey)]))
        story.append(Spacer(1,12))
        story.append(Paragraph(f"<b>Paziente:</b> {nome_paziente}", styles["Testo"]))
        story.append(Paragraph(f"<b>Motivo:</b> {motivo}", styles["Testo"]))
        story.append(Spacer(1,16))
    
        # Esercizi
        for idx, ex in enumerate(scheda):
            img_path = trova_immagine(ex['nome'])
            if img_path:
                esercizio_img = Image(img_path, width=3.5*cm, height=3.5*cm, kind="proportional")
            else:
                esercizio_img = Spacer(3.5*cm, 3.5*cm)
    
            qr = qrcode.make(ex["link_video"])
            qr_buf = io.BytesIO()
            qr.save(qr_buf)
            qr_buf.seek(0)
            qr_img = Image(qr_buf, width=2.5*cm, height=2.5*cm, kind="proportional")
    
            testo = Paragraph(
                f"<b>{ex['nome']}</b><br/>{ex['descrizione']}<br/><br/>"
                f"<b>Serie:</b> {ex['serie']} &nbsp;&nbsp; <b>Ripetizioni:</b> {ex['ripetizioni']}",
                styles["Testo"]
            )
    
            card = Table(
                [[esercizio_img, testo, qr_img]],
                colWidths=[4*cm, 9*cm, 3*cm],
                style=[
                    ("BOX", (0,0), (-1,-1), 0.5, colors.lightgrey),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING", (0,0), (-1,-1), 6),
                    ("RIGHTPADDING", (0,0), (-1,-1), 6),
                    ("TOPPADDING", (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 6)
                ]
            )
    
            story.append(KeepTogether([card, Spacer(1,14)]))
            if (idx+1) % 4 == 0:
                story.append(PageBreak())
    
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
                
                # Mostra link
                app_url = "http://localhost:8501"  # Cambia con il tuo URL Streamlit Cloud
                link_paziente = f"{app_url}?paziente={codice}"
                
                st.success(f"✅ Scheda creata per {nome_paziente}!")
                st.code(link_paziente, language=None)
                st.markdown(f"**Invia questo link al paziente via WhatsApp o email** 📱")
                
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
                
                app_url = "http://localhost:8501"
                link_paziente = f"{app_url}?paziente={codice}"
                st.code(link_paziente, language=None)
                
                if st.button(f"🗑️ Elimina paziente", key=f"del_{codice}"):
                    del db[codice]
                    salva_database(db)
                    st.rerun()
    else:
        st.info("Nessun paziente registrato ancora")
