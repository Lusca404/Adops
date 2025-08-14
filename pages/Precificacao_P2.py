import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Precificação P2")

st.title("📈 Precificação P2")
st.markdown("Use esta ferramenta para calcular a **Perda de Usuário** e o **CPC Corrigido** com base nos dados da operação.")

st.divider()

# Inputs divididos
col1, col2, col3 = st.columns(3)

with col1:
    solicitacoes = st.number_input("Solicitações de Anúncios", min_value=0)
with col2:
    cobertura = st.number_input("Cobertura (%)", min_value=0.0, format="%.2f")
with col3:
    impressoes = st.number_input("Impressões", min_value=0)

col4, col5 = st.columns(2)
with col4:
    receita = st.number_input("Receita (R$)", min_value=0.0, format="%.2f")
with col5:
    cliques = st.number_input("Cliques", min_value=0)

st.divider()

# Botão para calcular
if st.button("🔍 Calcular"):
    perda_usuario = (solicitacoes * (cobertura / 100)) - impressoes
    perda_usuario = max(perda_usuario, 0)

    denominador = cliques + perda_usuario
    if denominador == 0:
        st.error("⚠️ Cliques + Perda de Usuário não pode ser zero.")
    else:
        cpc_corrigido = receita / denominador

        perda_formatada = f"{perda_usuario:.0f}"
        cpc_formatado = f"R$ {cpc_corrigido:.4f}"

        st.success(f"🔻 Perda de Usuário: {perda_formatada}")
        st.success(f"🎯 CPC Corrigido: {cpc_formatado}")

        resultado = f"Perda de Usuário: {perda_formatada}\nCPC Corrigido: {cpc_formatado}"

        # Botão copiar
        components.html(f"""
            <button onclick="navigator.clipboard.writeText(`{resultado}`)" 
                    style="margin-top: 10px; padding: 0.75em 1.5em; 
                           background-color: #3b82f6; color: white;
                           border: none; border-radius: 6px; 
                           font-weight: 600; cursor: pointer;">
                📋 Copiar Resultado
            </button>
        """, height=50)
