import streamlit as st
import pandas as pd
from fpdf import FPDF
import qrcode
from io import BytesIO
from PIL import Image

# --------------------------
# Configurazioni Streamlit
# --------------------------
st.set_page_config(page_title="Generatore Schede Pazienti", layout="wide")

st.title("Schede Pazienti")

# Carica Excel con esercizi
df = pd.read_excel("esercizi.xlsx")  # Assicurati che il file sia nella stessa cartella

# Seleziona paziente e data
nome_paziente = st.text_input("Nome paziente:")
data_inizio = st.date_input("Data inizio:")

# Seleziona distretto
distretto = st.selectbox("Seleziona distretto:", df["distretto"].unique())

# Filtra esercizi per distretto
df_distretto = df[df["distretto"] == distretto]

# Seleziona più esercizi
esercizi_selezionati = st.multiselect(
    "Seleziona esercizi",
    options=df_distretto["nome"].tolist()
)

# Serie e ripetizioni dinamiche
serie_dict = {}
rip_dict = {}
for e in esercizi_selezionati:
    serie_dict[e] = st.number_input(f"Serie per {e}", min_value=1, value=3)
    rip_dict[e] = st.number_input(f"Ripetizioni per {e}", min_value=1, value=10)

# --------------------------
# Generazione PDF
# --------------------------
class PDF(FPDF):
    def header(self):
        # Logo a sinistra
        logo_path = "logo.png"  # metti il tuo logo nella stessa cartella
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

# Inizializza PDF
pdf = PDF()
pdf.add_page()
pdf.add_font("ArialUnicode", "", "Arial-Unicode-Regular.ttf", uni=True)
pdf.set_font("ArialUnicode", "", 12)

# Aggiungi ogni esercizio
for e in esercizi_selezionati:
    row = df_distretto[df_distretto["nome"] == e].iloc[0]
    pdf.set_font("ArialUnicode", "", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, e, ln=True)
    
    # Immagine esercizio se esiste
    try:
        img_path = f"images/{e}.png"  # cartella images con i nomi degli esercizi
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

# Salva PDF
pdf_file = f"Scheda_{nome_paziente}.pdf"
pdf.output(pdf_file)

st.success(f"PDF generato: {pdf_file}")
with open(pdf_file, "rb") as f:
    st.download_button("Scarica PDF", f, file_name=pdf_file, mime="application/pdf")
