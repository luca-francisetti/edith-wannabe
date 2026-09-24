import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
from google import genai

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Edith Finanza & Trading Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile CSS personalizzato
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("🚀 Edith Trading & Finance")
st.sidebar.markdown("---")

# Gestione API Key Gemini
api_key = st.sidebar.text_input("Inserisci Gemini API Key", type="password", value=st.secrets.get("GEMINI_API_KEY", ""))

menu = st.sidebar.radio(
    "Navigazione",
    ["📊 Panoramica & Mercati", "📈 Analisi Tecnica", "🔍 Scanner & Rubrica A-Z", "⚡ Sala Trading & Segnali", "💰 Dividendi & Tasse", "🏠 Immobiliare & REITs", "🤖 Assistente AI Gemini"]
)

# Funzione per interrogare Gemini con il nuovo SDK google-genai
def get_gemini_response(prompt):
    if not api_key:
        return "⚠️ Inserisci la tua API Key di Gemini nella barra laterale per attivare l'Intelligenza Artificiale."
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Errore di connessione a Gemini: {str(e)}"

# Sezione 1: Panoramica & Mercati
if menu == "📊 Panoramica & Mercati":
    st.title("📊 Panoramica dei Mercati Globali")
    st.markdown("Monitoraggio in tempo reale dei principali indici azionari e asset mondiali.")
    
    tickers = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "FTSE MIB": "FTSEMIB.MI", "DAX": "^GDAXI", "Oro": "GC=F", "Bitcoin": "BTC-USD"}
    
    cols = st.columns(3)
    idx = 0
    for name, symbol in tickers.items():
        with cols[idx % 3]:
            try:
                data = yf.Ticker(symbol).history(period="5d")
                if not data.empty:
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    st.metric(label=name, value=f"{current:,.2f}", delta=f"{change:+.2f}%")
                else:
                    st.metric(label=name, value="N/D")
            except Exception:
                st.metric(label=name, value="Errore dati")
        idx += 1
        
    st.markdown("---")
    st.subheader("💡 Commento di Mercato AI")
    if st.button("Genera Analisi Rapida di Mercato"):
        with st.spinner("Analisi in corso con Gemini..."):
            prompt = "Fai un'analisi macroeconomica rapida e professionale dei mercati finanziari globali attuali."
            analysis = get_gemini_response(prompt)
            st.info(analysis)

# Sezione 2: Analisi Tecnica
elif menu == "📈 Analisi Tecnica":
    st.title("📈 Analisi Tecnica Avanzata")
    
    ticker_input = st.text_input("Inserisci il Ticker Yahoo Finance (es. AAPL, TSLA, ENEL.MI, BTC-USD)", value="AAPL").upper()
    period = st.selectbox("Periodo temporale", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    
    if ticker_input:
        try:
            stock = yf.Ticker(ticker_input)
            df = stock.history(period=period)
            
            if df.empty:
                st.error("Nessun dato trovato per questo ticker.")
            else:
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
                
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                st.subheader(f"Grafico Prezzo & Medie Mobili ({ticker_input})")
                st.line_chart(df[['Close', 'SMA_50', 'SMA_200']])
                
                st.subheader("Indice di Forza Relativa (RSI 14)")
                st.line_chart(df['RSI'])
                
                latest_rsi = df['RSI'].iloc[-1]
                st.metric("RSI Attuale", f"{latest_rsi:.2f}", "Ipervenduto < 30 | Ipercomprato > 70" if not np.isnan(latest_rsi) else "")
        except Exception as e:
            st.error(f"Errore nel recupero dei dati: {e}")

# Sezione 3: Scanner & Rubrica A-Z
elif menu == "🔍 Scanner & Rubrica A-Z":
    st.title("🔍 Scanner Titoli & Rubrica A-Z")
    st.markdown("Esplora e filtra un elenco di azioni popolari con metriche chiave.")
    
    default_watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "ENEL.MI", "ISP.MI", "UCG.MI", "BTC-USD"]
    selected_stock = st.selectbox("Seleziona dalla Rubrica:", default_watchlist)
    
    if selected_stock:
        t = yf.Ticker(selected_stock)
        info = t.info
        st.write(f"### {info.get('longName', selected_stock)} ({selected_stock})")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Prezzo Attuale", f"{info.get('currentPrice', info.get('regularMarketPrice', 'N/D'))}")
        col2.metric("Capitalizzazione", f"{info.get('marketCap', 'N/D'):,}" if isinstance(info.get('marketCap'), (int, float)) else "N/D")
        col3.metric("Settore", f"{info.get('sector', 'N/D')}")
        
        st.write("Descrizione:")
        st.write(info.get('longBusinessSummary', 'Nessuna descrizione disponibile.'))

# Sezione 4: Sala Trading & Segnali
elif menu == "⚡ Sala Trading & Segnali":
    st.title("⚡ Sala Trading & Segnali Operativi")
    st.markdown("Generazione di segnali di trading basati su indicatori quantitativi e validazione AI.")
    
    trade_ticker = st.text_input("Ticker per Segnale di Trading", value="TSLA").upper()
    if st.button("Genera Segnale di Trading"):
        with st.spinner("Elaborazione indicatori e segnale AI..."):
            try:
                df = yf.Ticker(trade_ticker).history(period="6mo")
                close = df['Close'].iloc[-1]
                sma50 = df['Close'].rolling(50).mean().iloc[-1]
                sma200 = df['Close'].rolling(200).mean().iloc[-1]
                
                prompt = f"Analizza il titolo {trade_ticker} con prezzo attuale {close}, SMA 50 a {sma50}, e SMA 200 a {sma200}. Fornisci un segnale chiaro (BUY, SELL, HOLD) con motivazione tecnica."
                signal_analysis = get_gemini_response(prompt)
                
                st.success("Analisi completata!")
                st.write(signal_analysis)
            except Exception as e:
                st.error(f"Errore: {e}")

# Sezione 5: Dividendi & Tasse
elif menu == "💰 Dividendi & Tasse":
    st.title("💰 Calcolatore Dividendi & Tasse")
    st.markdown("Calcola il rendimento netto dei dividendi considerando la tassazione sulle rendite finanziarie (es. aliquota 26%).")
    
    capital = st.number_input("Capitale Investito (€)", value=10000.0, step=1000.0)
    div_yield = st.slider("Dividend Yield annuo (%)", min_value=0.0, max_value=15.0, value=4.5, step=0.1)
    tax_rate = st.slider("Aliquota Fiscale / Tasse (%)", min_value=0.0, max_value=50.0, value=26.0, step=0.5)
    
    annual_gross = capital * (div_yield / 100)
    tax_amount = annual_gross * (tax_rate / 100)
    annual_net = annual_gross - tax_amount
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Dividendo Lordo Annuo", f"€ {annual_gross:,.2f}")
    col2.metric("Tasse Trattenute", f"€ {tax_amount:,.2f}")
    col3.metric("Dividendo Netto Annuo", f"€ {annual_net:,.2f}")

# Sezione 6: Immobiliare & REITs
elif menu == "🏠 Immobiliare & REITs":
    st.title("🏠 Immobiliare & REITs Globali")
    st.markdown("Analisi dei principali fondi di investimento immobiliare (REITs) come Realty Income (O), Simon Property Group (SPG), ecc.")
    
    reit_ticker = st.selectbox("Seleziona REIT", ["O", "SPG", "PLD", "VICI"])
    reit_data = yf.Ticker(reit_ticker)
    info = reit_data.info
    
    st.write(f"### {info.get('longName', reit_ticker)}")
    st.metric("Prezzo", f"{info.get('currentPrice', 'N/D')}")
    st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/D")
    st.write(info.get('longBusinessSummary', ''))

# Sezione 7: Assistente AI Gemini
elif menu == "🤖 Assistente AI Gemini":
    st.title("🤖 Chat Assistente Finanziario IA")
    st.markdown("Fai qualsiasi domanda di finanza, mercati, strategie o analisi di bilancio a Gemini.")
    
    user_query = st.text_area("Scrivi la tua domanda qui:", placeholder="Es. Quali sono le differenze tra ETF a capitalizzazione e a distribuzione?")
    if st.button("Invia Domanda"):
        if user_query:
            with st.spinner("Gemini sta elaborando la risposta..."):
                answer = get_gemini_response(user_query)
                st.write("### Risposta:")
                st.write(answer)
        else:
            st.warning("Inserisci una domanda prima di inviare.")
