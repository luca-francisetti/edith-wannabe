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

# --- 2. GESTIONE API KEY & GEMINI CON FALLBACK AUTOMATICO ---
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
    
    models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
    
    last_error = ""
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"⚠️ I server di Google sono temporaneamente sovraccarichi (Errore 503). Riprova tra qualche istante. Dettaglio: {last_error}"

# --- 3. MENU DI NAVIGAZIONE A PIÙ SCHERMATE ---
menu = st.sidebar.radio(
    "Seleziona Schermata:",
    [
        "🏠 Home & Panoramica", 
        "🔍 Rubrica A-Z & Ricerca Universale", 
        "📈 Grafici & Analisi Tecnica", 
        "💰 Cantiere Dividendi & Tasse",
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
    st.info("💡 **Come procedere:** Usa il menu laterale a sinistra per esplorare la Rubrica, l'Analisi Tecnica, il **Cantiere Dividendi** o l'Assistente IA.")

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
                    
                    stock = yf.Ticker(ticker_selezionato)
                    info = stock.info
                    df = stock.history(period="1y")
                    
                    if not df.empty:
                        delta = df['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        df['RSI'] = 100 - (100 / (1 + rs))
                        
                        prezzo_attuale = df['Close'].iloc[-1]
                        rsi_attuale = df['RSI'].iloc[-1]
                        
                        pe_ratio = info.get('trailingPE', 'N/D')
                        eps = info.get('trailingEps', 'N/D')
                        
                        div_raw = info.get('dividendYield', 0)
                        div_yield_val = (div_raw * 100) if (div_raw and div_raw <= 0.5) else (div_raw if div_raw else 0.0)
                        div_yield_str = f"{div_yield_val:.2f}%" if div_yield_val > 0 else "N/D"
                        
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
# SCHERMATA 4: CANTIERE DIVIDENDI & TASSE (TRADE REPUBLIC)
# =====================================================================
elif menu == "💰 Cantiere Dividendi & Tasse":
    st.title("💰 Cantiere Dividendi & Motore Fiscale (Trade Republic)")
    st.markdown("Calcola al centesimo il rendimento netto dei dividendi considerando commissioni, ritenuta estera (es. W-8BEN USA al 15%) e tassazione italiana del 26% in regime amministrato.")

    tab1, tab2 = st.tabs(["🧮 Calcolatore Singolo Investimento", "🏆 Classifica Top 10 Dividendi & Trappole IA"])

    with tab1:
        st.subheader("Simulatore Rendimento Netto su Capitale Investito")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            capitale = st.number_input("Capitale Investito (€)", min_value=10.0, value=100.0, step=10.0)
            yield_input = st.number_input("Dividend Yield Annuo (%)", min_value=0.0, max_value=30.0, value=3.5, step=0.1)
        with col_c2:
            commissione_tr = st.number_input("Commissione Trade Republic per operazione (€)", min_value=0.0, value=1.0, step=0.5)
            ritenuta_estera_pct = st.selectbox("Ritenuta alla fonte estera (es. W-8BEN per USA)", [15.0, 0.0, 25.0, 30.0], index=0)

        dividendo_lordo = capitale * (yield_input / 100.0)
        base_netta_lorda = max(0.0, dividendo_lordo)
        
        tassa_estera = base_netta_lorda * (ritenuta_estera_pct / 100.0)
        tassa_totale_dovuta = base_netta_lorda * 0.26
        tassa_italia_aggiuntiva = max(0.0, tassa_totale_dovuta - tassa_estera)
        
        dividendo_netto_annuo = base_netta_lorda - tassa_estera - tassa_italia_aggiuntiva - commissione_tr
        dividendo_netto_mensile = max(0.0, dividendo_netto_annuo / 12.0)

        st.markdown("---")
        res1, res2, res3, res4 = st.columns(4)
        res1.metric("Dividendo Lordo Annuo", f"€ {dividendo_lordo:.2f}")
        res2.metric("Commissione TR (Una tantum)", f"€ {commissione_tr:.2f}")
        res3.metric("Tasse (Estera + ITA)", f"€ {tassa_estera + tassa_italia_aggiuntiva:.2f}")
        res4.metric("Netto Mensile Reale", f"€ {dividendo_netto_mensile:.2f}", delta="al mese")

        st.info("ℹ️ **Nota Fiscale Trade Republic (Regime Amministrato):** Trade Republic agisce come sostituto d'imposta calcolando e versando automaticamente le ritenute e le imposte in Italia.")

    with tab2:
        st.subheader("🏆 Classifica Top 10 Regine dei Dividendi & Controllo 'Dividend Trap'")
        st.markdown("Analisi automatica sui titoli storici a maggiore distribuzione (inclusi i mensili come Realty Income, Main Street Capital e STAG Industrial). I valori mostrano il **Netto Mensile** effettivo su un investimento di **100€**.")

        top_div_tickers = ["O", "MAIN", "STAG", "KO", "JNJ", "MO", "PEP", "ABBV", "ENEL.MI", "BHP"]
        
        dati_dividendi = []
        for t in top_div_tickers:
            try:
                tk = yf.Ticker(t)
                inf = tk.info
                nome = inf.get('longName', t)
                prezzo = inf.get('currentPrice', inf.get('regularMarketPrice', 0))
                
                div_raw = inf.get('dividendYield', 0)
                div_yield = (div_raw * 100) if (div_raw and div_raw <= 0.5) else (div_raw if div_raw else 0.0)
                
                # Calcolo Netto Mensile su 100€
                lordo_100_annuo = 100.0 * (div_yield / 100.0)
                tassa_est = lordo_100_annuo * 0.15 
                tassa_ita = max(0.0, (lordo_100_annuo * 0.26) - tassa_est)
                netto_annuo = lordo_100_annuo - tassa_est - tassa_ita
                netto_mensile = max(0.0, netto_annuo / 12.0)
                
                dati_dividendi.append({
                    "Ticker": t,
                    "Nome": nome,
                    "Prezzo ($/€)": prezzo,
                    "Dividend Yield (%)": round(div_yield, 2),
                    "Netto Mensile su 100€ (€)": round(netto_mensile, 2)
                })
            except Exception:
                pass

        if dati_dividendi:
            df_div = pd.DataFrame(dati_dividendi)
            st.dataframe(df_div, use_container_width=True)

        st.markdown("---")
        st.subheader("🤖 Analisi IA 'Dividend Trap' (Trappola da Dividendo)")
        st.markdown("Se un'azienda offre un dividendo superiore all'8-10%, spesso nasconde problemi di bilancio o un crollo del titolo. Chiedi a Gemini di verificare un titolo specifico:")
        
        titolo_da_verificare = st.text_input("Inserisci Ticker da analizzare per il rischio trappola:", value="MO")
        if st.button("Esegui Controllo Trappola Dividendo"):
            with st.spinner("L'intelligenza artificiale sta esaminando la sostenibilità del dividendo..."):
                prompt = f"""
                Analizza il titolo azionario {titolo_da_verificare} dal punto di vista della sostenibilità del suo dividendo. 
                Verifica se il dividend yield elevato rappresenta una 'trappola da dividendo' (dividend trap) dovuta a crollo del business, debito eccessivo o payout ratio insostenibile, oppure se è un dividendo sicuro e solido. 
                Fornisci un verdetto chiaro e motivato.
                """
                parere_ia = get_gemini_response(prompt)
                st.markdown("### Verdetto IA sulla sostenibilità:")
                st.write(parere_ia)

# =====================================================================
# SCHERMATA 5: ASSISTENTE IA & SEGNALI
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
            st.write(risposta)
