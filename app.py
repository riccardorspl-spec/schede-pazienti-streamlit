import streamlit as st
import pandas as pd
import os
import io
import qrcode

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors


# --------------------------------------------------
# CONFIG STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="Programma esercizi personalizzato",
    layout="centered"
)

st.title("Programma esercizi personalizzato")
st.divider()


# --------------------------------------------------
# CARICAMENTO E VALIDAZIONE CSV
# --------------------------------------------------
@st.cache_data
def load_csv():
    df = pd.read_csv("esercizi.csv")

    required_cols = [
        "distretto",
        "nome",
        "difficoltà",
        "descrizione",
        "link_video"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Colonna mancante nel CSV: {col}")

    df = df.fillna("")
    return df


df = load_csv()

distretti = sorted(df["distretto"].unique())
distretto_sel = st.selectbox("Seleziona il distretto", distretti)

esercizi_sel = df[df["distretto"] == distretto_sel]


# --------------------------------------------------
# FUNZIONE BACKGROUND PDF (CORRETTA)
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
# GENERAZIONE PDF
# --------------------------------------------------
def genera_pdf(esercizi):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Titolo",
        fontSize=18,
        alignment=1,
        spaceAfter=20
    ))

    styles.add(ParagraphStyle(
        name="NomeEsercizio",
        fontSize=12,
        spaceAfter=6,
        leading=14,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Testo",
        fontSize=10,
        leading=14
    ))

    story = []

    # LOGO (proporzioni corrette)
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/a/ab/Logo_TV_2015.png"
    story.append(Image(logo_url, width=4 * cm, height=4 * cm))
    story.append(Spacer(1, 12))

    # TITOLO
    story.append(Paragraph("Programma esercizi personalizzato", styles["Titolo"]))
    story.append(Spacer(1, 12))

    # LINEA SOTTILE
    story.append(Table(
        [[""]],
        colWidths=[16 * cm],
        style=[("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey)]
    ))
    story.append(Spacer(1, 16))

    for _, ex in esercizi.iterrows():
        # QR CODE
        qr = qrcode.make(ex["link_video"])
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer)
        qr_buffer.seek(0)

        qr_img = Image(qr_buffer, width=3 * cm, height=3 * cm)

        testo = [
            Paragraph(ex["nome"], styles["NomeEsercizio"]),
            Paragraph(f"<b>Difficoltà:</b> {ex['difficoltà']}", styles["Testo"]),
            Spacer(1, 4),
            Paragraph(ex["descrizione"], styles["Testo"])
        ]

        card = Table(
            [[qr_img, testo]],
            colWidths=[3.5 * cm, 11.5 * cm],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
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
# UI STREAMLIT
# --------------------------------------------------
st.subheader(f"Esercizi per: {distretto_sel}")

for _, row in esercizi_sel.iterrows():
    st.markdown(f"**{row['nome']}**")
    st.caption(row["descrizione"])
    st.markdown("---")

if st.button("Genera PDF"):
    pdf = genera_pdf(esercizi_sel)
    st.download_button(
        "Scarica PDF",
        pdf,
        file_name="programma_esercizi.pdf",
        mime="application/pdf"
    )
