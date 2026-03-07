import re
import streamlit as st
from urllib.parse import urlparse
from openai import OpenAI

st.set_page_config(page_title="GPT Response Analyzer", page_icon="🔍", layout="centered")

# ─── Brand CSS ────────────────────────────────────────────────────────────────
logo = "assets/logo-leticia-.png"
fonte = "assets/GCARTUM-BOLD.TTF"  
title = "ChatGPT Response Analyzer"

def load_file_as_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_header():
    # Carrega logo como base64
    try:
        logo_b64 = load_file_as_base64(LOGO_PATH)
        logo_tag = f'<img src="data:image/png;base64,{logo_b64}" class="header-logo" alt="Logo" />'
    except FileNotFoundError:
        # Placeholder enquanto a logo não está disponível
        logo_tag = '<div class="logo-placeholder">LOGO</div>'

    # Carrega fonte como base64
    try:
        font_b64 = load_file_as_base64(FONT_PATH)
        font_face = f"""
        @font-face {{
            font-family: 'GCartum';
            src: url('data:font/truetype;base64,{font_b64}') format('truetype');
            font-weight: bold;
        }}
        """
    except FileNotFoundError:
        # Fallback para fonte serifada enquanto a fonte não está disponível
        font_face = """
        @font-face {
            font-family: 'GCartum';
            src: local('Georgia');
        }
        """

    st.markdown(f"""
    <style>
        /* ── Reset do header padrão do Streamlit ── */
        [data-testid="stHeader"] {{
            display: none !important;
        }}

        /* ── Fonte customizada ── */
        {font_face}

        /* ── Container principal do header ── */
        .brand-header {{
            position: sticky;
            top: 0;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 40px;
            background-color: #ffffff;
            border-bottom: 3px solid #e72a1c;
            box-shadow: 0 2px 12px rgba(6, 6, 56, 0.08);
        }}

        /* ── Logo ── */
        .header-logo {{
            height: 52px;
            width: auto;
            object-fit: contain;
            display: block;
        }}

        /* ── Placeholder da logo (remove quando tiver a imagem real) ── */
        .logo-placeholder {{
            height: 52px;
            width: 120px;
            background: #060638;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 0.15em;
            border-radius: 4px;
        }}

        /* ── Título ── */
        .header-title {{
            font-family: 'GCartum', Georgia, serif;
            font-size: 22px;
            font-weight: bold;
            color: #060638;
            letter-spacing: 0.04em;
            text-align: right;
            line-height: 1.2;
            margin: 0;
        }}

        /* ── Linha de destaque abaixo do título ── */
        .header-title span {{
            display: block;
            height: 3px;
            width: 100%;
            background: linear-gradient(90deg, #e72a1c, #060638);
            margin-top: 5px;
            border-radius: 2px;
        }}

        /* ── Padding do conteúdo para não ficar atrás do header fixo ── */
        .main .block-container {{
            padding-top: 90px !important;
        }}
    </style>

    <div class="brand-header">
        {logo_tag}
        <div class="header-title">
            {APP_TITLE}
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Chame esta função no topo do seu app ──
render_header()


# ─── Extração — idêntica ao Colab ─────────────────────────────────────────────

def extract(response):
    queries = []
    fontes_lidas = []
    fontes_citadas = []
    urls_lidas_vistas = set()
    urls_citadas_vistas = set()

    for item in response.output:
        if item.type == "web_search_call":
            if item.action.type == "search":
                for query in item.action.queries:
                    queries.append(query)
                for source in item.action.sources:
                    if source.url not in urls_lidas_vistas:
                        urls_lidas_vistas.add(source.url)
                        fontes_lidas.append({
                            "url":   source.url,
                            "title": getattr(source, "title", None) or source.url,
                        })
            elif item.action.type == "open_page":
                if item.action.url not in urls_lidas_vistas:
                    urls_lidas_vistas.add(item.action.url)
                    fontes_lidas.append({
                        "url":   item.action.url,
                        "title": getattr(item.action, "title", None) or item.action.url,
                    })

    for item in response.output:
        if item.type == "message":
            for annotation in item.content[0].annotations:
                if annotation.type == "url_citation":
                    url_limpa = re.sub(r'\?utm_source=openai$', '', annotation.url)
                    if url_limpa not in urls_citadas_vistas:
                        urls_citadas_vistas.add(url_limpa)
                        fontes_citadas.append({
                            "url":   url_limpa,
                            "title": getattr(annotation, "title", None) or url_limpa,
                        })

    fontes_apenas_lidas = [
        f for f in fontes_lidas
        if re.sub(r'\?utm_source=openai$', '', f["url"]) not in urls_citadas_vistas
    ]

    resposta_final = response.output[-1].content[0].text

    return {
        "resposta": resposta_final,
        "queries": queries,
        "fontes_lidas": fontes_apenas_lidas,
        "fontes_citadas": fontes_citadas,
    }


def agrupa_por_dominio(fontes):
    """Recebe lista de {"url", "title"} e agrupa por domínio."""
    dominios = {}
    for fonte in fontes:
        url = re.sub(r'\?utm_source=openai$', '', fonte["url"])
        url = re.sub(r'\?utm_source=openai&', '?', url)
        url = re.sub(r'&utm_source=openai', '', url)
        dominio = urlparse(url).netloc.replace("www.", "")
        if not dominio:
            continue
        if dominio not in dominios:
            dominios[dominio] = []
        dominios[dominio].append({"url": url, "title": fonte["title"]})

    return sorted(dominios.items(), key=lambda x: len(x[1]), reverse=True)


# ─── UI ───────────────────────────────────────────────────────────────────────

st.title("🔍 GPT Response Analyzer")
st.caption("gpt-5.4 · web_search · BR")
st.divider()

api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
prompt  = st.text_area("Prompt", placeholder="Qual é o melhor banco para investir em 2026?", height=120)
run     = st.button("→ Analisar", use_container_width=True)

# ─── Execução ─────────────────────────────────────────────────────────────────

if run:
    if not api_key.strip():
        st.error("Insira sua API Key.")
    elif not prompt.strip():
        st.error("Insira um prompt.")
    else:
        with st.spinner("Aguardando gpt-5.4..."):
            try:
                client = OpenAI(api_key=api_key.strip())

                resp = client.responses.create(
                    model="gpt-5.4",
                    tools=[{
                        "type": "web_search",
                        "user_location": {
                            "type": "approximate",
                            "country": "BR",
                        },
                    }],
                    tool_choice="required",
                    reasoning={"effort": "high"},
                    store=False,
                    include=["web_search_call.results", "web_search_call.action.sources"],
                    input=prompt,
                )

                r = extract(resp)
                dominios_lidos = agrupa_por_dominio(r["fontes_lidas"])

                st.success("Concluído!")
                st.divider()

                # ── 1. Resposta ───────────────────────────────────────────────
                st.markdown("## Resposta")
                st.markdown(r["resposta"])
                st.divider()

                # ── 2. Buscas realizadas ──────────────────────────────────────
                with st.expander(f"Buscas realizadas pelo modelo ({len(r['queries'])})"):
                    if r["queries"]:
                        for q in r["queries"]:
                            st.markdown(f"- 🔍 {q}")
                    else:
                        st.caption("Nenhuma busca identificada.")

                # ── 3. Fontes citadas ─────────────────────────────────────────
                with st.expander(f"Fontes citadas ({len(r['fontes_citadas'])})"):
                    if r["fontes_citadas"]:
                        for fonte in r["fontes_citadas"]:
                            st.markdown(f"- [{fonte['title']}]({fonte['url']})")
                    else:
                        st.caption("Nenhuma fonte citada identificada.")

                # ── 4. Fontes lidas ───────────────────────────────────────────
                st.markdown(f"Fontes lidas ({len(r['fontes_lidas'])})")
                if dominios_lidos:
                    for dominio, paginas in dominios_lidos:
                        label = f"🌐 {dominio} ({len(paginas)} página{'s' if len(paginas) > 1 else ''})"
                        with st.expander(label):
                            for p in paginas:
                                st.markdown(f"- [{p['title']}]({p['url']})")
                else:
                    st.caption("Nenhuma fonte lida identificada.")

                # ── Debug ─────────────────────────────────────────────────────
                with st.expander("🐛 Output bruto da API"):
                    st.json(resp.model_dump())

            except Exception as e:
                st.error(f"Erro: {e}")
                st.exception(e)
