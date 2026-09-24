import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from google import genai
from datetime import datetime
from zoneinfo import ZoneInfo
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
    
    models_to_try = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.8-flash"]
    
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
        "🏢 Immobili & REITs Mensili",
        "🚨 Sala Segnali (Day Trading)",
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
    st.info("💡 **Come procedere:** Usa il menu laterale a sinistra per esplorare la Rubrica, l'Analisi Tecnica, il **Cantiere Dividendi**, i **REITs Immobiliari** o la **Sala Segnali**.")

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

    tab1, tab2, tab3 = st.tabs([
        "🧮 Calcolatore Singolo Investimento", 
        "🏆 Classifica Top 10 Dividendi & Trappole IA",
        "🔥 Top 10 Alto Yield & Rischio"
    ])

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
        st.markdown("Analisi automatica sui titoli storici a maggiore distribuzione. I valori mostrano il **Netto Mensile** effettivo su un investimento di **100€**.")

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
        st.subheader("🤖 Analisi IA 'Dividend Trap'")
        titolo_da_verificare = st.text_input("Inserisci Ticker da analizzare per il rischio trappola:", value="MO")
        if st.button("Esegui Controllo Trappola Dividendo"):
            with st.spinner("L'intelligenza artificiale sta esaminando la sostenibilità del dividendo..."):
                prompt = f"""
                Analizza il titolo azionario {titolo_da_verificare} dal punto di vista della sostenibilità del suo dividendo. 
                Verifica se il dividend yield elevato rappresenta una 'trappola da dividendo' (dividend trap) dovuta a crollo del business o debito eccessivo, oppure se è un dividendo sicuro. 
                Fornisci un verdetto chiaro e motivato.
                """
                parere_ia = get_gemini_response(prompt)
                st.markdown("### Verdetto IA sulla sostenibilità:")
                st.write(parere_ia)

    with tab3:
        st.subheader("🔥 Top 10 Alto Yield & Rischio (Potenziali Dividend Traps)")
        high_yield_tickers = ["PBR", "ENI.MI", "BTI", "AGNC", "NLY", "VOD", "VZ", "T", "PFE", "LEG"]
        
        dati_high_yield = []
        for t in high_yield_tickers:
            try:
                tk = yf.Ticker(t)
                inf = tk.info
                nome = inf.get('longName', t)
                prezzo = inf.get('currentPrice', inf.get('regularMarketPrice', 0))
                
                div_raw = inf.get('dividendYield', 0)
                div_yield = (div_raw * 100) if (div_raw and div_raw <= 0.5) else (div_raw if div_raw else 0.0)
                
                lordo_100_annuo = 100.0 * (div_yield / 100.0)
                tassa_est = lordo_100_annuo * 0.15 
                tassa_ita = max(0.0, (lordo_100_annuo * 0.26) - tassa_est)
                netto_annuo = lordo_100_annuo - tassa_est - tassa_ita
                netto_mensile = max(0.0, netto_annuo / 12.0)
                
                dati_high_yield.append({
                    "Ticker": t,
                    "Nome": nome,
                    "Prezzo ($/€)": prezzo,
                    "Dividend Yield (%)": round(div_yield, 2),
                    "Netto Mensile su 100€ (€)": round(netto_mensile, 2)
                })
            except Exception:
                pass

        if dati_high_yield:
            df_hy = pd.DataFrame(dati_high_yield)
            df_hy = df_hy.sort_values(by="Dividend Yield (%)", ascending=False)
            st.dataframe(df_hy, use_container_width=True)

# =====================================================================
# SCHERMATA 5: IMMOBILI & REITs MENSILI
# =====================================================================
elif menu == "🏢 Immobili & REITs Mensili":
    st.title("🏢 Immobili & Frazionamento (REITs)")
    st.markdown("""
    Per investire in immobili e ottenere rendite passive con percentuali minime di edifici senza sborsare centinaia di migliaia d'euro, sfrutteremo i **REIT (Real Estate Investment Trusts)**.
    
    Sono società immobiliari quotate in borsa (acquistabili comodamente su **Trade Republic** a partire da pochi euro) che per legge devono distribuire quasi tutti gli affitti percepiti sotto forma di dividendi mensili o trimestrali.
    """)
    
    st.markdown("---")
    st.subheader("🏙️ Immobili & REITs Mensili: I 10 Migliori Globali su Trade Republic")
    st.markdown("Una sezione dedicata ai 10 migliori REITs globali presenti su Trade Republic che pagano dividendi con stima precisa di quanto ti tornerà in tasca ogni singolo mese su **100€** e, in evidenza nella colonna a destra, su **10€** (perché parti dal basso).")

    reits_mensili_data = [
        {"ticker": "O", "nome": "Realty Income Corp.", "settore": "Retail / Commerciale", "yield": 5.3},
        {"ticker": "STAG", "nome": "STAG Industrial Inc.", "settore": "Logistica & Magazzini", "yield": 4.1},
        {"ticker": "LTC", "nome": "LTC Properties Inc.", "settore": "Sanitario / Senior Housing", "yield": 6.2},
        {"ticker": "EPR", "nome": "EPR Properties", "settore": "Intrattenimento & Esperienziale", "yield": 6.5},
        {"ticker": "GOOD", "nome": "Gladstone Commercial", "settore": "Uffici & Industriale", "yield": 8.0},
        {"ticker": "ADC", "nome": "Agree Realty Corp.", "settore": "Retail / Negozi", "yield": 4.4},
        {"ticker": "LAND", "nome": "Gladstone Land Corp.", "settore": "Terreni Agricoli (Farmland)", "yield": 4.8},
        {"ticker": "AGNC", "nome": "AGNC Investment Corp.", "settore": "Mortgage REITs / Mutui", "yield": 14.0},
        {"ticker": "NLY", "nome": "Annaly Capital Management", "settore": "Mortgage REITs / Finanziario", "yield": 13.5},
        {"ticker": "PSEC", "nome": "Prospect Capital Corp.", "settore": "Finanziario / Immobili", "yield": 11.0}
    ]

    tabella_reit_output = []
    for r in reits_mensili_data:
        y = r["yield"]
        
        # Calcolo su 100€
        lordo_100 = 100.0 * (y / 100.0)
        t_est_100 = lordo_100 * 0.15
        t_ita_100 = max(0.0, (lordo_100 * 0.26) - t_est_100)
        netto_mensile_100 = max(0.0, (lordo_100 - t_est_100 - t_ita_100) / 12.0)
        
        # Calcolo su 10€ (Partendo dal basso)
        lordo_10 = 10.0 * (y / 100.0)
        t_est_10 = lordo_10 * 0.15
        t_ita_10 = max(0.0, (lordo_10 * 0.26) - t_est_10)
        netto_mensile_10 = max(0.0, (lordo_10 - t_est_10 - t_ita_10) / 12.0)
        
        tabella_reit_output.append({
            "Ticker": r["ticker"],
            "Società": r["nome"],
            "Settore": r["settore"],
            "Yield (%)": f"{y:.2f}%",
            "Netto Mensile (su 100€)": f"€ {netto_mensile_100:.4f}",
            "🟢 Netto Mensile (su 10€)": f"€ {netto_mensile_10:.4f}"
        })

    df_reit_view = pd.DataFrame(tabella_reit_output)
    st.dataframe(df_reit_view, use_container_width=True)

    st.markdown("---")
    st.subheader("🧮 Calcolatore Rendita Passiva Metri Quadri Frazionati")
    
    col_sim_r1, col_sim_r2 = st.columns(2)
    with col_sim_r1:
        capitale_reit = st.number_input("Capitale Investito in REITs (€)", min_value=10.0, value=150.0, step=10.0)
    with col_sim_r2:
        yield_reit_scelto = st.slider("Dividend Yield medio atteso (%)", min_value=3.0, max_value=15.0, value=5.5, step=0.1)
        
    lordo_reit_annuo = capitale_reit * (yield_reit_scelto / 100.0)
    tass_est_reit = lordo_reit_annuo * 0.15
    tass_ita_reit = max(0.0, (lordo_reit_annuo * 0.26) - tass_est_reit)
    netto_annuo_reit = lordo_reit_annuo - tass_est_reit - tass_ita_reit
    netto_mensile_reit = netto_annuo_reit / 12.0

    cr1, cr2, cr3 = st.columns(3)
    cr1.metric("Rendita Lorda Annua", f"€ {lordo_reit_annuo:.2f}")
    cr2.metric("Rendita Netta Annua", f"€ {netto_annuo_reit:.2f}")
    cr3.metric("Rendita Netta Mensile", f"€ {netto_mensile_reit:.2f}", delta="al mese")

    st.info(f"💡 **Suggerimento Operativo:** Con soli **€ {capitale_reit:,.2f}** investiti in REITs, possiedi una piccola frazione di centinaia di immobili commerciali e logistici nel mondo, ricevendo ogni mese circa **€ {netto_mensile_reit:.2f}** netti sul tuo conto Trade Republic.")

# =====================================================================
# SCHERMATA 6: SALA SEGNALI (DAY TRADING - SOLO LONG)
# =====================================================================
elif menu == "🚨 Sala Segnali (Day Trading)":
    st.title("🚨 Sala Segnali - Day Trading (Ottimizzato per Trade Republic - Solo Long)")
    
    # 1. Doppio Orologio (Milano / New York) con logica oraria richiesta
    now_milano = datetime.now(ZoneInfo("Europe/Rome"))
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    
    min_milano = now_milano.hour * 60 + now_milano.minute
    
    # Milano: Verde 09:05-10:00 (545-600 min), Rosso 11:30-14:30 (690-870 min)
    if 545 <= min_milano <= 600:
        color_milano = "#4ade80"  # Verde
    elif 690 <= min_milano <= 870:
        color_milano = "#ef4444"  # Rosso
    else:
        color_milano = "white"

    # New York (su orario italiano): Verde 15:30-16:30 (930-990 min), Rosso 21:00-22:00 (1260-1320 min)
    if 930 <= min_milano <= 990:
        color_ny = "#4ade80"  # Verde
    elif 1260 <= min_milano <= 1320:
        color_ny = "#ef4444"  # Rosso
    else:
        color_ny = "white"
    
    col_cl1, col_cl2 = st.columns(2)
    with col_cl1:
        st.markdown(f"""
            <div style="background-color: #1e3a8a; color: white; padding: 10px; border-radius: 8px; text-align: center; font-family: sans-serif;">
                <b>📍 MILANO (Borsa Italiana)</b><br>
                <span style="font-size: 1.3em; font-weight: bold; color: {color_milano};">{now_milano.strftime('%H:%M:%S')}</span>
            </div>
        """, unsafe_allow_html=True)
    with col_cl2:
        st.markdown(f"""
            <div style="background-color: #1e3a8a; color: white; padding: 10px; border-radius: 8px; text-align: center; font-family: sans-serif;">
                <b>🗽 NEW YORK (Wall Street)</b><br>
                <span style="font-size: 1.3em; font-weight: bold; color: {color_ny};">{now_ny.strftime('%H:%M:%S')}</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Disclaimer Commissioni TR Compatto
    st.markdown("""
        <div style="background-color: #111827; padding: 10px 15px; border-radius: 8px; border: 1px solid #374151; font-size: 0.9em; color: #9ca3af;">
            💡 <b>Nota Commissioni TR:</b> 1€ acquisto + 1€ vendita (Totale 2€ fissi). I micro-investimenti (es. 10€) subiscono un forte impatto commissionale; si consigliano capitali da 200€–400€ per ottimizzare il margine.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("⚡ Top 5 Segnali Long (Analisi Quantitativa in Tempo Reale)")

    if st.button("🚀 Avvia Scansione e Calcola Top 5 Long", type="primary"):
        with st.spinner("Scansione mercati e calcolo indicatori in corso..."):
            paniere_day = [
                ("TSLA", "Tesla Inc."),
                ("AAPL", "Apple Inc."),
                ("NVDA", "NVIDIA Corp."),
                ("MSFT", "Microsoft Corp."),
                ("AMZN", "Amazon.com Inc."),
                ("AMD", "Advanced Micro Devices"),
                ("ENEL.MI", "Enel S.p.A."),
                ("UCG.MI", "UniCredit S.p.A."),
                ("RACE.MI", "Ferrari N.V.")
            ]
            
            risultati_analisi = []
            for ticker, nome_compagnia in paniere_day:
                try:
                    tk = yf.Ticker(ticker)
                    df = tk.history(period="1d", interval="5m")
                    if not df.empty and len(df) > 3:
                        p_attuale = df['Close'].iloc[-1]
                        p_apertura = df['Open'].iloc[0]
                        var_pct = ((p_attuale - p_apertura) / p_apertura) * 100
                        vol_medio = df['Volume'].mean()
                        vol_ultimo = df['Volume'].iloc[-1]
                        
                        score = var_pct + (2.0 if vol_ultimo > vol_medio * 1.2 else 0.0)
                        
                        risultati_analisi.append({
                            "ticker": ticker,
                            "nome": nome_compagnia,
                            "prezzo": p_attuale,
                            "var": var_pct,
                            "score": score
                        })
                except Exception:
                    pass
            
            risultati_analisi = sorted(risultati_analisi, key=lambda x: x['score'], reverse=True)[:5]
            
            if not risultati_analisi:
                st.warning("Non è stato possibile recuperare i dati in tempo reale in questo momento.")
            else:
                for idx, item in enumerate(risultati_analisi, 1):
                    p_curr = item['prezzo']
                    target_pct = 1.00 
                    p_target = p_curr * (1 + target_pct / 100.0)
                    
                    cap_10 = 10.0
                    lordo_10 = cap_10 * (target_pct / 100.0)
                    netto_10 = lordo_10 - 2.0 
                    
                    cap_consigliato = 200.0 if p_curr < 200 else 400.0
                    lordo_cons = cap_consigliato * (target_pct / 100.0)
                    netto_cons = lordo_cons - 2.0
                    
                    with st.container():
                        st.markdown(f"### #{idx} — {item['nome']} (`{item['ticker']}`)")
                        col_main, col_mini = st.columns([2, 1])
                        
                        with col_main:
                            st.markdown(f"""
                            - **Prezzo Attuale:** € {p_curr:,.2f}  
                            - **Variazione Intraday:** `{item['var']:+.2f}%`  
                            - **Target di Rialzo:** `+{target_pct:.2f}%`  
                            - **Prezzo di Vendita (Target):** **€ {p_target:,.2f}**  
                            - **Capitale Consigliato:** `€ {cap_consigliato:,.0f}` (Utile lordo stimato: € {lordo_cons:.2f} | Netto: € {netto_cons:.2f})  
                            - **Timeframe:** 25–40 minuti | **Strategia:** Long intraday momentum.
                            """)
                        
                        with col_mini:
                            st.markdown(f"""
                            <div style="background-color: #1e3a8a; color: white; padding: 12px; border-radius: 8px; border: 1px solid #3b82f6; font-size: 0.9em;">
                                <div style="font-weight: bold; margin-bottom: 6px; color: #93c5fd;">💎 Micro-Investimento (10€)</div>
                                • Capitale: <b>€ 10,00</b><br>
                                • Target Vendita: <b>€ {p_target:,.2f}</b><br>
                                • Lordo: € {lordo_10:.2f}<br>
                                • Commissioni TR: € 2,00<br>
                                <hr style="margin: 6px 0; border-color: #3b82f6;">
                                • Netto: <b style="color: {"#f87171" if netto_10 < 0 else "#4ade80"};">€ {netto_10:.2f}</b>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.markdown("---")
    else:
        st.info("👆 Clicca sul pulsante sopra per avviare la scansione dei mercati e visualizzare i segnali.")

# =====================================================================
# SCHERMATA 7: ASSISTENTE IA & SEGNALI
# =====================================================================
elif menu == "🤖 Assistente IA & Segnali":
    st.title("🤖 Assistente IA Gemini & Analisi Operativa")
    st.markdown("Fai domande di finanza o chiedi un'analisi intelligente su un titolo.")
    
    domanda = st.text_area("Scrivi la tua richiesta o il titolo da analizzare:", value="Dammi un parere sui REITs immobiliari e come inserirli in un piano d'accumulo a piccolo budget.")
    
    if st.button("Chiedi a Gemini"):
        with st.spinner("L'intelligenza artificiale sta elaborando la risposta..."):
            risposta = get_gemini_response(domanda)
            st.markdown("### Risposta di Gemini:")
            st.write(risposta)
