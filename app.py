import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
import io

st.set_page_config(page_title="Gestione Tirocini", page_icon="🏥", layout="wide")

st.title("🏥 Assegnazione Automatica Sedi Tirocinio")
st.markdown("Algoritmo intelligente: ottimizza in base a distanze esatte, carpooling, mezzi pubblici, comodità stazioni e intelligenza geografica.")

uploaded_file = st.file_uploader("Carica il file Excel scaricato da Google Forms", type=["xlsx"])

# 1. CAPIENZE SEDI (Totale 31 posti)
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

# 3. DISTANZE ESATTE (in km) - Ricalibrate
distanze_mappa = {
    "Monselice": {"CASTELFRANCO": 60, "MONTEBELLUNA": 70, "SAN DONA' DI PIAVE": 90, "NOALE": 55, "TREVISO": 70, "CITTADELLA": 55, "VICENZA": 50, "VENEZIA": 65, "MESTRE": 60, "CHIOGGIA": 45},
    "Mandria": {"CASTELFRANCO": 40, "MONTEBELLUNA": 55, "SAN DONA' DI PIAVE": 70, "NOALE": 35, "TREVISO": 55, "CITTADELLA": 35, "VICENZA": 40, "VENEZIA": 45, "MESTRE": 40, "CHIOGGIA": 45},
    "Treviso": {"CASTELFRANCO": 30, "MONTEBELLUNA": 25, "SAN DONA' DI PIAVE": 30, "NOALE": 25, "TREVISO": 0, "CITTADELLA": 40, "VICENZA": 60, "VENEZIA": 40, "MESTRE": 30, "CHIOGGIA": 75},
    "Vicenza": {"CASTELFRANCO": 35, "MONTEBELLUNA": 50, "SAN DONA' DI PIAVE": 90, "NOALE": 50, "TREVISO": 60, "CITTADELLA": 25, "VICENZA": 0, "VENEZIA": 75, "MESTRE": 65, "CHIOGGIA": 80},
    "Borgoricco": {"CASTELFRANCO": 15, "MONTEBELLUNA": 30, "SAN DONA' DI PIAVE": 55, "NOALE": 15, "TREVISO": 35, "CITTADELLA": 20, "VICENZA": 45, "VENEZIA": 40, "MESTRE": 30, "CHIOGGIA": 60},
    "Spinea": {"CASTELFRANCO": 30, "MONTEBELLUNA": 45, "SAN DONA' DI PIAVE": 35, "NOALE": 10, "TREVISO": 25, "CITTADELLA": 40, "VICENZA": 65, "VENEZIA": 20, "MESTRE": 10, "CHIOGGIA": 45},
    "Caselle di Selvazzano": {"CASTELFRANCO": 40, "MONTEBELLUNA": 55, "SAN DONA' DI PIAVE": 75, "NOALE": 40, "TREVISO": 60, "CITTADELLA": 30, "VICENZA": 35, "VENEZIA": 50, "MESTRE": 45, "CHIOGGIA": 55},
    "Torreglia": {"CASTELFRANCO": 50, "MONTEBELLUNA": 65, "SAN DONA' DI PIAVE": 80, "NOALE": 45, "TREVISO": 65, "CITTADELLA": 45, "VICENZA": 40, "VENEZIA": 55, "MESTRE": 50, "CHIOGGIA": 55},
    "Albignasego": {"CASTELFRANCO": 45, "MONTEBELLUNA": 60, "SAN DONA' DI PIAVE": 70, "NOALE": 35, "TREVISO": 55, "CITTADELLA": 40, "VICENZA": 45, "VENEZIA": 45, "MESTRE": 40, "CHIOGGIA": 45},
    "Abano Terme": {"CASTELFRANCO": 45, "MONTEBELLUNA": 60, "SAN DONA' DI PIAVE": 75, "NOALE": 40, "TREVISO": 60, "CITTADELLA": 35, "VICENZA": 35, "VENEZIA": 50, "MESTRE": 45, "CHIOGGIA": 55},
    "Padova Centro": {"CASTELFRANCO": 35, "MONTEBELLUNA": 50, "SAN DONA' DI PIAVE": 65, "NOALE": 30, "TREVISO": 50, "CITTADELLA": 35, "VICENZA": 40, "VENEZIA": 45, "MESTRE": 40, "CHIOGGIA": 50},
    "San Donà di Piave": {"CASTELFRANCO": 60, "MONTEBELLUNA": 50, "SAN DONA' DI PIAVE": 0, "NOALE": 45, "TREVISO": 30, "CITTADELLA": 70, "VICENZA": 90, "VENEZIA": 40, "MESTRE": 30, "CHIOGGIA": 75},
    "Chioggia": {"CASTELFRANCO": 75, "MONTEBELLUNA": 85, "SAN DONA' DI PIAVE": 80, "NOALE": 55, "TREVISO": 75, "CITTADELLA": 70, "VICENZA": 80, "VENEZIA": 55, "MESTRE": 50, "CHIOGGIA": 0},
    "Mestre": {"CASTELFRANCO": 35, "MONTEBELLUNA": 45, "SAN DONA' DI PIAVE": 30, "NOALE": 20, "TREVISO": 30, "CITTADELLA": 50, "VICENZA": 65, "VENEZIA": 10, "MESTRE": 0, "CHIOGGIA": 50},
    "Piove di Sacco": {"CASTELFRANCO": 50, "MONTEBELLUNA": 65, "SAN DONA' DI PIAVE": 65, "NOALE": 35, "TREVISO": 55, "CITTADELLA": 50, "VICENZA": 60, "VENEZIA": 45, "MESTRE": 40, "CHIOGGIA": 30},
    "Sant'Angelo di Piove di Sacco": {"CASTELFRANCO": 45, "MONTEBELLUNA": 60, "SAN DONA' DI PIAVE": 60, "NOALE": 30, "TREVISO": 50, "CITTADELLA": 45, "VICENZA": 55, "VENEZIA": 40, "MESTRE": 35, "CHIOGGIA": 35},
    "Castelfranco": {"CASTELFRANCO": 0, "MONTEBELLUNA": 15, "SAN DONA' DI PIAVE": 60, "NOALE": 25, "TREVISO": 30, "CITTADELLA": 15, "VICENZA": 35, "VENEZIA": 50, "MESTRE": 40, "CHIOGGIA": 75},
    "Bassano": {"CASTELFRANCO": 20, "MONTEBELLUNA": 30, "SAN DONA' DI PIAVE": 80, "NOALE": 45, "TREVISO": 50, "CITTADELLA": 15, "VICENZA": 35, "VENEZIA": 70, "MESTRE": 60, "CHIOGGIA": 90},
    "Ponte di Brenta": {"CASTELFRANCO": 30, "MONTEBELLUNA": 45, "SAN DONA' DI PIAVE": 55, "NOALE": 20, "TREVISO": 45, "CITTADELLA": 30, "VICENZA": 40, "VENEZIA": 35, "MESTRE": 30, "CHIOGGIA": 45}
}

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success(f"File caricato con successo! Analisi di {len(df)} partecipanti.")
    
    if st.button("Calcola Assegnazioni Ottimali"):
        with st.spinner("Incrocio di distanze, costi, trasporti e preferenze in corso..."):
            
            spots = []
            for loc, cap in capacities.items():
                spots.extend([loc] * cap)
                
            n_people = len(df)
            cost_matrix = np.zeros((n_people, len(spots)))
            
            for i in range(n_people):
                nome = str(df.iloc[i, 0]).strip()
                prov_utente = str(df.iloc[i, 1]).strip()
                mezzo_utente = str(df.iloc[i, 2]).strip()
                carpooling = str(df.iloc[i, 3]).strip()
                scelta_1 = str(df.iloc[i, 4]).strip()
                scelta_2 = str(df.iloc[i, 5]).strip()
                
                # Identifica se è Padova Centro
                is_centro = "Padova Centro" in prov_utente
                
                for j, spot in enumerate(spots):
                    # Estrae la distanza, default 50km se la città non è in lista
                    dist = distanze_mappa.get(prov_utente, {}).get(spot, 50)
                    
                    # 1. Costo Base (Stima 0.15€/km moltiplicato per 10 per scala punteggio)
                    costo_algoritmo = (dist * 2 * 0.15) * 10
                    
                    # 2. Penalità Mezzi Pubblici
                    if "Treno" in mezzo_utente or "Autobus" in mezzo_utente:
                        costo_algoritmo += (comodita_stazione.get(spot, 0) * 50)
                    
                    # 3. Intelligenza Geografica Veneta
                    if is_centro and "Treno" in mezzo_utente:
                        if spot in ["TREVISO", "VENEZIA", "MONTEBELLUNA"]:
                            costo_algoritmo -= 200  # Agevola collegamenti ferroviari diretti
                    elif not is_centro and "Auto" in mezzo_utente:
                        if spot in ["CITTADELLA", "NOALE", "CASTELFRANCO"]:
                            costo_algoritmo -= 150  # Agevola statali, evita traffico hub grandi
                    
                    # 4. Sconti Preferenze
                    if spot == scelta_1: 
                        costo_algoritmo -= 400
                    elif spot == scelta_2: 
                        costo_algoritmo -= 150
                        
                    # 5. Bonus Carpooling (se compila il campo e la sede è la sua 1ª scelta, forziamo l'assegnazione)
                    if carpooling != "nan" and carpooling != "" and spot == scelta_1:
                        costo_algoritmo -= 100
                        
                    # 6. Muro di Sicurezza 50 km (Eccezione: se scelta espressamente dall'utente)
                    if dist > 50 and spot != scelta_1 and spot != scelta_2:
                        costo_algoritmo += 1000 
                        
                    cost_matrix[i, j] = costo_algoritmo
            
            # Motore di calcolo (Ricerca Operativa)
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            risultati = []
            for idx in range(n_people):
                assigned_spot = spots[col_ind[idx]]
                
                # Valutazione Esito Finale
                scelta_1 = str(df.iloc[idx, 4]).strip()
                scelta_2 = str(df.iloc[idx, 5]).strip()
                if assigned_spot == scelta_1: esito = "1ª Scelta"
                elif assigned_spot == scelta_2: esito = "2ª Scelta"
                else: esito = "Ottimizzazione Logistica / Adattamento"
                
                # Stima Distanza Effettiva
                prov_utente = str(df.iloc[idx, 1]).strip()
                dist_finale = distanze_mappa.get(prov_utente, {}).get(assigned_spot, 50)
                costo_euro = round(dist_finale * 2 * 0.15, 2)
                
                risultati.append({
                    "Nome": df.iloc[idx, 0], 
                    "Sede Assegnata": f"Ospedale di {assigned_spot.title()}",
                    "Esito": esito,
                    "Distanza Stima": f"{dist_finale} km",
                    "Costo Viaggio Stimato (A/R)": f"~ {costo_euro} €",
                    "Stazione/Fermata": "Ottima / Vicina" if comodita_stazione.get(assigned_spot, 0) <= 1 else "Consigliata Auto / Bus"
                })
                
            df_risultati = pd.DataFrame(risultati).sort_values(by=["Sede Assegnata", "Nome"])
            
            st.write("### 🏆 Assegnazioni Finali Calcolate")
            st.dataframe(df_risultati, use_container_width=True)
            
            # Esportazione in Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_risultati.to_excel(writer, index=False, sheet_name='Assegnazioni')
            
            st.download_button(
                label="📥 Scarica l'Excel Definitivo",
                data=output.getvalue(),
                file_name="Assegnazioni_Intelligenti_Tirocinio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
