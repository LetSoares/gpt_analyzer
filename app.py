import re
import streamlit as st
from urllib.parse import urlparse
from openai import OpenAI

st.set_page_config(page_title="GPT Response Analyzer", page_icon="🔍", layout="centered")

# ─── Brand CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;700&display=swap');

/* ── Tokens ── */
:root {
  --navy:   #060638;
  --red:    #e72a1c;
  --white:  #ffffff;
  --off:    #f4f4f4;
  --muted:  #8888aa;
  --card:   #0b0b50;
  --border: #1a1a7a;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--white) !important;
  color: var(--navy) !important;
  font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stMain"] { background: var(--navy) !important; }
[data-testid="stBottom"] { background: var(--navy) !important; }
.stMainBlockContainer { padding-top: 2rem !important; }
section[data-testid="stSidebar"] { background: #040428 !important; }

/* ── Hero header ── */
.ls-hero {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  padding: 2rem 0 1.2rem;
  border-bottom: 2px solid var(--red);
  margin-bottom: 0.5rem;
}
.ls-logo-text {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 3rem;
  line-height: 0.95;
  letter-spacing: 0.01em;
  color: var(--white);
}
.ls-logo-text span { color: var(--red); }
.ls-tagline {
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 0.25rem;
}

/* ── Section titles ── */
h1, h2, h3 {
  font-family: 'Bebas Neue', sans-serif !important;
  letter-spacing: 0.04em !important;
  color: var(--white) !important;
}

/* ── Labels ── */
label, .stTextInput label, .stTextArea label {
  font-size: 0.7rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  font-weight: 500 !important;
}

/* ── Inputs ── */
input[type="password"],
input[type="text"],
textarea {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  color: var(--white) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.95rem !important;
  caret-color: var(--red) !important;
}
input:focus, textarea:focus {
  border-color: var(--red) !important;
  box-shadow: 0 0 0 2px rgba(231,42,28,0.18) !important;
}

/* ── Primary button ── */
[data-testid="stButton"] > button {
  background: var(--red) !important;
  color: var(--white) !important;
  border: none !important;
  border-radius: 6px !important;
  font-family: 'Bebas Neue', sans-serif !important;
  font-size: 1.1rem !important;
  letter-spacing: 0.1em !important;
  padding: 0.6rem 1.4rem !important;
  transition: background 0.15s, transform 0.1s !important;
}
[data-testid="stButton"] > button:hover {
  background: #c42218 !important;
  transform: translateY(-1px) !important;
}
[data-testid="stButton"] > button:active { transform: translateY(0) !important; }

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.4rem 0 !important;
}

/* ── Success / Error alerts ── */
[data-testid="stAlert"] {
  border-radius: 6px !important;
  font-family: 'DM Sans', sans-serif !important;
}
div[data-baseweb="notification"][kind="positive"] {
  background: rgba(231,42,28,0.12) !important;
  border-left: 3px solid var(--red) !important;
}

/* ── Markdown body ── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
  color: #d0d0ee !important;
  line-height: 1.7 !important;
}
[data-testid="stMarkdownContainer"] a {
  color: var(--red) !important;
  text-decoration: none !important;
}
[data-testid="stMarkdownContainer"] a:hover {
  text-decoration: underline !important;
}

/* ── Expanders ── */
details {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  margin-bottom: 0.6rem !important;
  overflow: hidden !important;
}
details summary {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  color: var(--white) !important;
  padding: 0.75rem 1rem !important;
  cursor: pointer !important;
  user-select: none !important;
  list-style: none !important;
}
details summary:hover { color: var(--red) !important; }
details[open] summary { border-bottom: 1px solid var(--border); }
details > div { padding: 0.75rem 1rem 1rem !important; }

/* ── Caption ── */
.stCaptionContainer, small {
  color: var(--muted) !important;
  font-size: 0.75rem !important;
}

/* ── JSON viewer ── */
[data-testid="stJson"] {
  background: #040428 !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: var(--red) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--red); }
</style>
""", unsafe_allow_html=True)

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ls-hero">
  <div>
    <div class="ls-logo-text">letícia<br>s<span>oo</span>res</div>
  </div>
  <div style="margin-left:auto; text-align:right;">
    <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem; color:var(--red); letter-spacing:0.06em;">GPT Response Analyzer</div>
    <div class="ls-tagline">gpt-5.4 · web_search · BR</div>
  </div>
</div>
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
