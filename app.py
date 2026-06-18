import html
import uuid

import requests
import streamlit as st

RASA_URL = "http://localhost:5005/webhooks/rest/webhook"
APP_VERSION = "KRUIDVAT_POLISHED_LOOM_UI_V6_RESET_FIX_2026_06_12"

st.set_page_config(
    page_title="Kruidvat Klantenservice",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def initial_messages():
    return [
        {
            "role": "assistant",
            "content": (
                "Hoi! Ik ben Kruidvat Klantenservice. Ik kan helpen met webshopbestellingen, ontbrekende of beschadigde artikelen, "
                "retouren, terugbetalingen, bezorgproblemen en orderstatus. Waarmee kan ik je helpen?"
            ),
        }
    ]


def new_sender_id() -> str:
    """Create a fresh Rasa sender ID so Chat resetten also resets the Rasa tracker."""
    return f"kruidvat-klantenservice-{uuid.uuid4().hex[:8]}"


def send_to_rasa(message: str) -> list[str]:
    payload = {"sender": st.session_state.sender_id, "message": message}

    try:
        response = requests.post(RASA_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError:
        return [
            'Ik kan de lokale Rasa-server niet bereiken. Start Rasa eerst met: rasa run --enable-api --cors "*"'
        ]
    except requests.exceptions.Timeout:
        return ["De Rasa-server reageerde te langzaam. Probeer het opnieuw."]
    except requests.exceptions.RequestException as exc:
        return [f"Er ging iets mis bij het verbinden met Rasa: {exc}"]

    bot_messages = [item.get("text") for item in data if item.get("text")]
    return bot_messages or ["Ik heb geen antwoord ontvangen van de Rasa-server."]


def add_user_message(message: str):
    st.session_state.messages.append({"role": "user", "content": message})
    for response in send_to_rasa(message):
        st.session_state.messages.append({"role": "assistant", "content": response})


if "messages" not in st.session_state:
    st.session_state.messages = initial_messages()

if "sender_id" not in st.session_state:
    st.session_state.sender_id = new_sender_id()


st.markdown(
    """
    <style>
        :root {
            --kv-red: #d71920;
            --kv-red-dark: #b81218;
            --kv-yellow: #ffe500;
            --kv-yellow-soft: #fff8c9;
            --kv-green: #008a2e;
            --kv-green-dark: #006f25;
            --kv-text: #222222;
            --kv-muted: #666666;
            --kv-line: #ececec;
            --kv-soft: #f7f7f7;
            --kv-shadow: 0 18px 44px rgba(20, 20, 20, 0.10);
            --kv-chat-shadow: 0 20px 45px rgba(0, 0, 0, 0.14);
        }

        .stApp {
            background: #ffffff;
            color: var(--kv-text);
        }

        .block-container {
            max-width: 100%;
            padding: 0 !important;
        }

        #MainMenu, footer, header[data-testid="stHeader"] {
            visibility: hidden;
            height: 0;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        .kv-page {
            min-height: 100vh;
            background: #ffffff;
            font-family: Arial, Helvetica, sans-serif;
        }

        .kv-top-strip {
            height: 34px;
            background: var(--kv-red);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.4rem;
            font-size: 0.88rem;
            font-weight: 800;
            letter-spacing: -0.01rem;
        }

        .kv-nav {
            height: 82px;
            border-bottom: 1px solid #eeeeee;
            box-shadow: 0 2px 9px rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            gap: 1.4rem;
            padding: 0 4.4rem;
            background: #ffffff;
            box-sizing: border-box;
        }

        .kv-logo {
            width: 102px;
            height: 56px;
            background: var(--kv-red);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 1000;
            font-size: 1.08rem;
            border-radius: 4px;
            box-shadow: inset 0 -4px 0 rgba(0,0,0,0.08);
            flex: 0 0 auto;
        }

        .hamburger {
            width: 28px;
            height: 22px;
            flex: 0 0 auto;
        }

        .hamburger span {
            display: block;
            height: 3px;
            background: #252525;
            border-radius: 10px;
            margin-bottom: 6px;
        }

        .cat-label {
            font-size: 1.02rem;
            font-weight: 900;
            color: #333333;
            white-space: nowrap;
        }

        .top-search {
            flex: 1;
            max-width: 760px;
            height: 52px;
            border-radius: 999px;
            background: #eeeeee;
            color: #707070;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.35rem 0 1.65rem;
            font-size: 1rem;
            box-sizing: border-box;
            margin-left: 1rem;
        }

        .search-icon {
            width: 19px;
            height: 19px;
            border: 3px solid #242424;
            border-radius: 50%;
            display: inline-block;
            position: relative;
            flex: 0 0 auto;
        }

        .search-icon:after {
            content: "";
            position: absolute;
            width: 10px;
            height: 3px;
            background: #242424;
            transform: rotate(45deg);
            right: -8px;
            bottom: -5px;
            border-radius: 4px;
        }

        .nav-actions {
            display: flex;
            gap: 1.25rem;
            align-items: center;
            font-weight: 900;
            color: #333333;
            font-size: 0.95rem;
            white-space: nowrap;
        }

        .cart-pill {
            background: var(--kv-yellow);
            border-radius: 999px;
            padding: 0.55rem 0.8rem;
            color: var(--kv-red);
            font-weight: 1000;
        }

        .kv-hero {
            width: calc(100% - 2.4rem);
            max-width: 1560px;
            margin: 0 auto;
            background: linear-gradient(135deg, var(--kv-yellow) 0%, #ffef71 58%, #fff7c1 100%);
            min-height: 365px;
            border-radius: 0 0 24px 24px;
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: 0.94fr 1.06fr;
            box-sizing: border-box;
        }

        .kv-hero:before {
            content: "";
            position: absolute;
            width: 460px;
            height: 460px;
            border-radius: 50%;
            background: rgba(215,25,32,0.08);
            right: -110px;
            top: -130px;
        }

        .hero-copy {
            padding: 3rem 0 0 3.5rem;
            max-width: 530px;
            position: relative;
            z-index: 2;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            background: #ffffff;
            color: var(--kv-red);
            border-radius: 999px;
            padding: 0.48rem 0.85rem;
            font-weight: 1000;
            font-size: 0.84rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 18px rgba(0,0,0,0.08);
        }

        .hero-copy h1 {
            margin: 0;
            font-size: 3rem;
            line-height: 1.04;
            letter-spacing: -0.08rem;
            font-weight: 1000;
            color: #292929;
        }

        .hero-copy p {
            margin: 1rem 0 1.35rem 0;
            font-size: 1.02rem;
            line-height: 1.48;
            color: #333333;
        }

        .hero-button {
            border: 0;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 220px;
            height: 58px;
            font-weight: 1000;
            font-size: 1rem;
            color: #ffffff;
            background: var(--kv-red);
            box-shadow: 0 10px 22px rgba(215,25,32,0.23);
        }

        .hero-art {
            position: relative;
            min-height: 365px;
            z-index: 2;
        }

        .promo-board {
            position: absolute;
            right: 10%;
            top: 46px;
            width: 460px;
            height: 236px;
            background: #ffffff;
            border-radius: 24px;
            box-shadow: var(--kv-shadow);
            overflow: hidden;
            border: 1px solid rgba(0,0,0,0.05);
        }

        .promo-board-top {
            height: 58px;
            background: var(--kv-red);
            color: #ffffff;
            display: flex;
            align-items: center;
            padding-left: 1.35rem;
            font-size: 1.05rem;
            font-weight: 1000;
        }

        .promo-board-body {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.9rem;
            padding: 1.1rem;
        }

        .mini-tile {
            background: #f8f8f8;
            border: 1px solid #efefef;
            border-radius: 18px;
            padding: 1rem;
            min-height: 92px;
        }

        .mini-tile strong {
            display: block;
            color: var(--kv-red);
            font-size: 1.3rem;
            font-weight: 1000;
            margin-bottom: 0.25rem;
        }

        .mini-tile span {
            color: #444444;
            font-size: 0.83rem;
            line-height: 1.25;
            font-weight: 800;
        }

        .floating-badge {
            position: absolute;
            right: 2.5%;
            bottom: 52px;
            width: 150px;
            height: 150px;
            background: var(--kv-red);
            color: #ffffff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-size: 1.1rem;
            line-height: 1.1;
            font-weight: 1000;
            box-shadow: 0 18px 36px rgba(215,25,32,0.28);
        }

        .main-grid {
            width: calc(100% - 9rem);
            max-width: 1500px;
            margin: 2.25rem auto 3rem auto;
            display: grid;
            grid-template-columns: 1.08fr 0.72fr;
            gap: 2.6rem;
            align-items: start;
        }

        .support-card {
            background: #ffffff;
            border: 1px solid var(--kv-line);
            border-radius: 24px;
            padding: 1.55rem 1.7rem;
            box-shadow: 0 12px 34px rgba(0,0,0,0.055);
        }

        .support-card h2 {
            margin: 0 0 0.55rem 0;
            font-size: 1.88rem;
            font-weight: 1000;
            letter-spacing: -0.04rem;
        }

        .support-card p {
            color: #424242;
            font-size: 0.98rem;
            line-height: 1.52;
            max-width: 760px;
            margin-bottom: 0.9rem;
        }

        .quick-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .quick-card {
            background: #fafafa;
            border-radius: 18px;
            padding: 0.95rem 1rem;
            border: 1px solid #eeeeee;
            min-height: 88px;
        }

        .quick-card strong {
            display: block;
            font-size: 0.98rem;
            margin-bottom: 0.27rem;
            color: #222222;
        }

        .quick-card span {
            color: #666666;
            font-size: 0.82rem;
            line-height: 1.35;
        }

        .demo-note {
            background: #fffbe0;
            border: 1px solid #f1df6c;
            border-radius: 18px;
            padding: 0.9rem 1rem;
            font-size: 0.86rem;
            color: #242424;
            margin-top: 1rem;
        }

        .chat-column {
            display: flex;
            justify-content: flex-end;
        }

        .widget-wrap {
            width: 356px;
            max-width: 100%;
            margin-left: auto;
        }

        .widget {
            background: #ffffff;
            border: 1px solid rgba(215,25,32,0.16);
            border-radius: 28px;
            overflow: hidden;
            box-shadow: var(--kv-chat-shadow);
        }

        .widget-header {
            background: var(--kv-red);
            color: #ffffff;
            padding: 0.86rem 0.95rem 0.92rem 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.78rem;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        .header-copy {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.05rem;
            transform: translateY(-1px);
            min-width: 0;
        }

        .avatar {
            width: 42px;
            height: 42px;
            background: #ffffff;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 16px rgba(0,0,0,0.16);
            flex: 0 0 auto;
            overflow: hidden;
        }

        .kv-brandmark {
            width: 34px;
            height: 34px;
            background: var(--kv-red);
            border-radius: 9px;
            position: relative;
            display: block;
        }

        .kv-brandmark::before {
            content: "";
            position: absolute;
            width: 21px;
            height: 21px;
            border: 4px solid #ffffff;
            border-radius: 50%;
            top: 4.5px;
            left: 4.5px;
        }

        .kv-brandmark span {
            position: absolute;
            width: 4.7px;
            height: 4.7px;
            background: #ffffff;
            border-radius: 50%;
            z-index: 2;
        }

        .kv-brandmark .dot-1 { top: 12px; left: 10px; }
        .kv-brandmark .dot-2 { top: 9px; left: 15px; }
        .kv-brandmark .dot-3 { top: 6.5px; left: 20px; }
        .kv-brandmark .dot-4 { top: 18px; left: 15px; }
        .kv-brandmark .dot-5 { top: 22px; left: 20px; }

        .widget-title {
            font-size: 1.02rem;
            font-weight: 1000;
            margin: 0;
            letter-spacing: -0.01rem;
            line-height: 1.05;
        }

        .widget-status {
            font-size: 0.72rem;
            margin-top: 0.05rem;
            opacity: 0.98;
            line-height: 1.15;
            display: flex;
            align-items: center;
            white-space: nowrap;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            background: #69de80;
            border: 1px solid rgba(255,255,255,0.75);
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.38rem;
            flex: 0 0 auto;
        }

        .messages {
            padding: 0.78rem 0.78rem 0.48rem 0.78rem;
            height: 292px;
            overflow-y: auto;
            background: linear-gradient(180deg, #ffffff 0%, #fffdf1 100%);
        }

        .messages::-webkit-scrollbar { width: 6px; }
        .messages::-webkit-scrollbar-thumb {
            background: rgba(0,0,0,0.14);
            border-radius: 999px;
        }

        .bubble-row {
            display: flex;
            margin: 0.48rem 0;
        }

        .bubble-row.user { justify-content: flex-end; }
        .bubble-row.assistant { justify-content: flex-start; }

        .bubble {
            max-width: 87%;
            padding: 0.66rem 0.8rem;
            border-radius: 18px;
            font-size: 0.84rem;
            line-height: 1.39;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .bubble.user {
            background: var(--kv-red);
            color: #ffffff;
            border-bottom-right-radius: 6px;
            font-weight: 750;
            box-shadow: 0 6px 14px rgba(215,25,32,0.20);
        }

        .bubble.assistant {
            background: #ffffff;
            color: #121212;
            border-bottom-left-radius: 6px;
            border: 1px solid #ececec;
            box-shadow: 0 4px 12px rgba(0,0,0,0.045);
        }

        .input-box {
            padding: 0.72rem 0.78rem 0.78rem 0.78rem;
            background: #ffffff;
            border-top: 1px solid #f0f0f0;
        }

        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }

        div[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
            gap: 0.48rem;
            align-items: center;
        }

        div[data-testid="stTextInput"] { margin-bottom: 0 !important; }
        div[data-testid="stTextInput"] > div { border: none !important; box-shadow: none !important; }

        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus,
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-testid="stTextInput"] div[data-baseweb="input"]:active {
            height: 45px !important;
            min-height: 45px !important;
            background: #eeeeee !important;
            border: 0 !important;
            outline: 0 !important;
            box-shadow: none !important;
            border-radius: 999px !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextInput"] input:hover,
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextInput"] input:active {
            height: 45px !important;
            min-height: 45px !important;
            border-radius: 999px !important;
            border: 0 !important;
            outline: 0 !important;
            background: #eeeeee !important;
            color: #222222 !important;
            padding: 0 1.12rem !important;
            font-size: 0.9rem !important;
            box-shadow: none !important;
            caret-color: var(--kv-red) !important;
        }

        div[data-testid="stTextInput"] input::placeholder {
            color: #737373 !important;
            opacity: 1 !important;
        }

        div[data-testid="stForm"] button {
            width: 45px !important;
            min-width: 45px !important;
            height: 45px !important;
            min-height: 45px !important;
            background: var(--kv-green) !important;
            color: #ffffff !important;
            border: 0 !important;
            border-radius: 999px !important;
            font-weight: 1000 !important;
            padding: 0 !important;
            text-align: center !important;
            font-size: 1.28rem !important;
            line-height: 1 !important;
            box-shadow: 0 8px 18px rgba(0,138,46,0.24) !important;
            margin-top: 0 !important;
        }

        div[data-testid="stForm"] button p {
            font-size: 1.28rem !important;
            line-height: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div[data-testid="stForm"] button:hover {
            background: var(--kv-green-dark) !important;
            color: #ffffff !important;
        }

        .reset-button-wrapper {
            padding: 0 0.85rem 0.75rem 0.85rem;
            background: #ffffff;
        }

        div.stButton > button {
            background: #ffffff !important;
            color: var(--kv-red) !important;
            border: 1px solid rgba(215,25,32,0.20) !important;
            text-align: center !important;
            border-radius: 999px !important;
            font-weight: 850 !important;
            width: 100% !important;
            min-height: 34px !important;
            opacity: 1 !important;
            box-shadow: none !important;
            font-size: 0.84rem !important;
        }

        div.stButton > button:hover {
            background: #fff4f4 !important;
            color: var(--kv-red-dark) !important;
            border-color: rgba(215,25,32,0.36) !important;
        }

        .footer-scope {
            padding: 0 0.95rem 0.9rem 0.95rem;
            color: #777777;
            font-size: 0.63rem;
            line-height: 1.35;
            background: #ffffff;
        }

        @media (max-width: 1100px) {
            .kv-top-strip { display: none; }
            .kv-nav { padding: 0 1.25rem; gap: 1rem; }
            .nav-actions { display: none; }
            .kv-hero { grid-template-columns: 1fr; min-height: 330px; }
            .hero-art { display: none; }
            .main-grid { width: calc(100% - 2rem); grid-template-columns: 1fr; gap: 1.2rem; margin-top: 1.4rem; }
            .chat-column { justify-content: flex-start; }
            .widget-wrap { width: 100%; }
        }

        @media (max-width: 760px) {
            .cat-label { display: none; }
            .kv-logo { width: 78px; height: 52px; font-size: 0.92rem; }
            .top-search { height: 48px; font-size: 0.92rem; margin-left: 0; }
            .hero-copy { padding: 2rem 1.5rem; }
            .hero-copy h1 { font-size: 2.25rem; }
            .hero-button { min-width: 190px; height: 54px; }
            .messages { height: 280px; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="kv-page">
        <div class="kv-top-strip">
            <span>gratis retourneren</span>
            <span>snelle hulp bij je bestelling</span>
            <span>Kruidvat Club voordeel</span>
        </div>
        <div class="kv-nav">
            <div class="kv-logo">Kruidvat</div>
            <div class="hamburger" aria-hidden="true"><span></span><span></span><span></span></div>
            <div class="cat-label">categorieën⌄</div>
            <div class="top-search"><span>waar ben je naar op zoek?</span><span class="search-icon"></span></div>
            <div class="nav-actions"><span>acties</span><span>Kruidvat Club</span><span>inloggen</span><span class="cart-pill">mandje</span></div>
        </div>
        <div class="kv-hero">
            <div class="hero-copy">
                <div class="eyebrow">Kruidvat Klantenservice · prototype</div>
                <h1>slimmere hulp<br>bij webshopvragen</h1>
                <p>Een Kruidvat-stijl supportagent voor ontbrekende artikelen, beschadigde producten, partnerorders, bezorging en orderstatus.</p>
                <div class="hero-button">stel je vraag</div>
            </div>
            <div class="hero-art">
                <div class="promo-board">
                    <div class="promo-board-top">support die verder kijkt</div>
                    <div class="promo-board-body">
                        <div class="mini-tile"><strong>1</strong><span>vraag herkennen</span></div>
                        <div class="mini-tile"><strong>2</strong><span>ordercontext ophalen</span></div>
                        <div class="mini-tile"><strong>3</strong><span>slimmer doorzetten</span></div>
                        <div class="mini-tile"><strong>KV</strong><span>Kruidvat-stijl demo</span></div>
                    </div>
                </div>
                <div class="floating-badge">minder<br>onnodige<br>handoff</div>
            </div>
        </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-grid">', unsafe_allow_html=True)

left, right = st.columns([1.08, 0.72], gap="large")

with left:
    st.markdown(
        """
        <div class="support-card">
            <h2>waarmee kunnen we helpen?</h2>
            <p>
                Deze demo laat zien hoe een bestaande chatbotervaring kan worden uitgebreid met orderbewuste ondersteuning.
                De assistent helpt eerst zelfservicegericht, haalt voorbeeld-ordercontext op en schakelt pas door wanneer
                beoordeling, partnercontext of orderonderzoek nodig is.
            </p>
            <div class="quick-grid">
                <div class="quick-card"><strong>ontbrekend artikel</strong><span>Controleert ordercontext en legt uit wanneer medewerkeronderzoek nodig is.</span></div>
                <div class="quick-card"><strong>beschadigd product</strong><span>Geeft eerste stappen en verzamelt context voor beoordeling of vervanging.</span></div>
                <div class="quick-card"><strong>partnerorder</strong><span>Herkent wanneer retour- of beoordelingsstappen anders kunnen verlopen.</span></div>
                <div class="quick-card"><strong>slimmere escalatie</strong><span>Geeft medewerkers issue type, ordernummer, status en handoffreden mee.</span></div>
            </div>
            <div class="demo-note">
                <strong>Prototype-scope:</strong> gebruikt voorbeeldgegevens en verwerkt geen persoonsgegevens.
                De assistent maakt geen retouren aan; hij begeleidt, haalt voorbeeld-ordercontext op en escaleert wanneer nodig.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown('<div class="chat-column"><div class="widget-wrap"><div class="widget">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="widget-header">
            <div class="avatar" aria-label="Kruidvat logo">
                <div class="kv-brandmark" aria-hidden="true">
                    <span class="dot-1"></span>
                    <span class="dot-2"></span>
                    <span class="dot-3"></span>
                    <span class="dot-4"></span>
                    <span class="dot-5"></span>
                </div>
            </div>
            <div class="header-copy">
                <div class="widget-title">Kruidvat Klantenservice</div>
                <div class="widget-status"><span class="status-dot"></span>online</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="messages">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        role = message["role"]
        safe_text = html.escape(message["content"])
        st.markdown(
            f"""
            <div class="bubble-row {role}">
                <div class="bubble {role}">{safe_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="input-box">', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        input_col, send_col = st.columns([7.2, 0.9], gap="small")

        with input_col:
            user_text = st.text_input(
                "Typ je vraag",
                placeholder="waarmee kan Kruidvat Klantenservice je helpen?",
                label_visibility="collapsed",
                key="kruidvat_hulp_chat_message_input",
            )

        with send_col:
            submitted = st.form_submit_button("→")

        if submitted and user_text.strip():
            add_user_message(user_text.strip())
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="reset-button-wrapper">', unsafe_allow_html=True)
    if st.button("Chat resetten", key="reset", use_container_width=True):
        st.session_state.messages = initial_messages()
        st.session_state.sender_id = new_sender_id()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="footer-scope">
            Prototype: algemene Kruidvat-supportbegeleiding plus orderlookup met voorbeeldgegevens.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div></div></div>", unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)
