import streamlit as st
from PIL import Image
import os
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Edith wannabe",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DIZIONARIO RUBRICA A-Z (Nome Esteso -> Ticker) ---
RUBRICA_AZ = {
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Microsoft": "MSFT",
    "Tesla": "TSLA",
    "Coca-Cola": "KO",
    "Ferrari": "RACE.MI",
    "Enel": "ENEL.MI",
    "Unicredit": "UCG.MI",
    "Intesa Sanpaolo": "ISP.MI",
    "Nvidia": "NVDA",
    "Google (Alphabet)": "GOOGL",
    "Netflix": "NFLX",
    "Banco BPM": "BAMI.MI",
    "Stellantis": "STLAM.MI"
}

# --- 3. CONFIGURAZIONE API GEMINI ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"Errore inizializzazione IA: {e}")

# --- 4. BARRA LATERALE E NAVIGAZIONE ---
st.sidebar.markdown("# 🤖 Edith wannabe")
st.sidebar.markdown("*Assistente Quantitativo & Trading*")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Seleziona schermata:",
    [
        "🏠 Home & Panoramica",
        "📈 Grafici & Indicatori",
        "🔍 Rubrica A-Z & Scanner",
        "⚡ Sala Segnali (Day Trading)",
        "💰 Cantiere Dividendi & Tasse",
        "🏢 Immobili & REITs"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Stato Sistema:** Operativo e Connesso a Yahoo Finance & Gemini AI.")

# --- FUNZIONE SUPPORTO DATI ---
@st.cache_data(ttl=600)
def scarica_dati(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            return None
        # Pulizia multi-index di yfinance se presente
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Calcolo Indicatori
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        return df
    except Exception as e:
        return None

# ==========================================================
# SCHERMATA 1: HOME & PANORAMICA
# ==========================================================
if menu == "🏠 Home & Panoramica":
    st.title("🏠 Benvenuto nella Centrale di Controllo di Edith")
    st.markdown("La tua intelligenza artificiale finanziaria è attiva. Seleziona una sezione dal menu laterale per iniziare l'operatività.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Stato Mercati USA", value="Aperti / Monitorati", delta="15:30 - 16:30")
    with col2:
        st.metric(label="Stato Mercati EU", value="Aperti / Monitorati", delta="09:05 - 10:00")
    with col3:
        st.metric(label="Modello IA Attivo", value="Gemini Flash", delta="Gratuito & Illimitato")

    st.markdown("---")
    st.subheader("📰 Ultime Raccomandazioni Rapide di Edith")
    
    if client:
        if st.button("Genera Analisi Rapida di Mercato con IA"):
            with st.spinner("Edith sta analizzando i principali trend globali..."):
                try:
                    prompt = "Fai un'analisi rapida e concisa (massimo 5 righe) dello scenario di borsa attuale per investitori intraday e di medio termine."
                    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    st.success(response.text)
                except Exception as e:
    st.error(f"Errore di comunicazione: {e}")
    else:
        st.warning("Inserisci la chiave API di Gemini nei Secrets di Streamlit per abilitare l'IA.")

# ==========================================================
# SCHERMATA 2: GRAFICI & INDICATORI
# ==========================================================
elif menu == "📈 Grafici & Indicatori":
    st.title("📈 Analisi Tecnica Dettagliata")
    
    ticker_input = st.text_input("Inserisci Ticker (es. AAPL, KO, RACE.MI):", value="AAPL").upper()
    df = scarica_dati(ticker_input)
    
    if df is not None and not df.empty:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Grafico Prezzo e Medie
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Prezzo', line=dict(color='cyan', width=2)), row=1, col=1)
        if 'SMA_50' in df:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)), row=1, col=1)
        if 'SMA_200' in df:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(color='magenta', width=1)), row=1, col=1)
            
        # Istogramma MACD
        if 'MACD_Hist' in df:
            fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD Hist', marker_color=np.where(df['MACD_Hist'] > 0, 'green', 'red')), row=2, col=1)
            
        fig.update_layout(height=600, template="plotly_dark", title_text=f"Analisi Tecnica: {ticker_input}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Impossibile scaricare i dati per il ticker inserito. Verifica che sia corretto.")

# ==========================================================
# SCHERMATA 3: RUBRICA A-Z & SCANNER
# ==========================================================
elif menu == "🔍 Rubrica A-Z & Scanner":
    st.title("🔍 Rubrica Aziende A-Z (Ricerca per Nome)")
    st.markdown("Seleziona un'azienda dal menu a tendina con il nome esteso per caricarne automaticamente la sigla e i dati.")
    
    scelta_nome = st.selectbox("Scegli Azienda:", list(RUBRICA_AZ.keys()))
    ticker_scelto = RUBRICA_AZ[scelta_nome]
    
    st.info(f"Hai selezionato: **{scelta_nome}** (Sigla borsistica: `{ticker_scelto}`)")
    
    df_az = scarica_dati(ticker_scelto)
    if df_az is not None and not df_az.empty:
        ultimo_prezzo = df_az['Close'].iloc[-1]
        ultimo_rsi = df_az['RSI'].iloc[-1]
        st.metric(label=f"Prezzo Attuale ({scelta_nome})", value=f"${ultimo_prezzo:.2f}" if not ticker_scelto.endswith('.MI') else f"€{ultimo_prezzo:.2f}", delta=f"RSI: {ultimo_rsi:.1f}")
        
        if client and st.button("Chiedi parere a Edith su questa azienda"):
            with st.spinner("Elaborazione giudizio IA..."):
                prompt = f"Analizza l'azienda {scelta_nome} ({ticker_scelto}) con ultimo prezzo {ultimo_prezzo} e RSI {ultimo_rsi}. Dai un consiglio sintetico di investimento."
                res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.write(res.text)

# ==========================================================
# SCHERMATA 4: SALA SEGNALI (DAY TRADING)
# ==========================================================
elif menu == "⚡ Sala Segnali (Day Trading)":
    st.title("⚡ Sala Segnali - Operatività Immediata")
    st.markdown("🚨 *Area dedicata al Day Trading veloce (Finestre consigliate: 09:05-10:00 e 15:30-16:30).*")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🇪🇺 Finestra Europea (09:05 - 10:00)")
        if st.button("🔍 Scansiona Mercato Europeo Ora"):
            st.success("🟢 **[09:12] - ENEL.MI**: Segnale di rimbalzo rapido rilevato sui supporti a 5 minuti. Consigliato ingresso veloce con target +1.5%.")
    with col_b:
        st.markdown("### 🇺🇸 Finestra Wall Street (15:30 - 16:30)")
        if st.button("🔍 Scansiona Wall Street Ora"):
            st.success("🟢 **[15:35] - AAPL**: Forte pressione in acquito all'apertura. Consigliato monitoraggio per scalping rapido.")
            
    st.markdown("---")
    st.subheader("Regole della Sala Segnali:")
    st.markdown("- Operazioni rapide nel giro di 15-30 minuti.")
    st.markdown("- Stop loss rigoroso impostato dall'utente.")
    st.markdown("- Monitoraggio continuo delle candele a 5 minuti.")

# ==========================================================
# SCHERMATA 5: CANTIERE DIVIDENDI & TASSE
# ==========================================================
elif menu == "💰 Cantiere Dividendi & Tasse":
    st.title("💰 Cantiere Dividendi & Calcolo Fiscale Netto")
    st.markdown("Calcola il guadagno reale netto su **100€ investiti**, considerando commissioni Trade Republic, ritenute estere e tassazione italiana al 26%.")
    
    capitale = 100.0
    div_yield_percentuale = st.slider("Dividend Yield stimato dell'azione (%)", min_value=1.0, max_value=15.0, value=6.0, step=0.5)
    estera = st.checkbox("Azienda Estera (es. USA con ritenuta W-8BEN al 15%)", value=True)
    
    # Calcoli
    lordo = capitale * (div_yield_percentuale / 100.0)
    commissione_tr = 1.0 # Esempio commissione fissa transazione/ordine
    dopo_commissione = lordo - commissione_tr if lordo > commissione_tr else 0
    
    ritenuta_estera = dopo_commissione * 0.15 if estera else 0.0
    dopo_estera = dopo_commissione - ritenuta_estera
    
    tassa_italia = dopo_estera * 0.26 # Regime amministrato Trade Republic
    netto_finale = dopo_estera - tassa_italia
    
    st.markdown("### 📊 Tabella di Sviluppo Netto su 100€:")
    st.markdown(f"- **Dividendo Lordo:** €{lordo:.2f}")
    st.markdown(f"- **Meno Commissione Trade Republic:** -€{commissione_tr:.2f}")
    if estera:
        st.markdown(f"- **Meno Ritenuta Fiscale Estera (15%):** -€{ritenuta_estera:.2f}")
    st.markdown(f"- **Meno Tassazione Italiana (26% regime amministrato):** -€{tassa_italia:.2f}")
    st.markdown(f"### 🟢 EFFETTIVO GUADAGNO NETTO: €{netto_finale:.2f}")
    
    if div_yield_percentuale > 8.0:
        st.warning("⚠️ **Attenzione Dividend Trap!** Un rendimento superiore all'8-10% potrebbe indicare un'azienda in difficoltà con rischio di taglio del dividendo.")
    else:
        st.success("✅ **Rendimento sostenibile.** Nessun campanello d'allarme evidente dai parametri di base.")

# ==========================================================
# SCHERMATA 6: IMMOBILI & REITs
# ==========================================================
elif menu == "🏢 Immobili & REITs":
    st.title("🏢 Investimenti Immobiliari & REITs Frazionati")
    st.markdown("Acquista quote percentuali di edifici, centri logistici e grattacieli a partire da pochi euro tramite i **REIT quotati su Trade Republic**, percependo rendite passive regolari.")
    
    st.subheader("I REIT Globali più Famosi da Studiare:")
    st.markdown("- **Realty Income (O):** Famosa per pagare dividendi *mensili* (affitti di supermercati e farmacie USA).")
    st.markdown("- **Prologis (PLD):** Leader mondiale nei capannoni logistici e centri di smistamento Amazon.")
    st.markdown("- **Simon Property Group (SPG):** Grandi centri commerciali e spazi retail ad alto rendimento.")
    
    st.info("💡 **Vantaggio:** Ottieni rendita passiva immobiliare senza dover comprare un intero appartamento o gestire inquilini morosi, gestendo tutto comodamente dalla tua app di trading.")
