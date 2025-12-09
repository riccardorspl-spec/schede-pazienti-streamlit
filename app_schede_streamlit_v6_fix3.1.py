# --------------------------
#   GENERAZIONE PDF MODERNO
# --------------------------

class PDF(FPDF):
    def header(self):
        # Sfondo leggero (opzionale ma molto professionale)
        try:
            self.image("background.png", x=0, y=0, w=210, h=297)  # A4
        except:
            pass

        # Logo
        try:
            self.image("logo.png", x=10, y=8, w=25)
        except:
            pass

        # Titolo
        self.set_xy(0, 15)
        self.set_font("ArialUnicode", "", 18)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, f"Riabilitazione • {nome_paziente}", align="C", ln=True)

        self.set_font("ArialUnicode", "", 12)
        self.cell(0, 7, f"Data inizio: {data_inizio}", align="C", ln=True)
        self.ln(8)

    def footer(self):
        self.set_y(-25)
        self.set_font("ArialUnicode", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, "Fisioterapista OMPT: Riccardo Rispoli", align="C")
        self.ln(4)
        self.cell(0, 6, "Studio di Fisioterapia • Grosseto", align="C")


# --------------------------
#   INIZIO DEL PDF
# --------------------------

pdf = PDF()
pdf.add_font("ArialUnicode", "", "Arial-Unicode-Regular.ttf", uni=True)
pdf.add_page()
pdf.set_font("ArialUnicode", "", 12)

# --------------------------
#   CICLO ESERCIZI
# --------------------------

for e in esercizi_selezionati:
    row = df_distretto[df_distretto["nome"] == e].iloc[0]

    # Titolo esercizio
    pdf.set_font("ArialUnicode", "", 15)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, e, ln=True)
    pdf.ln(2)

    start_y = pdf.get_y()

    # Immagine esercizio
    try:
        img_path = f"images/{e}.png"
        pdf.image(img_path, x=10, y=start_y, w=45)
    except:
        pass

    # Descrizione + serie + ripetizioni
    pdf.set_xy(60, start_y)
    pdf.set_font("ArialUnicode", "", 12)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 6, row["descrizione"])

    pdf.ln(2)
    pdf.set_font("ArialUnicode", "", 12)
    pdf.cell(0, 6, f"Serie: {serie_dict[e]}   |   Ripetizioni: {rip_dict[e]}", ln=True)

    # QR Code del video
    if pd.notna(row["link_video"]):
        qr = qrcode.QRCode(box_size=2, border=1)
        qr.add_data(row["link_video"])
        qr.make(fit=True)
        buf = BytesIO()
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        pdf.image(buf, x=160, y=start_y, w=25)

    pdf.ln(20)

# --------------------------
#   SALVATAGGIO PDF
# --------------------------

pdf_file = f"Scheda_{nome_paziente}.pdf"
pdf.output(pdf_file)

st.success(f"PDF generato: {pdf_file}")
with open(pdf_file, "rb") as f:
    st.download_button("Scarica PDF", f, file_name=pdf_file, mime="application/pdf")
