import streamlit as st
import pandas as pd
import os
import io
import qrcode

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors


# --------------------------------------------------
# CONFIG STREAMLIT
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
# BACKGROUND PDF
# --------------------------------------------------
def draw_background(canvas, doc):
    if os.path.exists("background.png"):
        canvas.drawImage(
            "background.png",
            0,
            0,
            width=A4[0],
            height=A4[1]
        )


# --------------------------------------------------
# GENERA PDF
# --------------------------------------------------
def genera_pdf(scheda):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Titolo",
        fontSize=18,
        alignment=1,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="Bold",
        fontSize=11,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Testo",
        fontSize=10,
        leading=14
    ))

    story = []

    # LOGO LOCALE (SAFE)
    if os.path.exists("logo.png"):
        story.append(Image("logo.png", width=4 * cm, height=2 * cm))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Programma esercizi personalizzato", styles["Titolo"]))

    story.append(Paragraph(f"<b>Paziente:</b> {nome_paziente}", styles["Testo"]))
    story.append(Paragraph(f"<b>Motivo:</b> {motivo}", styles["Testo"]))
    story.append(Spacer(1, 12))

    story.append(Table(
        [[""]],
        colWidths=[16 * cm],
        style=[("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey)]
    ))

    story.append(Spacer(1, 14))

    for ex in scheda:
        qr = qrcode.make(ex["link_video"])
        qr_buf = io.BytesIO()
        qr.save(qr_buf)
        qr_buf.seek(0)

        qr_img = Image(qr_buf, width=3 * cm, height=3 * cm)

        testo = [
            Paragraph(ex["nome"], styles["Bold"]),
            Paragraph(f"Serie: {ex['serie']} – Ripetizioni: {ex['ripetizioni']}", styles["Testo"]),
            Paragraph(ex["descrizione"], styles["Testo"])
        ]

        card = Table(
            [[qr_img, testo]],
            colWidths=[3.5 * cm, 11.5 * cm],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        story.append(card)
        story.append(Spacer(1, 12))

    doc.build(
        story,
        onFirstPage=draw_background,
        onLaterPages=draw_background
    )

    buffer.seek(0)
    return buffer


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------
if st.button("Genera PDF") and scheda:
    pdf = genera_pdf(scheda)
    st.download_button(
        "Scarica PDF",
        pdf,
        file_name="programma_esercizi.pdf",
        mime="application/pdf"
    )
