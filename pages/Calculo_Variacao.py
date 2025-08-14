import streamlit as st

st.set_page_config(page_title="Cálculo de Variação")

st.title("📊 Cálculo de Variação de Regra")
st.markdown("Escolha se deseja **aumentar ou diminuir** a regra e veja os valores recomendados com base em variações leves, médias e agressivas.")

st.divider()

# Entradas
col1, col2 = st.columns(2)
with col1:
    direcao = st.radio("Deseja:", ["Aumentar", "Diminuir"])
with col2:
    valor_atual = st.number_input("Valor atual da regra (R$)", min_value=0.0, format="%.2f")

st.divider()

# Botão de cálculo
if st.button("📈 Calcular Variações"):
    # Intervalos percentuais
    variacoes = {
        "Leve (5%–10%)": (0.05, 0.10),
        "Média (10%–20%)": (0.10, 0.20),
        "Agressiva (20%–30%)": (0.20, 0.30),
    }

    st.subheader(f"📋 Variações para {direcao.lower()} a regra:")

    for label, (min_var, max_var) in variacoes.items():
        if direcao == "Aumentar":
            maior = valor_atual * (1 + min_var)
            menor = valor_atual * (1 + max_var)
        else:
            maior = valor_atual * (1 - min_var)
            menor = valor_atual * (1 - max_var)

        st.markdown(f"""
        #### {label}  
        {maior:.2f} a {menor:.2f}
        """)
