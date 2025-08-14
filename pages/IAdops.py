import streamlit as st
import pandas as pd

st.set_page_config(page_title="IAdops")

st.title("🤖 IAdops – Análise Inteligente via GAM CSV")
st.markdown("Faça upload de um **CSV extraído do GAM**, preencha os dados necessários e o sistema irá sugerir ações para os blocos `interstitial` e `mob_top`.")

st.divider()

# Inputs do usuário
cliques_p2 = st.number_input("🔘 Cliques P2", min_value=0, format="%d")
cpa_medio = st.number_input("💰 CPA Médio (US$)", min_value=0.0, format="%.4f")
roas_input = st.number_input("🎯 ROAS desejado (%)", min_value=0.0, format="%.2f")

# Upload CSV
arquivo = st.file_uploader("📁 Enviar CSV do GAM", type=["csv"])

if arquivo:
    try:
        df = pd.read_csv(arquivo, sep=";")

        # Normalizar nomes das colunas esperadas
        df.columns = [col.strip() for col in df.columns]

        # Identificar as linhas dos blocos
        interstitial = df[df['Bloco de anúncios'].str.contains("interstitial", case=False)]
        mob_top = df[df['Bloco de anúncios'].str.contains("mob_top", case=False)]

        if interstitial.empty or mob_top.empty:
            st.error("❌ Não foram encontradas linhas com 'interstitial' e 'mob_top'.")
        else:
            st.success("✅ Blocos identificados no CSV!")

            # --- INTERSTITIAL ---

            linha_i = interstitial.iloc[0]
            solicitacoes_i = int(linha_i["Solicitações de anúncios do Ad Exchange"])
            cliques_i = int(linha_i["Cliques do Ad Exchange"])
            taxa_i = float(str(linha_i["Taxa de correspondência do Ad Exchange"]).replace('%', '').replace(',', '.'))

            perda = (solicitacoes_i - (cliques_i + cliques_p2)) / solicitacoes_i if solicitacoes_i > 0 else 0
            perda = max(perda, 0)

            roas_decimal = roas_input / 100
            cpc_alvo = cpa_medio * roas_decimal * (1 + perda)

            # Análise do interstitial
            if taxa_i >= 95:
                acao_i = "✅ Aumentar é uma boa opção"
            elif 85 <= taxa_i < 95:
                acao_i = "✔️ Pode aumentar"
            elif 80 <= taxa_i < 85:
                acao_i = "⚖️ Manter ou diminuir"
            else:
                acao_i = "🔽 Diminuir é a melhor opção"

            # --- MOB TOP ---

            linha_t = mob_top.iloc[0]
            taxa_t = float(str(linha_t["Taxa de correspondência do Ad Exchange"]).replace('%', '').replace(',', '.'))

            if taxa_t <= 30:
                acao_t = "🔽 Diminuir"
            elif 35 <= taxa_t <= 40:
                acao_t = "⚖️ Manter"
            elif 40 < taxa_t < 70:
                acao_t = "✅ Aumentar é uma boa opção"
            else:
                acao_t = "🚀 Aumentar é a melhor opção"

            # --- Exibir resultados

            st.subheader("📊 Resultados:")

            st.markdown(f"""
            ### 🎯 Interstitial  
            - Solicitações: `{solicitacoes_i}`  
            - Cliques P1: `{cliques_i}`  
            - Cliques P2: `{cliques_p2}`  
            - **Perda estimada:** `{perda:.2%}`  
            - **CPC Alvo calculado:** `US$ {cpc_alvo:.4f}`  
            - **Taxa:** `{taxa_i:.2f}%`  
            - 👉 **Ação sugerida:** **{acao_i}**
            """)

            st.divider()

            st.markdown(f"""
            ### 📱 Mob Top  
            - **Taxa:** `{taxa_t:.2f}%`  
            - 👉 **Ação sugerida:** **{acao_t}**
            """)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
