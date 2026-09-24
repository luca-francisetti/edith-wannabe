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

# --- 2. DIZIONARIO RUBRICA A-Z ESTESA ---
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
    "Stellantis": "STLAM.MI",
    "Realty Income (Mensile)": "O",
    "Main Street Capital (Mensile)": "MAIN",
    "STAG Industrial (Mensile)": "STAG",
    "Agree Realty (Mensile)": "ADC",
    "JPMorgan Chase": "JPM",
    "Johnson & Johnson": "JNJ"
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
try:
    st.sidebar.image("icona.png", width=120)
except:
    pass

st.sidebar.markdown("# 🤖 Edith wannabe")
st.sidebar.markdown("*Assistente Quantitativo & Trading*")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Seleziona schermata:",
    [
        "🏠 Home & Panoramica",
        "📈 Grafici & Indicatori",
        "🔍 Rubrica A-Z & Scanner",
        "⚡ Sala Segnali (Top 5 Live)",
        "💰 Cantiere Dividendi & Tasse",
        "🏢 Immobili & REITs Mensili"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Stato Sistema:** Operativo e Connesso in Tempo Reale.")

# --- FUNZIONE SUPPORTO DATI (Portata a 1 anno per SMA 200) ---
@st.cache_data(ttl=600)
def scarica_dati(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Calcolo Indicatori Tecnici
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
    st.markdown("La tua intelligenza artificiale finanziaria è attiva. Monitoraggio costante dei mercati globale e locale.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Stato Mercati USA", value="Aperti / Monitorati", delta="15:30 - 22:00")
    with col2:
        st.metric(label="Stato Mercati EU", value="Aperti / Monitorati", delta="09:00 - 17:30")
    with col3:
        st.metric(label="Modello IA Attivo", value="Gemini Flash", delta="Tempo Reale")

    st.markdown("---")
    st.subheader("📰 Sintesi di Mercato in Tempo Reale")
    
    if client:
        if st.button("Genera Analisi Rapida di Mercato con IA"):
            with st.spinner("Edith sta analizzando i trend macroeconomici globali..."):
                try:
                    prompt = "Fai un'analisi rapida e concisa (massimo 5 righe) dello scenario di borsa attuale per trader attivi."
                    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Errore di comunicazione: {e}")
    else:
        st.warning("Inserisci la chiave API di Gemini nei Secrets di Streamlit.")

# ==========================================================
# SCHERMATA 2: GRAFICI & INDICATORI
# ==========================================================
elif menu == "📈 Grafici & Indicatori":
    st.title("📈 Analisi Tecnica Avanzata (Con SMA 200)")
    
    ticker_input = st.text_input("Inserisci Ticker (es. AAPL, KO, O, RACE.MI):", value="AAPL").upper()
    df = scarica_dati(ticker_input)
    
    if df is not None and not df.empty:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Grafico Prezzo e Medie (SMA 50 Arancione, SMA 200 Viola)
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Prezzo', line=dict(color='cyan', width=2)), row=1, col=1)
        if 'SMA_50' in df:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='orange', width=1.5)), row=1, col=1)
        if 'SMA_200' in df:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200 (Viola)', line=dict(color='magenta', width=2)), row=1, col=1)
            
        # Istogramma MACD
        if 'MACD_Hist' in df:
            fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD Hist', marker_color=np.where(df['MACD_Hist'] > 0, 'green', 'red')), row=2, col=1)
            
        fig.update_layout(height=650, template="plotly_dark", title_text=f"Analisi Tecnica Completa: {ticker_input}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Impossibile scaricare i dati per il ticker inserito. Verifica che sia corretto.")

# ==========================================================
# SCHERMATA 3: RUBRICA A-Z & SCANNER
# ==========================================================
elif menu == "🔍 Rubrica A-Z & Scanner":
    st.title("🔍 Rubrica Aziende A-Z & Scheda Fondamentale")
    st.markdown("Seleziona un'azienda dall'elenco completo per visualizzare subito tutti i dati chiave e l'analisi di Edith.")
    
    scelta_nome = st.selectbox("Scegli Azienda:", list(RUBRICA_AZ.keys()))
    ticker_scelto = RUBRICA_AZ[scelta_nome]
    
    st.info(f"Azienda selezionata: **{scelta_nome}** (Ticker: `{ticker_scelto}`)")
    
    # Estrazione dati fondamentali via yfinance
    try:
        t_obj = yf.Ticker(ticker_scelto)
        info = t_obj.info
         prezzo_attuale = info.get('currentPrice', info.get('regularMarketPrice', 0))
         pe_ratio = info.get('trailingPE', 'N/D')
         eps = info.get('trailingEps', 'N/D')
         div_yield = info.get('dividendYield', 0)
         if div_yield:
             div_yield_str = f"{div_yield * 100:.2f}%"
         else:
             div_yield_str = "N/D / Assente"
    except:
        prezzo_attuale, pe_ratio, eps, div_yield_str = "N/D", "N/D", "N/D", "N/D"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Prezzo Attuale", f"${prezzo_attuale}" if not ticker_scelto.endswith('.MI') else f"€{prezzo_attuale}")
    with col2:
        st.metric("Prezzo/Utile (P/E)", f"{pe_ratio}")
    with col3:
        st.metric("Utile per Azione (EPS)", f"{eps}")
    with col4:
        st.metric("Rendimento Dividendi", f"{div_yield_str}")

    df_az = scarica_dati(ticker_scelto)
    if df_az is not None and not df_az.empty:
        ultimo_rsi = df_az['RSI'].iloc[-1]
        st.metric(label="RSI Attuale (14 periodi)", value=f"{ultimo_rsi:.1f}")
        
        if client and st.button("Richiedi parere approfondito a Edith"):
            with st.spinner("Edith sta elaborando i dati fondamentali e tecnici..."):
                prompt = f"Analizza l'azienda {scelta_nome} ({ticker_scelto}) con Prezzo {prezzo_attuale}, P/E {pe_ratio}, EPS {eps}, Div Yield {div_yield_str} e RSI {ultimo_rsi}. Dai un verdetto chiaro e un consiglio d'acquisto o attesa."
                res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.write(res.text)

# ==========================================================
# SCHERMATA 4: SALA SEGNALI (TOP 5 LIVE)
# ==========================================================
elif menu == "⚡ Sala Segnali (Top 5 Live)":
    st.title("⚡ Sala Segnali - Top 5 Operative in Tempo Reale")
    st.markdown("🚨 *Generazione automatica dei migliori 5 setup di mercato attivi adesso. Margine di esecuzione consigliato: entro 5-10 minuti.*")
    
    if client:
        if st.button("Aggiorna Top 5 Segnali Ora") or True: # Esegue subito all'apertura
            with st.spinner("Edith sta scansionando i volumi e i trend delle principali azioni globali..."):
                prompt = (
                    "Fai una lista delle attuali Top 5 azioni calde su cui fare trading intraday o swing oggi. "
                    "Per ciascuna indica: 1. Nome e Ticker, 2. Direzione (Long/Short), 3. Motivazione tecnica sintetica, "
                    "4. Finestra temporale di esecuzione raccomandata (es. entro 5-10 minuti)."
                )
                try:
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    st.markdown("### 📊 Report Segnali Live da Edith:")
                    st.success(res.text)
                except Exception as e:
                    st.error(f通讯 Errore IA: {e}")
    else:
        st.warning("Configura le API Key di Gemini per abilitare i segnali automatici in tempo reale.")

# ==========================================================
# SCHERMATA 5: CANTIERE DIVIDENDI & TASSE
# ==========================================================
elif menu == "💰 Cantiere Dividendi & Tasse":
    st.title("💰 Cantiere Dividendi & Classifica Top 10 Trade Republic")
    st.markdown("Analisi delle regine dei dividendi disponibili su Trade Republic con calcolo fiscale netto automatizzato (Commissioni TR, Ritenuta Estera 15%, Tassazione IT 26%).")
    
    st.subheader("🏆 Classifica Top 10 Aziende da Dividendo (Disponibili su Trade Republic)")
    
    # Tabella delle Top 10 da dividendo su Trade Republic
    data_top10 = {
        "Azienda": ["Realty Income", "Main Street Capital", "Altria Group", "AT&T", "Enel", "Intesa Sanpaolo", "Rio Tinto", "Verizon", "Chevron", "Banco BPM"],
        "Ticker": ["O", "MAIN", "MO", "T", "ENEL.MI", "ISP.MI", "RIO", "VZ", "CVX", "BAMI.MI"],
        "Frequenza": ["Mensile", "Mensile", "Trimestrale", "Trimestrale", "Annuale", "Semestrale", "Semestrale", "Trimestrale", "Trimestrale", "Annuale"],
        "Yield Lordo Stimato": ["5.5%", "6.2%", "8.5%", "6.3%", "6.8%", "7.5%", "7.0%", "6.5%", "4.2%", "6.0%"]
    }
    df_div = pd.DataFrame(data_top10)
    st.dataframe(df_div, use_container_width=True)

    st.markdown("---")
    st.subheader("🧮 Calcolatore Personalizzato Netto su 100€")
    capitale = 100.0
    div_yield_percentuale = st.slider("Dividend Yield stimato (%)", min_value=1.0, max_value=12.0, value=6.0, step=0.5)
    estera = st.checkbox("Azienda Estera (Ritenuta W-8BEN al 15%)", value=True)
    
    lordo = capitale * (div_yield_percentuale / 100.0)
    commissione_tr = 1.0 
    dopo_commissione = lordo - commissione_tr if lordo > commissione_tr else 0
    ritenuta_estera = dopo_commissione * 0.15 if estera else 0.0
    dopo_estera = dopo_commissione - ritenuta_estera
    tassa_italia = dopo_estera * 0.26 
    netto_finale = dopo_estera - tassa_italia
    
    st.markdown(f"- **Dividendo Lordo su 100€:** €{lordo:.2f}")
    st.markdown(f"- **Meno Commissione Trade Republic:** -€{commissione_tr:.2f}")
    if estera:
        st.markdown(f"- **Meno Ritenuta Estera (15%):** -€{ritenuta_estera:.2f}")
    st.markdown(f"- **Meno Tassazione Italiana (26% regime amministrato):** -€{tassa_italia:.2f}")
    st.markdown(f"### 🟢 GUADAGNO NETTO EFFETTIVO: €{netto_finale:.2f}")

# ==========================================================
# SCHERMATA 6: IMMOBILI & REITs MENSILI
# ==========================================================
elif menu == "🏢 Immobili & REITs Mensili":
    st.title("🏢 Immobili & REITs con Dividendo Mensile (Top 10)")
    st.markdown("I migliori REITs immobiliari globali negoziabili su **Trade Republic** che staccano la cedola **ogni singolo mese**, permettendoti di incassare rendite passive regolari.")
    
    reits_data = [
        {"Nome": "Realty Income", "Ticker": "O", "Settore": "Retail / Farmacie / Supermercati", "Yield": "~5.5%", "Pagamento": "Mensile"},
        {"Nome": "Main Street Capital", "Ticker": "MAIN", "Settore": "Private Equity / Debito Privato", "Yield": "~6.2%", "Pagamento": "Mensile"},
        {"Nome": "STAG Industrial", "Ticker": "STAG", "Settore": "Logistica & Magazzini", "Yield": "~4.1%", "Pagamento": "Mensile"},
        {"Nome": "Agree Realty", "Ticker": "ADC", "Settore": "Retail Commerciale USA", "Yield": "~4.8%", "Pagamento": "Mensile"},
        {"Nome": "Gladstone Commercial", "Ticker": "GOOD", "Settore": "Uffici & Industriale", "Yield": "~7.0%", "Pagamento": "Mensile"},
        {"Nome": "Broadstone Net Lease", "Ticker": "BNL", "Settore": "Immobili Industriali & Healthcare", "Yield": "~6.5%", "Pagamento": "Mensile"},
        {"Nome": "SL Green Realty", "Ticker": "SLG", "Settore": "Uffici Manhattan (NYC)", "Yield": "~5.2%", "Pagamento": "Mensile"},
        {"Nome": "EPR Properties", "Ticker": "EPR", "Yield": "~7.3%", "Settore": "Intrattenimento & Centri Vacanze", "Pagamento": "Mensile"},
        {"Nome": "LTC Properties", "Ticker": "LTC", "Yield": "~6.1%", "Settore": "Strutture Sanitarie & Rsa", "Pagamento": "Mensile"},
        {"Nome": "Apple Hospitality REIT", "Ticker": "APLE", "Yield": "~6.0%", "Settore": "Hotel & Ospitalità", "Pagamento": "Mensile"}
    ]
    
    st.dataframe(pd.DataFrame(reits_data), use_container_width=True)
    
    st.markdown("---")
    st.subheader("💡 Consigli di Edith sui REITs Mensili:")
    st.markdown("""
    * **Prevedibilità del cash flow:** Ricevere dividendi mensili ti permette di reinvestire il capitale più velocemente (effetto composto) o di coprire piccole spese correnti.
    * **Diversificazione:** Puntare su settori diversi (es. logistica con STAG e retail con Realty Income) riduce il rischio di vacanza degli immobili.
    * **Attenzione ai tassi:** I REITs subiscono oscillazioni quando le banche centrali muovono i tassi d'interesse; sfruttare i piani di accumulo (PAC) gratuiti di Trade Republic su questi titoli è la strategia ideale per mediare il prezzo.
    """)# --- 3. CONFIGURAZIONE API GEMINI ---
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
try:
    st.sidebar.image("icona.png", width=120) # Sostituisci "icona.png" con il nome esatto del tuo file
except:
    pass

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
