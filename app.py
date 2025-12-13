import streamlit as st
import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
import os

# --------------------------
# Streamlit UI
# --------------------------
st.set_page_config(page_title="Generatore schede", layout="centered")

st.title("Generatore schede esercizi")

df = pd.read_csv("esercizi.csv")
df = df.fillna("")

col1, col2 = st.columns(2)
with col1:
    nome_paziente = st.text_input("Nome e cognome paziente")
with col2:
    problematica = st.text_input("Problematica")

distretto = st.selectbox(
    "Seleziona il distretto",
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
    c1, c2 = st.columns(2)
    with c1:
        serie[e] = st.number_input(f"Serie – {e}", 1, 10, 3)
    with c2:
        ripetizioni[e] = st.number_input(f"Ripetizioni – {e}", 1, 30, 10)

# --------------------------
# PDF Background
# --------------------------
class BackgroundCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        self.bg_image = "background.png"
        super().__init__(*args, **kwargs)

    def drawPageBackground(self):
        if os.path.exists(self.bg_image):
            self.drawImage(
                self.bg_image,
                0,
                0,
                width=A4[0],
                height=A4[1]
            )

    def showPage(self):
        self.drawPageBackground()
        super().showPage()

    def save(self):
        self.drawPageBackground()
        super().save()

# --------------------------
# Generazione PDF
# --------------------------
if st.button("Genera PDF") and esercizi:

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Titolo",
        fontSize=18,
        alignment=1,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name="Testo",
        fontSize=11,
        spaceAfter=6
    ))

    story = []

    # --------------------------
    # Header con logo + titolo
    # --------------------------
    logo = Image("logo.png", width=3.5*cm, height=3.5*cm)
    titolo = Paragraph(
        "<b>Programma esercizi personalizzato</b>",
        styles["Titolo"]
    )

    header = Table(
        [[logo, titolo]],
        colWidths=[4*cm, 12*cm]
    )

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(header)

    # Linea sotto header
    linea_header = Table([[""]], colWidths=[18*cm])
    linea_header.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.75, colors.grey)
    ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(linea_header)
    story.append(Spacer(1, 0.8*cm))

    story.append(Paragraph(
        f"<b>Paziente:</b> {nome_paziente}<br/>"
        f"<b>Problematica:</b> {problematica}",
        styles["Testo"]
    ))

    story.append(Spacer(1, 0.8*cm))

    # --------------------------
    # Esercizi (CARD)
    # --------------------------
    for e in esercizi:
        row = df_distretto[df_distretto["nome"] == e].iloc[0]

        # Immagine esercizio
        img_path = f"images/{e}.png"
        if os.path.exists(img_path):
            img = Image(img_path, width=4*cm, height=4*cm)
        else:
            img = Spacer(4*cm, 4*cm)

        # QR Code
        qr = qrcode.make(row["link_video"])
        qr_buf = BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        qr_img = Image(qr_buf, width=3*cm, height=3*cm)

        testo = Paragraph(
            f"<b>{e}</b><br/>"
            f"{row['descrizione']}<br/>"
            f"<b>Serie:</b> {serie[e]} &nbsp;&nbsp;"
            f"<b>Ripetizioni:</b> {ripetizioni[e]}",
            styles["Testo"]
        )

        card = Table(
            [[img, testo, qr_img]],
            colWidths=[4.5*cm, 8.5*cm, 3*cm]
        )

        card.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERPADDING", (0, 0), (-1, -1), 6),
        ]))

        story.append(card)

        # Linea tra esercizi
        linea_es = Table([[""]], colWidths=[18*cm])
        linea_es.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ]))

        story.append(Spacer(1, 0.4*cm))
        story.append(linea_es)
        story.append(Spacer(1, 0.6*cm))

    doc.build(story, canvasmaker=BackgroundCanvas)

    buffer.seek(0)
    st.download_button(
        "Scarica PDF",
        buffer,
        file_name=f"Programma_{nome_paziente}.pdf",
        mime="application/pdf"
    )
