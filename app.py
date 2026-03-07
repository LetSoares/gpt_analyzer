import re
import streamlit as st
from urllib.parse import urlparse
from openai import OpenAI

st.set_page_config(page_title="GPT Response Analyzer", page_icon="🔍", layout="centered")

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
                            "country": "BR"
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
               with st.expander(f"## Buscas realizadas pelo modelo ({len(r['queries'])})"):
                    if r["queries"]:
                        for q in r["queries"]:
                            st.markdown(f"- 🔍 {q}")
                    else:
                        st.caption("Nenhuma busca identificada.")
                st.divider()

                # ── 3. Fontes citadas ─────────────────────────────────────────
                with st.expander(f"## Fontes citadas ({len(r['fontes_citadas'])})"):
                    if r["fontes_citadas"]:
                        for fonte in r["fontes_citadas"]:
                            st.markdown(f"- [{fonte['title']}]({fonte['url']})")
                    else:
                        st.caption("Nenhuma fonte citada identificada.")
                                st.divider()

                # ── 4. Fontes lidas ───────────────────────────────────────────
                with st.expander(f"## Fontes lidas ({len(r['fontes_lidas'])})"):
                    if dominios_lidos:
                        for dominio, paginas in dominios_lidos:
                            st.markdown(f"**🌐 {dominio}** ({len(paginas)} página{'s' if len(paginas) > 1 else ''})")
                            for p in paginas:
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- [{p['title']}]({p['url']})")
                    else:
                        st.caption("Nenhuma fonte lida identificada.")

                # ── Debug ─────────────────────────────────────────────────────
                with st.expander("🐛 Output bruto da API"):
                    st.json(resp.model_dump())

            except Exception as e:
                st.error(f"Erro: {e}")
                st.exception(e)
