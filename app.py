import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
import io
import math

st.set_page_config(page_title="Gestione Tirocini", page_icon="🏥", layout="wide")

st.sidebar.header("⚙️ Pannello Posti Disponibili")
st.sidebar.markdown("Modifica i posti definitivi.")

sedi_lista = ["CASTELFRANCO", "MONTEBELLUNA", "SAN DONA' DI PIAVE", "NOALE", "TREVISO", "CITTADELLA", "VICENZA", "VENEZIA", "MESTRE", "CHIOGGIA"]
default_posti = [4, 3, 2, 4, 10, 3, 2, 1, 1, 1] 

capacities = {}
for sede, default in zip(sedi_lista, default_posti):
    capacities[sede] = st.sidebar.number_input(f"Posti a {sede}", min_value=0, max_value=50, value=default, step=1)

totale_posti = sum(capacities.values())
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Totale posti impostati:** {totale_posti}")

st.markdown("""
<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #0066cc;'>
    <h3 style='margin: 0; color: #003366;'>🏥 Assegnazione Automatica Sedi Tirocinio</h3>
    <p style='margin: 5px 0 0 0; color: #333333;'>
        <b>Algoritmo rigoroso:</b> Precedenza assoluta alla vicinanza (&lt; 25 km). Le preferenze contano solo se non sono presenti sedi nei limitrofi.
    </p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Carica il file Excel scaricato da Google Forms", type=["xlsx"])

comodita_stazione = {
    "CITTADELLA": 0, "CASTELFRANCO": 0, "SAN DONA' DI PIAVE": 1, 
    "VENEZIA": 1, "TREVISO": 2, "MESTRE": 2, "MONTEBELLUNA": 2,
    "VICENZA": 2, "NOALE": 3, "CHIOGGIA": 5
}

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
    "Ponte di Brenta": {"CASTELFRANCO": 30, "MONTEBELLUNA": 45, "SAN DONA' DI PIAVE": 55, "NOALE": 20, "TREVISO": 45, "CITTADELLA": 30, "VICENZA": 40, "VENEZIA": 35, "MESTRE": 30, "CHIOGGIA": 45},
    "Dolo": {"CASTELFRANCO": 35, "MONTEBELLUNA": 50, "SAN DONA' DI PIAVE": 45, "NOALE": 15, "TREVISO": 35, "CITTADELLA": 40, "VICENZA": 60, "VENEZIA": 25, "MESTRE": 20, "CHIOGGIA": 40},
    "Quarto d'Altino": {"CASTELFRANCO": 40, "MONTEBELLUNA": 45, "SAN DONA' DI PIAVE": 20, "NOALE": 25, "TREVISO": 20, "CITTADELLA": 55, "VICENZA": 75, "VENEZIA": 25, "MESTRE": 15, "CHIOGGIA": 60}
}

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    studenti_totali = len(df)
    
    st.success(f"File caricato! Trovati {studenti_totali} partecipanti.")
    
    if totale_posti < studenti_totali:
        st.warning(f"⚠️ Ci sono {studenti_totali} studenti ma solo {totale_posti} posti ufficiali.")
    
    if st.button("Calcola Assegnazioni Ottimali"):
        with st.spinner("Calcolo basato su rigore chilometrico in corso..."):
            
            spots = []
            for loc, cap in capacities.items():
                spots.extend([loc] * cap)
            
            if totale_posti < studenti_totali:
                deficit = studenti_totali - totale_posti
                extra_per_sede = max(1, math.ceil(deficit / len(capacities)))
                for loc in capacities.keys():
                    spots.extend([loc] * extra_per_sede)
                    
            n_people = len(df)
            cost_matrix = np.zeros((n_people, len(spots)))
            
            for i in range(n_people):
                prov_utente = str(df.iloc[i, 1]).strip()
                mezzo_utente = str(df.iloc[i, 2]).strip()
                carpooling = str(df.iloc[i, 3]).strip()
                scelta_1 = str(df.iloc[i, 4]).strip()
                scelta_2 = str(df.iloc[i, 5]).strip()
                
                try:
                    stazione_casa = str(df.iloc[i, 6]).strip()
                except IndexError:
                    stazione_casa = "Media" 
                
                is_centro = "Padova Centro" in prov_utente
                
                # VERIFICA PREVENTIVA: Questo utente ha ALMENO UNA sede a meno di 25 km?
                distanze_utente = distanze_mappa.get(prov_utente, {s: 50 for s in capacities.keys()})
                ha_sede_vicina = any(d <= 25 for d in distanze_utente.values())
                
                for j, spot in enumerate(spots):
                    dist = distanze_utente.get(spot, 50)
                    
                    # 1. Costo Base Chilometrico (fortemente ponderato)
                    costo_algoritmo = (dist * 2 * 0.15) * 20 
                    
                    # 2. Penalità Mezzi Pubblici
                    if "Treno" in mezzo_utente or "Autobus" in mezzo_utente:
                        moltiplicatore = 100 if "Scomoda" in stazione_casa else 50
                        costo_algoritmo += (comodita_stazione.get(spot, 0) * moltiplicatore)
                    
                    # 3. Intelligenza Geografica Veneta
                    if is_centro and "Treno" in mezzo_utente:
                        if spot in ["TREVISO", "VENEZIA", "MONTEBELLUNA"]:
                            costo_algoritmo -= 200  
                    elif not is_centro and "Auto" in mezzo_utente:
                        if spot in ["CITTADELLA", "NOALE", "CASTELFRANCO"]:
                            costo_algoritmo -= 150  
                    
                    # 4. REGOLA DELLE PREFERENZE CONDIZIONATE DALLA DISTANZA
                    if ha_sede_vicina:
                        # Se l'utente HA sedi vicine (<25 km), la preferenza vale SOLO SE la sede scelta è effettivamente vicina (<= 25km).
                        # Se ha scelto una sede lontana, penalizziamo la scelta per dare priorità a chi abita lì vicino.
                        if spot == scelta_1:
                            if dist <= 25:
                                costo_algoritmo -= 600  # Ottimo: vuole la sede vicino a casa ed è vicina
                            else:
                                costo_algoritmo += 300  # Penalità: ha sedi vicine ma vuole ostinarsi ad andare lontano
                        elif spot == scelta_2:
                            if dist <= 25:
                                costo_algoritmo -= 300
                            else:
                                costo_algoritmo += 150
                    else:
                        # Se l'utente NON HA sedi vicine (<25 km), allora le sue preferenze vengono sbloccate pienamente!
                        if spot == scelta_1:
                            costo_algoritmo -= 800  # Sblocco totale preferenza perché è isolato geograficamente
                        elif spot == scelta_2:
                            costo_algoritmo -= 400
                        
                    # 5. Bonus Carpooling
                    if carpooling != "nan" and carpooling != "" and spot == scelta_1:
                        costo_algoritmo -= 200
                        
                    # 6. Muro di Sicurezza 50 km (tranne se è l'unica opzione per chi non ha sedi vicine)
                    if dist > 50 and spot != scelta_1 and spot != scelta_2:
                        costo_algoritmo += 1500 
                        
                    cost_matrix[i, j] = costo_algoritmo
            
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            posti_occupati = {loc: 0 for loc in capacities.keys()}
            risultati = []
            
            for idx in range(n_people):
                assigned_spot = spots[col_ind[idx]]
                posti_occupati[assigned_spot] += 1
                
                if posti_occupati[assigned_spot] <= capacities[assigned_spot]:
                    stato_assegnazione = "✅ Confermato"
                else:
                    stato_assegnazione = "⚠️ PROVVISORIO (Sovrannumero)"
                
                scelta_1 = str(df.iloc[idx, 4]).strip()
                scelta_2 = str(df.iloc[idx, 5]).strip()
                if assigned_spot == scelta_1: esito = "1ª Scelta"
                elif assigned_spot == scelta_2: esito = "2ª Scelta"
                else: esito = "Adattamento Logistico"
                
                prov_utente = str(df.iloc[idx, 1]).strip()
                dist_finale = distanze_mappa.get(prov_utente, {}).get(assigned_spot, 50)
                costo_euro = round(dist_finale * 2 * 0.15, 2)
                
                risultati.append({
                    "Nome": df.iloc[idx, 0], 
                    "Sede Assegnata": f"Ospedale di {assigned_spot.title()}",
                    "Stato": stato_assegnazione,
                    "Motivazione": esito,
                    "Distanza Stima": f"{dist_finale} km",
                    "Costo Viaggio (A/R)": f"~ {costo_euro} €",
                    "Stazione/Fermata": "Vicina/Comoda" if comodita_stazione.get(assigned_spot, 0) <= 1 else "Consigliata Auto"
                })
                
            df_risultati = pd.DataFrame(risultati).sort_values(by=["Sede Assegnata", "Stato", "Nome"])
            
            st.write("### 🏆 Assegnazioni Finali Calcolate (Rigorose per Distanza)")
            st.dataframe(df_risultati, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_risultati.to_excel(writer, index=False, sheet_name='Assegnazioni')
            
            st.download_button(
                label="📥 Scarica l'Excel Definitivo",
                data=output.getvalue(),
                file_name="Assegnazioni_Rigorose_Tirocinio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
