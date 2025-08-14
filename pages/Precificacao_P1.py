import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Precificação P1")

st.title("📊 Precificação P1")
st.markdown("Use esta ferramenta para calcular a **Perda** e o **CPC Alvo** com base nos dados da operação.")

st.divider()

# Layout: colunas para inputs lado a lado
col1, col2, col3 = st.columns(3)

with col1:
    solicitacoes_p1 = st.number_input("Solicitações Interstitial ou Offerwall", min_value=0)
with col2:
    cliques_p1 = st.number_input("Cliques P1", min_value=0)
with col3:
    cliques_p2 = st.number_input("Cliques P2", min_value=0)

col4, col5 = st.columns(2)
with col4:
    cpa_medio = st.number_input("CPA Médio (R$)", min_value=0.0, format="%.2f")
with col5:
    roas_meta = st.number_input("Meta de ROAS (%)", min_value=0.0, format="%.2f")

st.divider()

# Botão de cálculo
if st.button("🔍 Calcular"):
    if solicitacoes_p1 == 0:
        st.error("⚠️ As solicitações não podem ser zero.")
    else:
        perda = (solicitacoes_p1 - (cliques_p1 + cliques_p2)) / solicitacoes_p1
        perda = max(perda, 0)

        roas_decimal = roas_meta / 100
        cpc_alvo = cpa_medio * roas_decimal * (1 + perda)

        perda_formatada = f"{perda:.2%}"
        cpc_formatado = f"R$ {cpc_alvo:.4f}"

        st.success(f"🔻 Perda calculada: {perda_formatada}")
        st.success(f"🎯 CPC Alvo: {cpc_formatado}")

        resultado_texto = f"Perda: {perda_formatada}\nCPC Alvo: {cpc_formatado}"

        # Botão para copiar com clipboard
        components.html(f"""
            <button onclick="navigator.clipboard.writeText(`{resultado_texto}`)" 
                    style="margin-top: 10px; padding: 0.75em 1.5em; 
                           background-color: #3b82f6; color: white;
                           border: none; border-radius: 6px; 
                           font-weight: 600; cursor: pointer;">
                📋 Copiar Resultado
            </button>
        """, height=50)
