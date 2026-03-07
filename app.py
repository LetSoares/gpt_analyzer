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

    for item in response.output:
        if item.type == "web_search_call":
            if item.action.type == "search":
                for query in item.action.queries:
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

    resposta_final = response.output[-1].content[0].text

    return {
        "resposta": resposta_final,
        "queries": queries,
        "fontes_lidas": fontes_apenas_lidas,
        "fontes_citadas": fontes_citadas,
    }


def conta_dom(lista_de_fontes):
    dominios_citados = {}
    for fonte in lista_de_fontes:
        url_bruta = fonte["url"] if isinstance(fonte, dict) else fonte
        if not url_bruta:
            continue
        url = re.sub(r'\?utm_source=openai$', '', url_bruta)
        url = re.sub(r'\?utm_source=openai&', '?', url)
        url = re.sub(r'&utm_source=openai', '', url)
        dominio = urlparse(url).netloc
        if dominio.startswith("www."):
            dominio = dominio[4:]
        if not dominio:
            continue
        if dominio not in dominios_citados:
            dominios_citados[dominio] = {"quantidade": 0, "urls": set()}
        dominios_citados[dominio]["quantidade"] += 1
        dominios_citados[dominio]["urls"].add(url)

    return sorted(
        dominios_citados.items(),
        key=lambda item: item[1]["quantidade"],
        reverse=True,
    )


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
                            "city": "São Paulo",
                        },
                    }],
                    tool_choice="required",
                    reasoning={"effort": "high"},
                    store=False,
                    include=["web_search_call.results", "web_search_call.action.sources"],
                    input=prompt,
                )

                resultado = extract(resp)
                dominios_lidos   = conta_dom(resultado["fontes_lidas"])
                dominios_citados = conta_dom(resultado["fontes_citadas"])

                st.success("Concluído!")
                st.divider()

                # Dicionário de resultados — fiel ao Colab
                st.subheader("Dicionário de resultados")
                st.json({
                    "queries":        resultado["queries"],
                    "fontes_lidas":   resultado["fontes_lidas"],
                    "fontes_citadas": resultado["fontes_citadas"],
                    "dominios_lidos": [
                        {"dominio": d, "quantidade": v["quantidade"], "urls": list(v["urls"])}
                        for d, v in dominios_lidos
                    ],
                    "dominios_citados": [
                        {"dominio": d, "quantidade": v["quantidade"], "urls": list(v["urls"])}
                        for d, v in dominios_citados
                    ],
                })

                st.divider()
                st.subheader("Resposta")
                st.markdown(resultado["resposta"])

                # Debug — output bruto da API
                with st.expander("🐛 Output bruto da API"):
                    st.json(resp.model_dump())

            except Exception as e:
                st.error(f"Erro: {e}")
                st.exception(e)
