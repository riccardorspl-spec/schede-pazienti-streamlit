import streamlit as st
import pandas as pd
import os
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

import qrcode

# --------------------------
# CONFIG
# --------------------------
LOGO_PATH = "logo.png"
BACKGROUND_PATH = "background.png"
IMAGES_DIR = "images"

st.set_page_config(
    page_title="Generatore schede",
    page_icon="🧾",
    layout="centered"
)

st.title("🧾 Generatore schede esercizi")

# --------------------------
# LOAD CSV
# --------------------------
df = pd.read_csv("esercizi.csv")
df["distretto"] = df["distretto"].astype(str)

# --------------------------
# INPUT UI
# --------------------------
nome_paziente = st.text_input("Nome e cognome paziente")
problematica = st.text_area("Problematica")

distretto = st.selectbox(
    "Seleziona distretto",
    sorted(df["distretto"].dropna().unique())
)

df_distretto = df[df["distretto"] == distretto]

esercizi = st.multiselect(
    "Seleziona esercizi",
    df_distretto["nome"].tolist()
)

serie = {}
ripetizioni = {}

for e in esercizi:
    col1, col2 = st.columns(2)
    with col1:
        serie[e] = st.text_input(f"Serie – {e}", "3")
    with col2:
        ripetizioni[e] = st.text_input(f"Ripetizioni – {e}", "10")

# --------------------------
# PDF FUNCTIONS
# --------------------------
def background(canvas, doc):
    if os.path.exists(BACKGROUND_PATH):
        canvas.drawImage(
            BACKGROUND_PATH,
            0,
            0,
            width=A4[0],
            height=A4[1],
            preserveAspectRatio=True,
            mask='auto'
        )

def genera_pdf():
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=3.5*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Titolo",
        fontSize=18,
        alignment=1,
        spaceAfter=20
    ))

    elements = []

    # HEADER
    header_table = []

    if os.path.exists(LOGO_PATH):
        header_table.append([
            Image(LOGO_PATH, width=4*cm, height=2*cm),
            Paragraph("<b>Generatore schede esercizi</b>", styles["Titolo"])
        ])
    else:
        header_table.append([
            "",
            Paragraph("<b>Generatore schede esercizi</b>", styles["Titolo"])
        ])

    header = Table(header_table, colWidths=[5*cm, 11*cm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
    ]))

    elements.append(header)

    # PAZIENTE
    elements.append(Paragraph(f"<b>Paziente:</b> {nome_paziente}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Problematica:</b> {problematica}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # ESERCIZI
    for e in esercizi:
        row = df_distretto[df_distretto["nome"] == e].iloc[0]

        img_path = os.path.join(IMAGES_DIR, f"{e}.png")

        # QR
        qr = qrcode.make(row["link_video"])
        qr_buf = BytesIO()
        qr.save(qr_buf)
        qr_buf.seek(0)

        img_ex = Image(img_path, width=4*cm, height=4*cm) if os.path.exists(img_path) else ""
        img_qr = Image(qr_buf, width=3*cm, height=3*cm)

        data = [
            [
                img_ex,
                Paragraph(
                    f"<b>{e}</b><br/>"
                    f"{row['descrizione']}<br/><br/>"
                    f"<b>Serie:</b> {serie[e]} &nbsp;&nbsp; "
                    f"<b>Rip:</b> {ripetizioni[e]}",
                    styles["Normal"]
                ),
                img_qr
            ]
        ]

        table = Table(data, colWidths=[5*cm, 8*cm, 3*cm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

    doc.build(
        elements,
        onFirstPage=background,
        onLaterPages=background
    )

    buffer.seek(0)
    return buffer

# --------------------------
# GENERATE
# --------------------------
if st.button("📄 Genera PDF"):
    pdf = genera_pdf()
    st.download_button(
        "⬇️ Scarica PDF",
        pdf,
        file_name=f"Scheda_{nome_paziente}.pdf",
        mime="application/pdf"
    )
