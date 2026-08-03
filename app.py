import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
import io

st.set_page_config(page_title="Gestione Tirocini", page_icon="🏥")

st.title("🏥 Assegnazione Automatica Sedi Tirocinio")
st.markdown("Questo strumento distribuisce equamente le persone nelle sedi ospedaliere calcolando le distanze, le preferenze e i vincoli di auto.")

# File Uploader
uploaded_file = st.file_uploader("Carica il file Excel delle risposte (Es. scaricato da Google Forms)", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success(f"File caricato con successo! Trovati {len(df)} partecipanti.")
    
    st.write("Anteprima dati caricati:")
    st.dataframe(df.head())
    
    # Bottone di calcolo
    if st.button("Calcola Assegnazioni Ottimali"):
        with st.spinner("Calcolo delle combinazioni migliori per minimizzare i km..."):
            
            # --- QUI DENTRO CI SARA' L'ALGORITMO VERO E PROPRIO ---
            # Per questa demo, facciamo finta che l'algoritmo processi il file
            # e restituisca le assegnazioni. (Aggiungerai le tue regole specifiche).
            df["Esito"] = "Calcolato dall'algoritmo"
            df["Sede Assegnata"] = "Ospedale Assegnato" 
            
            st.success("Calcolo completato con successo!")
            st.write("### Risultato Assegnazioni")
            st.dataframe(df)
            
            # Creazione file Excel da scaricare
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Assegnazioni')
            
            # Bottone di Download
            st.download_button(
                label="📥 Scarica Excel con le Assegnazioni",
                data=output.getvalue(),
                file_name="Assegnazioni_Calcolate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
