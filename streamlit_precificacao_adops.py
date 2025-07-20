import streamlit as st
import math

st.set_page_config(page_title="Precificação P1 e P2", layout="centered")
st.title("📊 Sistema de Precificação AdOps")

pagina = st.sidebar.selectbox("Selecione a Página", ["Precificação P1", "Precificação P2 (Rewarded)"])

def mostrar_variacoes(ultima_regra, acao):
    variacoes = {
        "leve": (0.05, 0.10),
        "média": (0.10, 0.20),
        "agressiva": (0.20, 0.30)
    }

    for tipo, (pct_min, pct_max) in variacoes.items():
        if acao == "aumentar":
            min_val = ultima_regra * (1 + pct_min)
            max_val = ultima_regra * (1 + pct_max)
        else:
            min_val = ultima_regra * (1 - pct_max)
            max_val = ultima_regra * (1 - pct_min)
        st.markdown(f"🔹 **Variação {tipo.capitalize()}** ({int(pct_min*100)}% a {int(pct_max*100)}%) → **${min_val:.2f} a ${max_val:.2f}**")

# Página P1
if pagina == "Precificação P1":
    st.subheader("📋 Análise Interativa - Precificação P1")
    with st.form("form_p1"):
        bloco = st.selectbox("Bloco", options=["mob_top", "mob_interstitial"])
        cpc_atual = st.number_input("CPC Atual ($)", min_value=0.0, step=0.01)
        cobertura = st.number_input("Cobertura (%)", min_value=0.0, max_value=100.0, step=0.1)
        ultima_regra = st.number_input("Último valor da regra ($)", min_value=0)
        cpa = st.number_input("CPA Médio ($)", min_value=0.0, step=0.01)
        roas_meta = st.number_input("Meta de ROAS (%)", min_value=0.0, max_value=1.0, step=0.01, value=0.70)
        submitted = st.form_submit_button("Analisar Bloco")

    if submitted:
        cpc_alvo = cpa * roas_meta
        if bloco == "mob_top":
            if cpc_atual < cpc_alvo:
                acao = "aumentar" if cobertura > 30 else "diminuir"
            else:
                acao = "aumentar" if cobertura > 80 else "manter"
        else:
            if cpc_atual < cpc_alvo:
                acao = "aumentar" if cobertura > 80 else "diminuir"
            else:
                acao = "aumentar" if cobertura > 95 else "manter"

        st.success(f"Ação recomendada: **{acao.upper()}**")
        st.info(f"CPC Alvo calculado: **${cpc_alvo:.3f}**")
        if acao in ["aumentar", "diminuir"]:
            mostrar_variacoes(ultima_regra, acao)
        else:
            st.write("🔸 Nenhuma mudança recomendada. Regra pode ser mantida.")

# Página P2
elif pagina == "Precificação P2 (Rewarded)":
    st.subheader("📋 Análise Interativa - Precificação P2 (Rewarded)")
    with st.form("form_p2"):
        solicitacoes = st.number_input("Solicitações de anúncios", min_value=0)
        impressoes = st.number_input("Impressões", min_value=0)
        cliques = st.number_input("Cliques", min_value=0)
        cobertura = st.number_input("Cobertura (%)", min_value=0.0, max_value=100.0, step=0.1, value=100.0)
        receita = st.number_input("Receita ($)", min_value=0.0, step=0.01)
        ultima_regra = st.number_input("Último valor da regra ($)", min_value=0)
        cpa = st.number_input("CPA Médio ($)", min_value=0.0, step=0.01)
        roas_meta = st.number_input("Meta de ROAS (%)", min_value=0.0, max_value=1.0, step=0.01, value=0.70)
        cpc_mob_top = st.number_input("CPC do mob_top da P2 ($)", min_value=0.0, step=0.01)
        submitted_p2 = st.form_submit_button("Analisar Rewarded")

    if submitted_p2:
        perda_usuario = math.ceil((solicitacoes * (cobertura / 100)) - impressoes)
        perda_usuario = max(perda_usuario, 0)
        total_usuarios = cliques + perda_usuario
        cpc_corrigido = receita / total_usuarios if total_usuarios > 0 else 0
        cpc_alvo = cpa * roas_meta

        st.info(f"CPC Corrigido: **${cpc_corrigido:.3f}**")
        st.info(f"CPC Alvo: **${cpc_alvo:.3f}**")
        st.info(f"Perda de Usuário estimada: **{perda_usuario}**")

        if cpc_corrigido > cpc_alvo and cobertura > 30 and cpc_corrigido > cpc_mob_top:
            acao = "aumentar"
        elif cpc_corrigido < cpc_alvo and cobertura > 30 and cpc_corrigido < cpc_mob_top:
            acao = "diminuir"
        else:
            acao = "manter"

        st.success(f"Ação recomendada: **{acao.upper()}**")
        if acao in ["aumentar", "diminuir"]:
            mostrar_variacoes(ultima_regra, acao)
        else:
            st.write("🔸 Nenhuma mudança recomendada. Regra pode ser mantida.")
