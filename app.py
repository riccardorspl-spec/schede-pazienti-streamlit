import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

import qrcode
from PIL import Image as PILImage
from streamlit_drawable_canvas import st_canvas


# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Generatore schede",
    page_icon="📝",
    layout="centered"
)

st.title("📝 Generatore schede")
st.markdown("---")


# -------------------------------------------------
# CSV ESERCIZI (UPLOAD O DEFAULT)
# -------------------------------------------------
uploaded_csv = st.file_uploader(
    "Carica esercizi.csv (opzionale)",
    type=["csv"]
)

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
else:
    df = pd.read_csv("esercizi.csv")

df = df.fillna("")


# -------------------------------------------------
# INPUT PAZIENTE
# -------------------------------------------------
with st.container():
    st.subheader("👤 Dati paziente")
    nome_paziente = st.text_input("Nome e cognome")
    problematica = st.text_area("Problematica / diagnosi")

st.markdown("---")


# -------------------------------------------------
# SELEZIONE ESERCIZI
# -------------------------------------------------
distretto = st.selectbox(
    "Distretto",
    sorted(df["distretto"].unique())
)

df_d = df[df["distretto"] == distretto]

esercizi = st.multiselect(
    "Esercizi",
    df_d["nome"].tolist()
)

serie, rip = {}, {}

for e in esercizi:
    col1, col2 = st.columns(2)
    with col1:
        serie[e] = st.text_input(f"Serie – {e}")
    with col2:
        rip[e] = st.text_input(f"Ripetizioni – {e}")

st.markdown("---")


# -------------------------------------------------
# FIRMA DIGITALE
# -------------------------------------------------
st.subheader("✍️ Firma del terapista")

canvas = st_canvas(
    stroke_width=2,
    stroke_color="#000000",
    background_color="#FFFFFF",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="firma"
)

firma_img = None
if canvas.image_data is not None:
    firma_img = PILImage.fromarray(canvas.image_data.astype("uint8"))


# -------------------------------------------------
# FUNZIONE PDF
# -------------------------------------------------
def genera_pdf():
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=3*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        f"<b>Scheda riabilitativa</b><br/>"
        f"Paziente: {nome_paziente}<br/>"
        f"Problematica: {problematica}",
        styles["Title"]
    ))
    elements.append(Spacer(1, 20))

    for e in esercizi:
        row = df_d[df_d["nome"] == e].iloc[0]

        elements.append(Paragraph(f"<b>{e}</b>", styles["Heading2"]))
        elements.append(Paragraph(row["descrizione"], styles["Normal"]))
        elements.append(Paragraph(
            f"Serie: {serie[e]} &nbsp;&nbsp; Ripetizioni: {rip[e]}",
            styles["Italic"]
        ))
        elements.append(Spacer(1, 10))

        img_path = f"images/{e}.png"
        if os.path.exists(img_path):
            elements.append(Image(img_path, width=6*cm, height=6*cm))

        if row["link_video"]:
            qr = qrcode.make(row["link_video"])
            qr_buf = BytesIO()
            qr.save(qr_buf)
            qr_buf.seek(0)
            elements.append(Spacer(1, 5))
            elements.append(Image(qr_buf, width=3*cm, height=3*cm))

        elements.append(Spacer(1, 20))

    if firma_img:
        firma_buf = BytesIO()
        firma_img.save(firma_buf, format="PNG")
        firma_buf.seek(0)
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Firma terapista", styles["Normal"]))
        elements.append(Image(firma_buf, width=5*cm, height=2*cm))

    def background(canvas, doc):
        if os.path.exists("background.png"):
            canvas.drawImage(
                "background.png",
                0, 0,
                width=A4[0],
                height=A4[1]
            )
        if os.path.exists("logo.png"):
            canvas.drawImage(
                "logo.png",
                2*cm,
                A4[1] - 3*cm,
                width=3*cm,
                mask="auto"
            )

    doc.build(elements, onFirstPage=background, onLaterPages=background)
    buffer.seek(0)
    return buffer


# -------------------------------------------------
# SALVATAGGIO STORICO
# -------------------------------------------------
def salva_storico():
    record = {
        "data": datetime.now().strftime("%Y-%m-%d"),
        "paziente": nome_paziente,
        "distretto": distretto,
        "esercizi": ", ".join(esercizi)
    }

    file = "storico_pazienti.csv"
    df_new = pd.DataFrame([record])

    if os.path.exists(file):
        df_old = pd.read_csv(file)
        df_new = pd.concat([df_old, df_new])

    df_new.to_csv(file, index=False)


# -------------------------------------------------
# GENERA
# -------------------------------------------------
if st.button("📄 Genera PDF"):
    if not nome_paziente or not esercizi:
        st.error("Inserisci nome e almeno un esercizio")
    else:
        pdf = genera_pdf()
        salva_storico()

        st.success("Scheda generata")
        st.download_button(
            "⬇️ Scarica PDF",
            data=pdf,
            file_name=f"Scheda_{nome_paziente}.pdf",
            mime="application/pdf"
        )


# -------------------------------------------------
# STORICO
# -------------------------------------------------
if os.path.exists("storico_pazienti.csv"):
    with st.expander("📚 Storico pazienti"):
        st.dataframe(pd.read_csv("storico_pazienti.csv"))


