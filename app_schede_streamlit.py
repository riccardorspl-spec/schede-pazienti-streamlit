import streamlit as st
import pandas as pd
from fpdf import FPDF
import qrcode
from io import BytesIO
import os

# --------------------------
# Configurazioni Streamlit
# --------------------------
st.set_page_config(page_title="Schede Pazienti", layout="wide")
st.title("Generatore Schede Pazienti")

# --------------------------
# Input informazioni paziente
# --------------------------
nome_paziente = st.text_input("Nome e Cognome Paziente")
problematiche = st.text_area("Problematiche")
data_inizio = st.date_input("Data inizio")

# --------------------------
# Carica file Excel
# --------------------------
excel_path = "esercizi.xlsx"
if not os.path.exists(excel_path):
    st.error(f"File {excel_path} non trovato nella cartella!")
    st.stop()

df = pd.read_excel(excel_path)

# Controllo colonne minime
required_cols = ["distretto", "nome", "serie", "ripetizioni", "descrizione", "link_video"]
if not all(col in df.columns for col in required_cols):
    st.error(f"Le colonne del file Excel devono essere: {', '.join(required_cols)}")
    st.stop()

# --------------------------
# Selezione distretto ed esercizi
# --------------------------
distretto = st.selectbox("Seleziona distretto:", df["distretto"].unique())
df_distretto = df[df["distretto"] == distretto]

esercizi_selezionati = st.multiselect(
    "Seleziona esercizi",
    options=df_distretto["nome"].tolist()
)

# Serie e ripetizioni per ogni esercizio selezionato
serie_dict = {}
rip_dict = {}
for e in esercizi_selezionati:
    col1, col2 = st.columns(2)
    with col1:
        serie_dict[e] = st.number_input(f"Serie {e}", min_value=1, max_value=10, value=3, step=1)
    with col2:
        rip_dict[e] = st.number_input(f"Ripetizioni {e}", min_value=1, max_value=30, value=10, step=1)

# --------------------------
# Generazione PDF con sfondo
# --------------------------
class PDF(FPDF):
    def header(self):
        # Logo a sinistra
        logo_path = "logo.png"
        try:
            self.image(logo_path, x=10, y=8, w=25)
        except:
            pass
        # Titolo centrato
        self.set_xy(0, 10)
        self.set_font("ArialUnicode", "", 14)
        self.cell(0, 10, f"Scheda paziente: {nome_paziente}", ln=True, align="C")
        self.cell(0, 5, f"Data inizio: {data_inizio}", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font("ArialUnicode", "", 10)
        self.cell(0, 10, "Fisioterapista OMPT: Riccardo Rispoli", align="C")

# Bottone per generare PDF
if st.button("Genera scheda PDF") and nome_paziente and esercizi_selezionati:
    pdf = PDF()
    pdf.add_font("ArialUnicode", "", "Arial-Unicode-Regular.ttf", uni=True)
    pdf.set_font("ArialUnicode", "", 12)
    pdf.add_page()

    # Sfondo opzionale
    background_path = "background.png"
    if os.path.exists(background_path):
        pdf.image(background_path, x=0, y=0, w=210, h=297)  # A4

    for e in esercizi_selezionati:
        row = df_distretto[df_distretto["nome"] == e].iloc[0]
        pdf.set_font("ArialUnicode", "", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, e, ln=True)

        # Immagine esercizio se esiste
        try:
            img_path = f"images/{e}.png"
            if os.path.exists(img_path):
                pdf.image(img_path, x=10, y=pdf.get_y(), w=40)
        except:
            pass

        # Descrizione
        pdf.set_xy(55, pdf.get_y())
        pdf.set_font("ArialUnicode", "", 12)
        pdf.multi_cell(0, 6, row["descrizione"])

        # Serie/Ripetizioni
        pdf.set_font("ArialUnicode", "", 12)
        pdf.cell(0, 6, f"Serie: {serie_dict[e]}   Ripetizioni: {rip_dict[e]}", ln=True)

        # QR code del video
        if pd.notna(row["link_video"]):
            qr = qrcode.QRCode(box_size=2, border=1)
            qr.add_data(row["link_video"])
            qr.make(fit=True)
            buf = BytesIO()
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save(buf, format="PNG")
            buf.seek(0)
            pdf.image(buf, x=160, y=pdf.get_y()-10, w=25)

        pdf.ln(20)

    pdf_file = f"Scheda_{nome_paziente}.pdf"
    pdf.output(pdf_file)

    st.success(f"PDF generato: {pdf_file}")
    with open(pdf_file, "rb") as f:
        st.download_button("Scarica PDF", f, file_name=pdf_file, mime="application/pdf")
