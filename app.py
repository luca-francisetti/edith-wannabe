import streamlit as st
from PIL import Image
import os

# --- 1. CONFIGURAZIONE PAGINA (Dev'essere la PRIMA istruzione Streamlit) ---
try:
    icona = Image.open("icona.png")
except Exception:
    icona = "🤖"

st.set_page_config(
    page_title="Edith wannabe",
    page_icon=icona,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ALTRO IMPORT DELLE LIBRERIE ---
import yfinance as yf
import pandas as pd
import plotly.graph_objects as gg
from google import genai

# 3. --- BLOCCO NUOVO DA INCOLLARE QUI (PER ANDROID / SMARTPHONE) ---
try:
    with open("icona.png", "rb") as f:
        icon_b64 = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <head>
            <link rel="apple-touch-icon" href="data:image/png;base64,{icon_b64}">
            <link rel="icon" type="image/png" href="data:image/png;base64,{icon_b64}">
        </head>
        """,
        unsafe_allow_html=True
    )
except Exception:
    pass

# --- CONFIGURAZIONE PAGINA E TITOLO ---
st.set_page_config(
    page_title="Edith wannabe",
    page_icon=icona_app,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Legge la chiave dai Secret del Cloud, altrimenti usa quella locale se presente
api_key = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6LTAg9gXpzQbngglRJzpisk-1982qy_WO7RNNvp5Ta6Cg")
client = genai.Client(api_key=api_key)
# --- SIDEBAR & NAVIGAZIONE ---
st.sidebar.title("🤖 Edith wannabe")
st.sidebar.caption("L'algoritmo quantitativo avanzato con IA")

pagina = st.sidebar.radio(
    "Seleziona schermata:", 
    ["🏠 Home & Alert", "📈 Grafici & Indicatori (MACD/BB)", "🔍 Scanner Watchlist", "🤖 Analisi IA Edith"]
)

# --- 1.1 RICERCA DINAMICA DI QUALSIASI TITOLO ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Cerca Titolo")
preset_tickers = ["AAPL", "NVDA", "TSLA", "KO", "MSFT", "AMZN", "BTC-USD", "RACE.MI", "COIN"]
ticker_input = st.sidebar.text_input("Inserisci ticker libero (es. RACE.MI, BTC-USD, AMD):", value="AAPL")

ticker_selezionato = ticker_input.strip().upper() if ticker_input else "AAPL"

# --- 4. AUTO-REFRESH CONFIGURATION ---
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh (60s)")
if auto_refresh:
    time.sleep(60)
    st.rerun()

# --- FUNZIONE CALCOLO INDICATORI TECNICI CORRETTA ---
@st.cache_data(ttl=300)
def calcola_indicatori(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1y")
        if data.empty:
            return None
        
        # Rimuoviamo eventuali giornate con prezzo di chiusura mancante
        data = data.dropna(subset=['Close'])
        
        # Medie Mobili
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # RSI 14
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
        data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
        
        # Bande di Bollinger
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        data['BB_Std'] = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * 2)
        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * 2)
        
        # Eliminiamo le righe inziali/finali che contengono dati non ancora calcolati (NaN)
        data = data.dropna()
        
        return data
    except Exception:
        return None

df = calcola_indicatori(ticker_selezionato)

if df is None or df.empty:
    st.error(f"Impossibile recuperare i dati per il ticker **{ticker_selezionato}**. Verificare che il simbolo sia corretto.")
    st.stop()

ultimo = df.iloc[-1]

# --- CONTROLLO ALERT E NOTIFICHE VISIVE ---
alert_msg = []
if ultimo['RSI'] < 30:
    alert_msg.append(f"🚨 **ALERT ACCUMULO:** {ticker_selezionato} è in Ipervenduto (RSI: {ultimo['RSI']:.1f})")
elif ultimo['RSI'] > 70:
    alert_msg.append(f"⚠️ **ALERT RISCHIO:** {ticker_selezionato} è in Ipercomprato (RSI: {ultimo['RSI']:.1f})")

if ultimo['Close'] <= ultimo['BB_Lower']:
    alert_msg.append(f"💥 **ALERT VOLATILITÀ:** Prezzo sotto la Banda di Bollinger inferiore!")
elif ultimo['Close'] >= ultimo['BB_Upper']:
    alert_msg.append(f"🔥 **ALERT BREAKOUT:** Prezzo sopra la Banda di Bollinger superiore!")

# --- 1.0 SCHERMATA: HOME & ALERT ---
if pagina == "🏠 Home & Alert":
    st.title(f"🤖 Edith wannabe — Dashboard live per {ticker_selezionato}")
    
    # Mostra Toast o Banner
    for msg in alert_msg:
        st.toast(msg)
        st.warning(msg)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prezzo Attuale", f"${ultimo['Close']:.2f}")
    col2.metric("RSI (14 gg)", f"{ultimo['RSI']:.2f}", delta=f"{ultimo['RSI']-50:.1f} da Neutro")
    col3.metric("MACD Hist", f"{ultimo['MACD_Hist']:.2f}")
    col4.metric("Banda Sup / Inf", f"${ultimo['BB_Upper']:.1f} /${ultimo['BB_Lower']:.1f}")

    st.markdown("---")
    st.subheader("💡 Stato degli Indicatori")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("### 📊 Analisi Trend & Momentum")
        st.write(f"- **SMA 50 vs SMA 200:** {'🟢 RIALZISTA (Golden Cross)' if ultimo['SMA_50'] > ultimo['SMA_200'] else '🔴 RIBASSISTA (Death Cross)'}")
        st.write(f"- **MACD Crossover:** {'🟢 Segnale Rialzista' if ultimo['MACD'] > ultimo['MACD_Signal'] else '🔴 Segnale Ribassista'}")
    
    with col_b:
        st.write("### 🎯 Squeeze & Volatilità")
        larghezza_bande = ((ultimo['BB_Upper'] - ultimo['BB_Lower']) / ultimo['BB_Middle']) * 100
        st.write(f"- **Volatilità Bande BB:** {larghezza_bande:.2f}%")
        st.write(f"- **Posizione RSI:** {'🟢 Ipervenduto (Compra)' if ultimo['RSI'] < 30 else '🔴 Ipercomprato (Vendi)' if ultimo['RSI'] > 70 else '🟡 Neutro'}")

# --- 3. SCHERMATA: GRAFICI & INDICATORI (MACD / BB) ---
elif pagina == "📈 Grafici & Indicatori (MACD/BB)":
    st.title(f"📈 Analisi Tecnica Dettagliata: {ticker_selezionato}")
    
    # Grafico a 3 Subplot (Prezzo + BB, MACD, RSI)
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f"Prezzo, Medie Mobili e Bande di Bollinger ({ticker_selezionato})", "MACD & Signal", "RSI (14)")
    )

    # Subplot 1: Prezzo, SMA50/200, Bande BB
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Prezzo', line=dict(color='white', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(color='red')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Sup', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Inf', line=dict(color='gray', dash='dash'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)

    # Subplot 2: MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='cyan')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='magenta')), row=2, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Istogramma', marker_color=np.where(df['MACD_Hist'] > 0, 'green', 'red')), row=2, col=1)

    # Subplot 3: RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='yellow')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(height=800, template="plotly_dark", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# --- 2. SCHERMATA: SCANNER WATCHLIST MULTI-TITOLO ---
elif pagina == "🔍 Scanner Watchlist":
    st.title("🔍 Scanner Multi-Titolo Quantitativo")
    st.write("Scansione automatica di un paniere di titoli ordinabile per RSI e segnali operative.")

    watchlist = [
        "AAPL", "NVDA", "TSLA", "KO", "MSFT", "AMZN", "GOOGL", "META", 
        "NFLX", "AMD", "INTC", "SPY", "QQQ", "BTC-USD", "ETH-USD", 
        "RACE.MI", "ENI.MI", "UCG.MI", "COIN", "PLTR"
    ]
    
    if st.button("🚀 Avvia Scansione Live"):
        risultati = []
        progress_bar = st.progress(0)
        
        for idx, ticker in enumerate(watchlist):
            data_scan = calcola_indicatori(ticker)
            if data_scan is not None and not data_scan.empty:
                u = data_scan.iloc[-1]
                
                stato_rsi = "🟢 IPERVENDUTO" if u['RSI'] < 30 else ("🔴 IPERCOMPRATO" if u['RSI'] > 70 else "🟡 NEUTRO")
                trend = "🟢 RIALZISTA" if u['SMA_50'] > u['SMA_200'] else "🔴 RIBASSISTA"
                macd_signal = "🟢 BUY" if u['MACD'] > u['MACD_Signal'] else "🔴 SELL"
                
                risultati.append({
                    "Ticker": ticker,
                    "Prezzo ($)": round(u['Close'], 2),
                    "RSI (14)": round(u['RSI'], 2),
                    "Stato RSI": stato_rsi,
                    "Trend SMA": trend,
                    "MACD": macd_signal
                })
            progress_bar.progress((idx + 1) / len(watchlist))
        
        df_scan = pd.DataFrame(risultati).sort_values(by="RSI (14)")
        
        st.subheader("📊 Tabella Comparativa (Ordinata dal più ipervenduto al più ipercomprato)")
        st.dataframe(df_scan, use_container_width=True, height=600)

# --- ANALISI IA EDITH ---
elif pagina == "🤖 Analisi IA Edith":
    st.title(f"🤖 Assistente Strategico: Edith wannabe su {ticker_selezionato}")
    
    if client is None:
        st.error("API Key non trovata o non configurata. Inserisci la tua API Key di Gemini nel file `app.py`.")
    else:
        if st.button("✨ Genera Valutazione Quantitativa Completa"):
            with st.spinner("Edith sta elaborando gli indicatori tecnici e le Bande di Bollinger..."):
                prompt = f"""
                Sei Edith, un assistente IA ed esperto analista quantitativo di trading.
                Analizza i seguenti dati per il titolo {ticker_selezionato}:
                
                - Prezzo Attuale: ${ultimo['Close']:.2f}
                - Media Mobile 50 giorni: ${ultimo['SMA_50']:.2f}                 - Media Mobile 200 giorni:${ultimo['SMA_200']:.2f}
                - RSI (14 giorni): {ultimo['RSI']:.2f}
                - Valore MACD: {ultimo['MACD']:.3f} (Signal: {ultimo['MACD_Signal']:.3f})
                - Bande di Bollinger: Inf=${ultimo['BB_Lower']:.2f}, Sup=${ultimo['BB_Upper']:.2f}
                
                Fornisci:
                1. VERDETTO CHIARO: (ACQUISTA / VENDI / ATTENDI)
                2. MOTIVAZIONE TECNICA: Combinando RSI, MACD e Bande di Bollinger.
                3. LIVELLI CHIAVE: Supporti e resistenze da monitorare.
                """
                
                for modello in ["gemini-3.5-flash-lite", "gemini-3.6-flash"]:
                    try:
                        res = client.models.generate_content(model=modello, contents=prompt)
                        st.success(f"Analisi completata con successo ({modello}):")
                        st.markdown(res.text)
                        break
                    except Exception as e:
                        st.error(f"Errore con {modello}: {e}")
