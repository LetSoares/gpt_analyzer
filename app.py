import re
import streamlit as st
from urllib.parse import urlparse
from openai import OpenAI

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GPT Response Analyzer",
    page_icon="🔍",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { background-color: #080c10; color: #e0e0e0; }

h1 { font-family: 'Syne', sans-serif !important; font-size: 2.2rem !important; color: #ffffff !important; }
h2, h3 { font-family: 'Syne', sans-serif !important; color: #ffffff !important; }

.stTextInput > label, .stTextArea > label {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555 !important;
}
.stTextInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 13px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(0, 229, 160, 0.4) !important;
    box-shadow: none !important;
}

.stButton > button {
    background: #00e5a0 !important;
    color: #080c10 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.08em !important;
    padding: 14px 32px !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

.metric-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 6px;
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #555;
}
.section-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.query-tag {
    display: inline-block;
    background: rgba(240,192,64,0.1);
    border: 1px solid rgba(240,192,64,0.3);
    color: #f0c040;
    border-radius: 6px;
    padding: 4px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    margin: 4px;
}
.url-row {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    padding: 7px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #8ab4f8;
}
.domain-label {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #ccc;
}
.info-box {
    background: rgba(0,229,160,0.05);
    border: 1px solid rgba(0,229,160,0.15);
    border-radius: 10px;
    padding: 12px 16px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #00e5a0;
    margin-bottom: 16px;
}
.error-box {
    background: rgba(255,80,80,0.08);
    border: 1px solid rgba(255,80,80,0.2);
    border-radius: 10px;
    padding: 12px 16px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #ff8080;
    margin-bottom: 16px;
}
div[data-testid="stTabs"] button {
    font-family: 'Syne', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    color: #555 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00e5a0 !important;
}
.stExpander { border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


# ─── Lógica de extração (idêntica ao seu Python) ──────────────────────────────

def extract(response):
    queries = []
    fontes_lidas = []
    fontes_citadas = []

    for item in response.output:
        if item.type == "web_search_call":
            if item.action.type == "search":
                for query in item.action.queries:
                    if query not in queries:
                        queries.append(query)
                for source in item.action.sources:
                    if source.url not in fontes_lidas:
                        fontes_lidas.append(source.url)
            elif item.action.type == "open_page":
                if item.action.url not in fontes_lidas:
                    fontes_lidas.append(item.action.url)

    for item in response.output:
        if item.type == "message":
            for annotation in item.content[0].annotations:
                if annotation.type == "url_citation":
                    if annotation.url not in fontes_citadas:
                        fontes_citadas.append(annotation.url)

    urls_citadas = [re.sub(r'\?utm_source=openai$', '', f) for f in fontes_citadas]
    fontes_apenas_lidas = [f for f in fontes_lidas if f not in urls_citadas]

    resposta_final = ""
    for item in reversed(response.output):
        if item.type == "message":
            resposta_final = item.content[0].text
            break

    return {
        "resposta": resposta_final,
        "queries": queries,
        "fontes_lidas": fontes_apenas_lidas,
        "fontes_citadas": fontes_citadas,
    }


def conta_dom(lista_de_fontes):
    dominios = {}
    for fonte in lista_de_fontes:
        url = fonte if isinstance(fonte, str) else fonte.get("url", "")
        if not url:
            continue
        url = re.sub(r'\?utm_source=openai$', '', url)
        url = re.sub(r'\?utm_source=openai&', '?', url)
        url = re.sub(r'&utm_source=openai', '', url)
        dominio = urlparse(url).netloc
        if dominio.startswith("www."):
            dominio = dominio[4:]
        if not dominio:
            continue
        if dominio not in dominios:
            dominios[dominio] = {"quantidade": 0, "urls": []}
        dominios[dominio]["quantidade"] += 1
        if url not in dominios[dominio]["urls"]:
            dominios[dominio]["urls"].append(url)

    return sorted(dominios.items(), key=lambda x: x[1]["quantidade"], reverse=True)


# ─── UI ───────────────────────────────────────────────────────────────────────

st.markdown("## 🔍 GPT Response Analyzer")
st.markdown("*Veja exatamente o que o GPT pesquisou, leu e citou para responder seu prompt.*")
st.divider()

# Inputs
col_key, col_model = st.columns([3, 1])
with col_key:
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
with col_model:
    model = st.selectbox("Modelo", ["gpt-5.4","gpt-5", "gpt-5-mini", "gpt-4"], index=0)

prompt = st.text_area("Seu Prompt", placeholder="Ex: Qual é o melhor...?", height=120)

st.markdown(
    '<div class="info-box">🔒 Sua API key não é salva em nenhum lugar — usada apenas nesta sessão.</div>',
    unsafe_allow_html=True,
)

run = st.button("→ Analisar Resposta")

# ─── Execução ─────────────────────────────────────────────────────────────────

if run:
    if not api_key.strip():
        st.markdown('<div class="error-box">⚠ Insira sua OpenAI API Key.</div>', unsafe_allow_html=True)
    elif not prompt.strip():
        st.markdown('<div class="error-box">⚠ Insira um prompt antes de continuar.</div>', unsafe_allow_html=True)
    else:
        with st.spinner("GPT pesquisando na web..."):
            try:
                client = OpenAI(api_key=api_key.strip())
                resp = client.responses.create(
                    model=model,
                    tools=[{
                        "type": "web_search_preview",
                        "user_location": {
                            "type": "approximate",
                            "country": "BR"                            
                        },
                    }],
                    tool_choice="required",
                    store=False,
                    include=["web_search_call.results"],
                    input=prompt,
                )

                dados = extract(resp)
                dominios_lidos = conta_dom(dados["fontes_lidas"])
                dominios_citados = conta_dom(dados["fontes_citadas"])

                st.success("Análise concluída!")
                st.divider()

                # ── Métricas ──
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color:#f0c040">{len(dados["queries"])}</div>
                        <div class="metric-label">Queries</div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color:#60c8ff">{len(dados["fontes_lidas"])}</div>
                        <div class="metric-label">Fontes Lidas</div>
                    </div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color:#00e5a0">{len(dados["fontes_citadas"])}</div>
                        <div class="metric-label">Fontes Citadas</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Tabs ──
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🔍 Queries",
                    "🔗 Fontes Citadas",
                    "👁 Fontes Lidas",
                    "📊 Domínios",
                    "💬 Resposta",
                ])

                with tab1:
                    if dados["queries"]:
                        tags_html = "".join(f'<span class="query-tag">{q}</span>' for q in dados["queries"])
                        st.markdown(f'<div style="padding:8px 0">{tags_html}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Nenhuma query identificada.")

                with tab2:
                    if dados["fontes_citadas"]:
                        for i, url in enumerate(dados["fontes_citadas"]):
                            st.markdown(f'`{i+1:02d}` [{url}]({url})')
                    else:
                        st.info("Nenhuma fonte citada identificada.")

                with tab3:
                    if dados["fontes_lidas"]:
                        for i, url in enumerate(dados["fontes_lidas"]):
                            st.markdown(f'`{i+1:02d}` [{url}]({url})')
                    else:
                        st.info("Nenhuma fonte apenas lida identificada.")

                with tab4:
                    col_l, col_c = st.columns(2)
                    with col_l:
                        st.markdown("**👁 Domínios Lidos**")
                        if dominios_lidos:
                            max_val = dominios_lidos[0][1]["quantidade"]
                            for domain, data in dominios_lidos[:10]:
                                st.markdown(f"`{domain}` — **{data['quantidade']}x**")
                                st.progress(data["quantidade"] / max_val)
                        else:
                            st.info("Nenhum domínio.")
                    with col_c:
                        st.markdown("**🔗 Domínios Citados**")
                        if dominios_citados:
                            max_val = dominios_citados[0][1]["quantidade"]
                            for domain, data in dominios_citados[:10]:
                                st.markdown(f"`{domain}` — **{data['quantidade']}x**")
                                st.progress(data["quantidade"] / max_val)
                        else:
                            st.info("Nenhum domínio.")

                with tab5:
                    if dados["resposta"]:
                        st.markdown(dados["resposta"])
                    else:
                        st.info("Resposta não encontrada no output.")

            except Exception as e:
                st.markdown(
                    f'<div class="error-box">⚠ Erro: {str(e)}</div>',
                    unsafe_allow_html=True,
                )
