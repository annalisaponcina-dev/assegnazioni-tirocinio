import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
import io

st.set_page_config(page_title="Gestione Tirocini", page_icon="🏥", layout="wide")

st.title("🏥 Assegnazione Automatica Sedi Tirocinio")
st.markdown("Algoritmo intelligente: ottimizza in base a distanze (max 50km), mezzi pubblici, comodità stazioni e intelligenza geografica veneta.")

uploaded_file = st.file_uploader("Carica il file Excel scaricato da Google Forms", type=["xlsx"])

# 1. CAPIENZE SEDI (Totale 31)
capacities = {
    "CASTELFRANCO": 4, "MONTEBELLUNA": 3, "SAN DONA' DI PIAVE": 2,
    "NOALE": 4, "TREVISO": 10, "CITTADELLA": 3, "VICENZA": 2,
    "VENEZIA": 1, "MESTRE": 1, "CHIOGGIA": 1
}

# 2. COMODITÀ STAZIONI (0 = Eccellente, 5 = Scomodissimo/Inesistente)
comodita_stazione = {
    "CITTADELLA": 0, "CASTELFRANCO": 0, "SAN DONA' DI PIAVE": 1, 
    "VENEZIA": 1, "TREVISO": 2, "MESTRE": 2, "MONTEBELLUNA": 2,
    "VICENZA": 2, "NOALE": 3, "CHIOGGIA": 5
}

# 3. DISTANZE APPROSSIMATIVE (in km) - Mappa Semplificata
distanze_mappa = {
    "Padova Centro": {"TREVISO": 50, "MONTEBELLUNA": 55, "CITTADELLA": 35, "NOALE": 35, "CASTELFRANCO": 45, "VENEZIA": 45, "MESTRE": 40, "SAN DONA' DI PIAVE": 65, "VICENZA": 40, "CHIOGGIA": 45},
    "Provincia Sud/Ovest": {"TREVISO": 65, "MONTEBELLUNA": 75, "CITTADELLA": 45, "NOALE": 45, "CASTELFRANCO": 55, "VENEZIA": 55, "MESTRE": 50, "SAN DONA' DI PIAVE": 80, "VICENZA": 40, "CHIOGGIA": 50},
    "Provincia Nord/Est": {"TREVISO": 40, "MONTEBELLUNA": 45, "CITTADELLA": 35, "NOALE": 25, "CASTELFRANCO": 35, "VENEZIA": 35, "MESTRE": 30, "SAN DONA' DI PIAVE": 55, "VICENZA": 50, "CHIOGGIA": 50},
}

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success(f"File caricato! Trovate {len(df)} risposte.")
    
    if st.button("Calcola Assegnazioni Ottimali"):
        with st.spinner("Incrocio di distanze, costi e intelligenza geografica in corso..."):
            
            spots = []
            for loc, cap in capacities.items():
                spots.extend([loc] * cap)
                
            n_people = len(df)
            cost_matrix = np.zeros((n_people, len(spots)))
            
            for i in range(n_people):
                # Estrazione dati dalle colonne del file Excel (adattale se i titoli cambiano)
                nome = str(df.iloc[i, 0])
                prov_utente = str(df.iloc[i, 1])
                mezzo_utente = str(df.iloc[i, 2])
                scelta_1 = str(df.iloc[i, 4])
                scelta_2 = str(df.iloc[i, 5])
                
                # Categoria di provenienza
                cat_prov = "Padova Centro" if "Centro" in prov_utente else ("Provincia Sud/Ovest" if "Torreglia" in prov_utente or "Albignasego" in prov_utente or "Monselice" in prov_utente else "Provincia Nord/Est")
                
                for j, spot in enumerate(spots):
                    dist = distanze_mappa.get(cat_prov, distanze_mappa["Padova Centro"]).get(spot, 35)
                    
                    # Costo base chilometrico
                    costo_algoritmo = (dist * 2 * 0.15) * 10
                    
                    # Penalità Stazione se usa Mezzi Pubblici
                    if "Treno" in mezzo_utente or "Autobus" in mezzo_utente:
                        costo_algoritmo += (comodita_stazione.get(spot, 0) * 50)
                    
                    # INTELLIGENZA GEOGRAFICA VENETA
                    if cat_prov == "Padova Centro" and "Treno" in mezzo_utente:
                        if spot in ["TREVISO", "VENEZIA", "MONTEBELLUNA"]:
                            costo_algoritmo -= 200 # Sconto enorme per i pendolari comodi
                    elif cat_prov != "Padova Centro" and "Auto" in mezzo_utente:
                        if spot in ["CITTADELLA", "NOALE", "CASTELFRANCO"]:
                            costo_algoritmo -= 150 # Sconto per evitare il traffico verso le città grandi
                    
                    # Sconti Preferenze
                    if spot in scelta_1: costo_algoritmo -= 400
                    elif spot in scelta_2: costo_algoritmo -= 150
                        
                    # MURO DI SICUREZZA 50 KM
                    if dist > 50 and spot not in scelta_1 and spot not in scelta_2:
                        costo_algoritmo += 1000 
                        
                    cost_matrix[i, j] = costo_algoritmo
            
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            risultati = []
            for idx in range(n_people):
                assigned_spot = spots[col_ind[idx]]
                
                # Calcola Esito
                scelta_1 = str(df.iloc[idx, 4])
                scelta_2 = str(df.iloc[idx, 5])
                if assigned_spot in scelta_1: esito = "1ª Scelta"
                elif assigned_spot in scelta_2: esito = "2ª Scelta"
                else: esito = "Adattamento Logistico"
                
                risultati.append({
                    "Nome Studente": df.iloc[idx, 0], 
                    "Provenienza": df.iloc[idx, 1],
                    "Sede Assegnata": f"Ospedale di {assigned_spot.title()}",
                    "Esito": esito,
                    "Info Trasporti": "Stazione Vicina" if comodita_stazione.get(assigned_spot, 0) <= 1 else "Consigliata Auto"
                })
                
            df_risultati = pd.DataFrame(risultati).sort_values(by=["Sede Assegnata", "Nome Studente"])
            
            st.write("### Assegnazioni Finali Calcolate")
            st.dataframe(df_risultati, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_risultati.to_excel(writer, index=False, sheet_name='Assegnazioni')
            
            st.download_button(
                label="📥 Scarica l'Excel Definitivo",
                data=output.getvalue(),
                file_name="Assegnazioni_Tirocinio_Ottimizzate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
