import streamlit as st
import pandas as pd
import os
import io
import qrcode
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
st.set_page_config(page_title="Programma esercizi personalizzato")
st.title("Programma esercizi personalizzato")
st.divider()

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
# INPUT PAZIENTE
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    nome_paziente = st.text_input("Nome e cognome paziente")

with col2:
    motivo = st.text_input("Motivo della visita")

st.divider()

# --------------------------------------------------
# SELEZIONE ESERCIZI
# --------------------------------------------------
distretto = st.selectbox(
    "Seleziona distretto",
    sorted(df["distretto"].unique())
)

df_distretto = df[df["distretto"] == distretto]

esercizi_scelti = st.multiselect(
    "Seleziona esercizi",
    df_distretto["nome"].tolist()
)

scheda = []
for nome in esercizi_scelti:
    row = df_distretto[df_distretto["nome"] == nome].iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        serie = st.number_input(f"Serie – {nome}", 1, 10, 3)
    with c2:
        rip = st.number_input(f"Ripetizioni – {nome}", 1, 30, 10)

    scheda.append({
        **row,
        "serie": serie,
        "ripetizioni": rip
    })

# --------------------------------------------------
# FUNZIONE TROVA IMMAGINE INTELLIGENTE
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")

def trova_immagine(nome_esercizio):
    """
    Cerca un'immagine nella cartella IMAGE_DIR che corrisponda al nome dell'esercizio.
    Supporta .jpg, .jpeg, .png, ignora maiuscole/minuscole e spazi extra.
    """
    nome_norm = nome_esercizio.strip().lower().replace(" ", "")
    if not os.path.exists(IMAGE_DIR):
        return None
    for file in os.listdir(IMAGE_DIR):
        file_norm = os.path.splitext(file)[0].strip().lower().replace(" ", "")
        if nome_norm == file_norm:
            return os.path.join(IMAGE_DIR, file)
    return None

# --------------------------------------------------
# BACKGROUND E FOOTER
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

# --------------------------------------------------
# GENERA PDF
# --------------------------------------------------
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

    # ---------------- HEADER ----------------
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

    # ---------------- ESERCIZI ----------------
    for idx, ex in enumerate(scheda):
        # immagine esercizio
        img_path = trova_immagine(ex['nome'])
        if img_path:
            esercizio_img = Image(img_path, width=3.5*cm, height=3.5*cm, kind="proportional")
        else:
            st.warning(f"Nessuna immagine trovata per '{ex['nome']}'")
            esercizio_img = Spacer(3.5*cm, 3.5*cm)

        # QR
        qr = qrcode.make(ex["link_video"])
        qr_buf = io.BytesIO()
        qr.save(qr_buf)
        qr_buf.seek(0)
        qr_img = Image(qr_buf, width=2.5*cm, height=2.5*cm, kind="proportional")

        # testo
        testo = Paragraph(
            f"<b>{ex['nome']}</b><br/>{ex['descrizione']}<br/><br/>"
            f"<b>Serie:</b> {ex['serie']} &nbsp;&nbsp; <b>Ripetizioni:</b> {ex['ripetizioni']}",
            styles["Testo"]
        )

        # card esercizio
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

        # PageBreak ogni 4 esercizi
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
# DOWNLOAD
# --------------------------------------------------
if st.button("Genera PDF") and scheda:
    pdf = genera_pdf(scheda)
    filename = f"{nome_paziente.replace(' ', '_')}_esercizi.pdf"
    st.download_button(
        "Scarica PDF",
        pdf,
        file_name=filename,
        mime="application/pdf"
    )

    )

