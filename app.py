import streamlit as st
from app_schede_streamlit import genera_scheda

st.set_page_config(page_title="IlFisioColMalDiSchiena — Schede", page_icon="💪", layout="wide")

# ====== NAVBAR ======
st.markdown("""
    <style>
        .navbar {
            background-color: #0d6efd;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .navbar h1 {
            color: white;
            font-size: 28px;
            margin: 0;
            text-align: center;
        }
    </style>
    <div class="navbar">
        <h1>IlFisioColMalDiSchiena — Generatore Schede</h1>
    </div>
""", unsafe_allow_html=True)

# ====== SIDEBAR ======
with st.sidebar:
    st.header("⚙️ Impostazioni")
    nome_paziente = st.text_input("Nome cliente/paziente")
    obiettivo = st.text_input("Obiettivo")
    note = st.text_area("Note aggiuntive")
    
    st.markdown("---")
    st.subheader("📸 Carica immagine cliente (opzionale)")
    uploaded_img = st.file_uploader("Carica immagine", type=["jpg", "jpeg", "png"])

    st.markdown("---")
    st.subheader("🟦 Colori brand IlFisioColMalDiSchiena")
    colore_titolo = "#0d6efd"   # blu
    colore_accento = "#ff6f00"  # arancione


st.markdown("## ✍️ Crea la Scheda del Cliente")

# ========= INPUT ESERCIZI =========
st.markdown("#### 📋 Inserisci esercizi")

numero_esercizi = st.number_input("Quanti esercizi vuoi inserire?", min_value=1, max_value=20, value=5)

esercizi = []
for i in range(numero_esercizi):
    with st.expander(f"Esercizio {i+1}"):
        nome = st.text_input(f"Nome esercizio {i+1}")
        serie = st.text_input(f"Serie {i+1}")
        ripetizioni = st.text_input(f"Ripetizioni {i+1}")
        tempo = st.text_input(f"Tempo / ritmo {i+1}")
        descrizione = st.text_area(f"Descrizione tecnica {i+1}")
        esercizi.append({
            "nome": nome,
            "serie": serie,
            "ripetizioni": ripetizioni,
            "tempo": tempo,
            "descrizione": descrizione
        })

# ========= GENERA SCHEDA =========
if st.button("🚀 GENERA SCHEDA"):
    if nome_paziente.strip() == "":
        st.error("Inserisci il nome del paziente.")
    else:
        pdf_bytes = genera_scheda(
            nome_paziente,
            obiettivo,
            note,
            esercizi,
            uploaded_img,
            colore_titolo,
            colore_accento
        )

        st.success("Scheda generata con successo! 🎉")

        st.download_button(
            label="⬇️ Scarica Scheda in PDF",
            data=pdf_bytes,
            file_name=f"Scheda_{nome_paziente.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
