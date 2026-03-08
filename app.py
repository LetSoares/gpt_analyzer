import re
import base64 
import streamlit as st
from urllib.parse import urlparse
from openai import OpenAI

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

st.set_page_config(page_title="GPT Response Analyzer", page_icon="🔍", layout="centered")

# ─── Brand CSS ────────────────────────────────────────────────────────────────
def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_b64 = get_image_base64("assets/logo-leticia.png")
font_b64_bold = get_image_base64("assets/GCARTURM-BOLD.TTF")
font_b64_reg = get_image_base64("assets/GCARTURM-REGULAR.TTF")

st.markdown(f"""
    <style>
        @font-face {{
            font-family: 'GCartumBold';
            src: url('data:font/truetype;base64,{font_b64_bold}') format('truetype');
        }}
        @font-face {{
            font-family: 'GCartumRegular';
            src: url('data:font/truetype;base64,{font_b64_reg}') format('truetype');
        }}

        /* ── Fonte nos inputs ── */
        label, input, textarea, button,
        [data-testid="stTextInput"] *,
        [data-testid="stTextArea"] *,
        [data-testid="stButton"] * {{
            font-family: 'GCartumRegular', serif !important;
        }}

        /* ── Protege ícones e setas do Streamlit ── */
        [data-testid="stMetric"] *,
        [class*="arrow"] *,
        span[data-testid],
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary svg *,
        .streamlit-expanderHeader svg,
        [class*="st-emotion-cache"] svg {{
            font-family: sans-serif !important;
        }}

        /* ── Labels dos inputs ── */
        [data-testid="stTextInput"] label,
        [data-testid="stTextArea"] label {{
            color: #000000 !important;
            font-family: 'GCartumBold', serif !important;
            font-size: 15px;
        }}

        /* ── Caixas de input e textarea ── */
        [data-testid="stTextInput"] input {{
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #060638 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 15px rgba(231, 42, 28, 0.4) !important;
            font-family: 'GCartumRegular', serif !important;
        }}

        [data-testid="stTextArea"] textarea {{
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #060638 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 15px rgba(231, 42, 28, 0.7) !important;
            font-family: 'GCartumRegular', serif !important;
        }}

        /* ── Placeholder ── */
        input::placeholder,
        textarea::placeholder {{
            color: rgba(0, 0, 0, 0.4) !important;
            opacity: 1 !important;
            -webkit-text-fill-color: rgba(0, 0, 0, 0.4) !important;
        }}

        /* ── Botão ── */
        [data-testid="stButton"] button {{
            background-color: #e72a1c !important;
            color: #ffffff !important;
            border: 2px solid #060638 !important;
            border-radius: 10px !important;
            font-family: 'GCartumBold', serif !important;
            transition: box-shadow 0.2s ease !important;
        }}
        [data-testid="stButton"] button:hover {{
            background-color: #e72a1c !important;
            border-color: #060638 !important;
            box-shadow: 0 4px 15px rgba(231, 42, 28, 0.8) !important;
        }}
    </style>

    <div style="text-align: center; padding: 20px 0 5px 0;">
        <h1 style="margin: 0; font-family: 'GCartumBold', serif; font-size: 2rem; color: #060638;">
            🔎 ChatGPT Response Analyzer
        </h1>
        <p style="margin: 2px 0 0 0; font-family: 'GCartumRegular', serif; font-size: 0.7rem; color: #060638; opacity: 0.7;">
            gpt-5.4 · web search breakdown · BR
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; margin-top: 8px;">
            <a href="https://instagram.com/leticiasoares.seo" target="_blank" style="color: inherit; text-decoration: none;">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width:22px; height:22px; fill:#060638;">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
            </a>
            <a href="https://www.linkedin.com/in/leticia-soaresg" target="_blank" style="color: inherit; text-decoration: none;">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width:22px; height:22px; fill:#060638;">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
            </a>
        </div>
    </div>
    <div style="border-bottom: 3px solid #e72a1c; margin: 10px 0;"></div>
""", unsafe_allow_html=True)

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

api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
prompt  = st.text_area("Prompt", placeholder="Qual é o melhor banco para investir em 2026?", height=120)
run     = st.button("Analisar", use_container_width=True)

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

st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: 5px; padding: 20px 0;">
        <img src="data:image/png;base64,{logo_b64}" style="height: 100px; width: auto;" />
    </div>
""", unsafe_allow_html=True)
