from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from io import BytesIO
from PIL import Image as PILImage


def genera_scheda(nome, obiettivo, note, esercizi, immagine, colore_titolo, colore_accento):

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # ===== Titolo =====
    titolo_style = styles["Title"]
    titolo_style.textColor = HexColor(colore_titolo)
    titolo_style.fontSize = 28
    story.append(Paragraph(f"Scheda Cliente — {nome}", titolo_style))
    story.append(Spacer(1, 12))

    # ===== Obiettivo =====
    story.append(Paragraph(f"<b>🎯 Obiettivo:</b> {obiettivo}", styles["Normal"]))
    story.append(Spacer(1, 8))

    # ===== Note =====
    if note.strip():
        story.append(Paragraph(f"<b>📝 Note:</b> {note}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # ===== Immagine cliente =====
    if immagine:
        img = PILImage.open(immagine)
        img = img.resize((300, int(300 * img.height / img.width)))
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        story.append(Image(img_buffer, width=8*cm, height=8*cm))
        story.append(Spacer(1, 20))

    # ===== Esercizi =====
    header_style = styles["Heading2"]
    header_style.textColor = HexColor(colore_accento)
    header_style.fontSize = 18
    story.append(Paragraph("📋 Programma Allenamento", header_style))
    story.append(Spacer(1, 12))

    for i, ex in enumerate(esercizi):
        blocco = f"""
        <b>{i+1}. {ex['nome']}</b><br/>
        Serie: {ex['serie']} — Ripetizioni: {ex['ripetizioni']} — Tempo: {ex['tempo']}<br/>
        <i>{ex['descrizione']}</i><br/><br/>
        """
        story.append(Paragraph(blocco, styles["Normal"]))
        story.append(Spacer(1, 6))

    # ===== GENERA PDF =====
    pdf.build(story)
    buffer.seek(0)
    return buffer.getvalue()
