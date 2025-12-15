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
from reportlab.platypus import KeepTogether, PageBreak
from reportlab.platypus import Spacer





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


def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(
        A4[0] / 2,
        1.2 * cm,
        "Riccardo Rispoli – Fisioterapista OMPT"
    )
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
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="HeaderTitle",
        fontSize=18,
        leading=22
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

    # ---------------- HEADER ----------------
    logo = Spacer(4 * cm, 1 * cm)
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=3.5 * cm, height=3.5 * cm, kind="proportional")

    title = Paragraph("<b>Programma esercizi personalizzato</b>", styles["HeaderTitle"])

    header = Table(
        [[logo, title]],
        colWidths=[4 * cm, 12 * cm],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    story.append(header)

    story.append(Table(
        [[""]],
        colWidths=[16 * cm],
        style=[("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey)]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Paziente:</b> {nome_paziente}", styles["Testo"]))
    story.append(Paragraph(f"<b>Motivo:</b> {motivo}", styles["Testo"]))
    story.append(Spacer(1, 16))

    # ---------------- ESERCIZI ----------------
    for ex in scheda:
        # immagine esercizio
        img_path = f"images/{ex['nome']}.png"
        if os.path.exists(img_path):
            esercizio_img = Image(img_path, width=3.5 * cm, kind="proportional")
        else:
            esercizio_img = Spacer(3.5 * cm, 3 * cm, kind="proportional")
        # QR
        qr = qrcode.make(ex["link_video"])
        qr_buf = io.BytesIO()
        qr.save(qr_buf)
        qr_buf.seek(0)
        qr_img = Image(qr_buf, width=2.5 * cm)

        testo = Paragraph(
            f"""
            <b>{ex['nome']}</b><br/>
            {ex['descrizione']}<br/><br/>
            <b>Serie:</b> {ex['serie']} &nbsp;&nbsp;
            <b>Ripetizioni:</b> {ex['ripetizioni']}
            """,
            styles["Testo"]
        )

        card = Table(
            [[esercizio_img, testo, qr_img]],
            colWidths=[4 * cm, 9 * cm, 3 * cm],
            style=[
                ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )

        story.append(
    KeepTogether([
        card,
        Spacer(1, 14)
    ])
)
story.append(Spacer(1, 0.2 * cm))
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
    st.download_button(
        "Scarica PDF",
        pdf,
        file_name="programma_esercizi_personalizzato.pdf",
        mime="application/pdf"
    )

