import streamlit as st
import pandas as pd
import qrcode
import io
import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import black

# ---------------- CONFIG ----------------

st.set_page_config(page_title="Generatore Schede", layout="wide")
st.title("🧾 Generatore Schede Esercizi")

LOGO_URL = "https://TUO_LOGO_URL.png"   # ← metti il tuo
BACKGROUND_PATH = "background.png"
IMAGES_DIR = "images"

CSV_REQUIRED_COLUMNS = [
    "distretto", "nome", "difficoltà", "descrizione", "link_video"
]

# ---------------- CSV VALIDATION ----------------

@st.cache_data
def load_and_validate_csv():
    df = pd.read_csv("esercizi.csv")

    missing_cols = [c for c in CSV_REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        st.error(f"❌ Colonne mancanti nel CSV: {missing_cols}")
        st.stop()

    df = df.dropna(subset=["distretto", "nome"])
    df = df.fillna("")

    return df

df = load_and_validate_csv()

# ---------------- FORM UI ----------------

with st.form("scheda_form"):
    col1, col2 = st.columns(2)

    with col1:
        paziente = st.text_input("Nome e Cognome Paziente")
        problematica = st.text_area("Problematica")

    with col2:
        distretto = st.selectbox(
            "Distretto",
            sorted(df["distretto"].unique())
        )

    df_distretto = df[df["distretto"] == distretto]

    esercizi_scelti = st.multiselect(
        "Seleziona esercizi",
        df_distretto["nome"].tolist()
    )

    esercizi_finali = []

    for nome in esercizi_scelti:
        st.markdown(f"**{nome}**")
        c1, c2 = st.columns(2)
        serie = c1.text_input("Serie", key=f"serie_{nome}")
        rip = c2.text_input("Ripetizioni", key=f"rip_{nome}")

        riga = df_distretto[df_distretto["nome"] == nome].iloc[0]
        esercizi_finali.append({
            "nome": nome,
            "serie": serie,
            "ripetizioni": rip,
            "descrizione": riga["descrizione"],
            "link_video": riga["link_video"]
        })

    genera = st.form_submit_button("📄 Genera PDF")

# ---------------- PDF GENERATION ----------------

def genera_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    # Logo
    elements.append(Image(LOGO_URL, width=4*cm, height=2*cm))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Paziente:</b> {paziente}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Problematica:</b> {problematica}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    for ex in esercizi_finali:
        row = []

        # --- Immagine esercizio ---
        img_path = os.path.join(IMAGES_DIR, f"{ex['nome']}.png")
        if os.path.exists(img_path):
            img = Image(img_path, width=4*cm, height=4*cm)
        else:
            img = Spacer(4*cm, 4*cm)

        # --- Descrizione ---
        testo = f"""
        <b>{ex['nome']}</b><br/>
        Serie: {ex['serie']}<br/>
        Ripetizioni: {ex['ripetizioni']}<br/><br/>
        {ex['descrizione']}
        """
        desc = Paragraph(testo, styles["Normal"])

        # --- QR CODE ---
        qr = qrcode.make(ex["link_video"])
        qr_buf = io.BytesIO()
        qr.save(qr_buf)
        qr_buf.seek(0)
        qr_img = Image(qr_buf, width=3*cm, height=3*cm)

        table = Table(
            [[img, desc, qr_img]],
            colWidths=[5*cm, 8*cm, 3*cm]
        )

        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
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

def background(canvas, doc):
    if os.path.exists(BACKGROUND_PATH):
        canvas.drawImage(
            BACKGROUND_PATH, 0, 0,
            width=A4[0], height=A4[1]
        )

# ---------------- DOWNLOAD ----------------

if genera and paziente:
    pdf = genera_pdf()
    st.success("Scheda generata!")
    st.download_button(
        "⬇️ Scarica PDF",
        pdf,
        file_name=f"{paziente}_scheda.pdf",
        mime="application/pdf"
    )


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



