import streamlit as st
import pandas as pd
from fpdf import FPDF
import qrcode
import tempfile
from io import BytesIO
import os

st.set_page_config(page_title="Schede Pazienti - IlFisioColMalDiSchiena", layout="wide")

# ---------------------------------------------------------
# CARICAMENTO DATI
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("esercizi.csv")
    return df

df = load_data()

# ---------------------------------------------------------
# INTESTAZIONE
# ---------------------------------------------------------
st.title("📄 Generatore Schede Pazienti")
st.caption("Creato da **Riccardo Rispoli OMPT – IlFisioColMalDiSchiena**")

# ---------------------------------------------------------
# INPUT DATI PAZIENTE
# ---------------------------------------------------------
st.header("👤 Dati Paziente")

col1, col2 = st.columns(2)
with col1:
    nome_paziente = st.text_input("Nome e cognome del paziente")
with col2:
    data_inizio = st.date_input("Data inizio trattamento")

distretto = st.selectbox("Seleziona il distretto", sorted(df["distretto"].unique()))

df_distretto = df[df["distretto"] == distretto]

# ---------------------------------------------------------
# SELEZIONE ESERCIZI
# ---------------------------------------------------------
st.header("🏋️‍♂️ Seleziona gli esercizi")

esercizi = st.multiselect("Esercizi disponibili", df_distretto["nome"].tolist())

serie_dict = {}
rip_dict = {}

if esercizi:
    st.subheader("Imposta Serie e Ripetizioni")
    for e in esercizi:
        c1, c2 = st.columns(2)
        with c1:
            serie_dict[e] = st.number_input(f"Serie per {e}", min_value=1, max_value=10, value=3)
        with c2:
            rip_dict[e] = st.number_input(f"Ripetizioni per {e}", min_value=1, max_value=50, value=10)

# ---------------------------------------------------------
# CLASSE PDF
# ---------------------------------------------------------
class PDF(FPDF):
    def header(self):
        # Logo (opzionale)
        try:
            self.image("logo.png", x=10, y=8, w=25)
        except:
            pass

        self.set_xy(0, 10)
        self.set_font("ArialUnicode", "", 14)
        self.cell(0, 10, f"Scheda paziente: {nome_paziente}", ln=True, align="C")
        self.cell(0, 5, f"Data inizio: {data_inizio}", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font("ArialUnicode", "", 10)
        self.cell(0, 10, "Fisioterapista OMPT: Riccardo Rispoli", align="C")

# ---------------------------------------------------------
# GENERA PDF
# ---------------------------------------------------------
if st.button("Genera PDF"):
    if not nome_paziente:
        st.error("Inserisci il nome del paziente")
        st.stop()

    if not esercizi:
        st.error("Seleziona almeno un esercizio")
        st.stop()

    pdf = PDF()
    pdf.add_font("ArialUnicode", "", "Arial-Unicode-Regular.ttf", uni=True)
    pdf.add_page()
    pdf.set_font("ArialUnicode", "", 12)

    # Background
    try:
        pdf.image("background.png", x=0, y=0, w=210, h=297)
    except:
        pass

    for e in esercizi:
        row = df_distretto[df_distretto["nome"] == e].iloc[0]

        pdf.set_font("ArialUnicode", "", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, e, ln=True)

        # IMMAGE ESERCIZIO
        try:
            img_path = f"images/{e}.png"
            pdf.image(img_path, x=10, y=pdf.get_y(), w=40)
        except:
            pass

        # DESCRIZIONE
        pdf.set_xy(55, pdf.get_y())
        pdf.set_font("ArialUnicode", "", 12)
        pdf.multi_cell(0, 6, row["descrizione"])

        # SERIE / RIPETIZIONI
        pdf.set_font("ArialUnicode", "", 12)
        pdf.cell(0, 6, f"Serie: {serie_dict[e]}   Ripetizioni: {rip_dict[e]}", ln=True)

        # QR CODE video
        if pd.notna(row["link_video"]):
            qr = qrcode.QRCode(box_size=2, border=1)
            qr.add_data(row["link_video"])
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                qr_img.save(tmpfile.name)
                tmpfile_path = tmpfile.name

            pdf.image(tmpfile_path, x=160, y=pdf.get_y()-10, w=25)

        pdf.ln(20)

    filename = f"Scheda_{nome_paziente.replace(' ', '_')}.pdf"
    pdf.output(filename)

    with open(filename, "rb") as f:
        st.download_button("📥 Scarica PDF", f, file_name=filename, mime="application/pdf")

    st.success("PDF generato con successo!")
