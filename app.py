import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from google import genai
import os

# --- 1. CONFIGURAZIONE DELLA PAGINA ---
st.set_page_config(
    page_title="Edith - Piattaforma Finanziaria & IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile visivo pulito
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTIONE API KEY & GEMINI ---
st.sidebar.title("🚀 Edith Trading Hub")
st.sidebar.markdown("---")

api_key = st.sidebar.text_input("Inserisci Gemini API Key", type="password", value=st.secrets.get("GEMINI_API_KEY", ""))

client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception:
        pass

def get_gemini_response(prompt):
    if not client:
        return "⚠️ Inserisci la tua API Key di Gemini nella barra laterale per attivare l'Intelligenza Artificiale."
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Errore di connessione a Gemini: {str(e)}"

# --- 3. MENU DI NAVIGAZIONE A PIÙ SCHERMATE ---
menu = st.sidebar.radio(
    "Seleziona Schermata:",
    [
        "🏠 Home & Panoramica", 
        "🔍 Rubrica A-Z & Ricerca Universale", 
        "📈 Grafici & Analisi Tecnica", 
        "🤖 Assistente IA & Segnali"
    ]
)

# =====================================================================
# SCHERMATA 1: HOME & PANORAMICA
# =====================================================================
if menu == "🏠 Home & Panoramica":
    st.title("🏠 Home - Dashboard Finanziaria")
    st.markdown("Benvenuto nella tua applicazione di monitoraggio e analisi finanziaria assistita da IA.")
    
    st.subheader("📊 Sintesi Indici Globali")
    indici = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "FTSE MIB": "FTSEMIB.MI", "Oro": "GC=F", "Bitcoin": "BTC-USD"}
    
    cols = st.columns(len(indici))
    idx = 0
    for name, symbol in indici.items():
        with cols[idx]:
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
                st.metric(label=name, value="Errore")
        idx += 1

    st.markdown("---")
    st.info("💡 **Come procedere:** Usa il menu laterale a sinistra per passare alla **Rubrica A-Z** e cercare qualsiasi azienda al mondo per nome (es. Coca-Cola, Apple, Enel) senza bisogno di conoscere i ticker.")

# =====================================================================
# SCHERMATA 2: RUBRICA A-Z & RICERCA UNIVERSALE
# =====================================================================
elif menu == "🔍 Rubrica A-Z & Ricerca Universale":
    st.title("🔍 Rubrica A-Z & Ricerca Azienda Globale")
    st.markdown("Digita il nome di **qualsiasi azienda al mondo** (es. *Coca-Cola*, *Tesla*, *Ferrari*, *Enel*, *Apple*) nella barra sottostante:")

    query_testo = st.text_input("Cerca nome azienda o parola chiave:", value="Coca-Cola")

    if query_testo:
        with st.spinner("Ricerca globale in corso su Yahoo Finance..."):
            try:
                ricerca = yf.Search(query_testo, max_results=10)
                quotes = ricerca.quotes
                
                if not quotes:
                    st.warning("Nessuna azienda trovata con questo nome. Prova a digitare il nome in inglese o la sigla esatta.")
                else:
                    opzioni_mappate = {}
                    for q in quotes:
                        simbolo = q.get('symbol')
                        nome = q.get('shortname', q.get('longname', simbolo))
                        borsa = q.get('exchange', 'Mercato')
                        etichetta = f"{nome} ({simbolo}) - [{borsa}]"
                        opzioni_mappate[etichetta] = simbolo
                    
                    scelta_utente = st.selectbox("Seleziona il risultato corretto dalla ricerca:", list(opzioni_mappate.keys()))
                    ticker_selezionato = opzioni_mappate[scelta_utente]
                    
                    st.success(f"Ticker selezionato: **{ticker_selezionato}**")
                    
                    # Estrazione Dati Fondamentali e Storici
                    stock = yf.Ticker(ticker_selezionato)
                    info = stock.info
                    df = stock.history(period="1y")
                    
                    if not df.empty:
                        # Calcolo RSI (14)
                        delta = df['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        df['RSI'] = 100 - (100 / (1 + rs))
                        
                        prezzo_attuale = df['Close'].iloc[-1]
                        rsi_attuale = df['RSI'].iloc[-1]
                        
                        pe_ratio = info.get('trailingPE', 'N/D')
                        eps = info.get('trailingEps', 'N/D')
                        div_yield = info.get('dividendYield', None)
                        div_yield_str = f"{div_yield * 100:.2f}%" if div_yield else "N/D"
                        settore = info.get('sector', 'N/D')
                        nome_lungo = info.get('longName', ticker_selezionato)
                        
                        st.markdown("---")
                        st.subheader(f"📊 Dati Fondamentali: {nome_lungo}")
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Prezzo Attuale", f"${prezzo_attuale:,.2f}")
                        c2.metric("RSI (14)", f"{rsi_attuale:.1f}" if not np.isnan(rsi_attuale) else "N/D")
                        c3.metric("P/E (Prezzo/Utile)", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/D")
                        c4.metric("EPS (Utile per azione)", f"{eps:.2f}" if isinstance(eps, (int, float)) else "N/D")
                        
                        st.markdown(f"**Dividend Yield:** {div_yield_str} | **Settore:** {settore}")
                        
                        st.write("### Storico Prezzi (Ultimo Anno)")
                        st.line_chart(df['Close'])
                    else:
                        st.error("Impossibile scaricare i dati storici per questo titolo.")
            except Exception as e:
                st.error(f"Errore durante la ricerca: {e}")

# =====================================================================
# SCHERMATA 3: GRAFICI & ANALISI TECNICA
# =====================================================================
elif menu == "📈 Grafici & Analisi Tecnica":
    st.title("📈 Analisi Tecnica con Medie Mobili e RSI")
    
    ticker_input = st.text_input("Inserisci il Ticker esatto (es. AAPL, KO, TSLA, ENEL.MI)", value="KO").upper()
    periodo = st.selectbox("Seleziona Periodo", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    
    if ticker_input:
        try:
            stock = yf.Ticker(ticker_input)
            df = stock.history(period=periodo)
            
            if not df.empty:
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
                
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                st.subheader(f"Andamento Prezzo e Medie Mobili ({ticker_input})")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Prezzo Chiusura', line=dict(color='blue')))
                fig_price.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='orange')))
                fig_price.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], mode='lines', name='SMA 200', line=dict(color='red')))
                st.plotly_chart(fig_price, use_container_width=True)
                
                st.subheader("Indice di Forza Relativa (RSI 14)")
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Ipercomprato (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Ipervenduto (30)")
                st.plotly_chart(fig_rsi, use_container_width=True)
            else:
                st.error("Nessun dato trovato per questo ticker.")
        except Exception as e:
            st.error(f"Errore: {e}")

# =====================================================================
# SCHERMATA 4: ASSISTENTE IA & SEGNALI
# =====================================================================
elif menu == "🤖 Assistente IA & Segnali":
    st.title("🤖 Assistente IA Gemini & Analisi Operativa")
    st.markdown("Fai domande di finanza o chiedi un'analisi intelligente su un titolo.")
    
    domanda = st.text_area("Scrivi la tua richiesta o il titolo da analizzare:", value="Dammi un parere generale sull'investimento in azioni a dividendo alto.")
    
    if st.button("Chiedi a Gemini"):
        with st.spinner("L'intelligenza artificiale sta elaborando la risposta..."):
            risposta = get_gemini_response(domanda)
            st.markdown("### Risposta di Gemini:")
            st.write(risposta)
