import streamlit as st
import pandas as pd
import re, unicodedata, io

st.set_page_config(page_title="IAdops")

st.title("🤖 IAdops – Análise Inteligente via GAM CSV")
st.markdown(
    "Faça upload de um **CSV do GAM**. Informe **Cliques P2**, **CPA Médio** e **ROAS**. "
    "O sistema localizará **interstitial** e **mob_top**, calculará **Perda** e **CPC Alvo** (no interstitial) "
    "e sugerirá a ação conforme a **Taxa de correspondência**."
)
st.divider()

# ================= Helpers =================
def normalize_text(s: str) -> str:
    s = str(s).replace("\u00A0", " ").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def to_number(x):
    s = str(x).replace("\u00A0", " ")
    s = s.replace("US$", "").replace("R$", "").replace("%", "").strip()
    s = s.replace(".", "").replace(",", ".")  # pt-BR → float
    try:
        return float(s)
    except Exception:
        return float("nan")

def detect_header_and_sep(raw: str):
    lines = [ln for ln in raw.splitlines() if ln.strip() != ""]
    keys = ["bloco de anúncios", "bloco de anuncios", "cliques do ad exchange",
            "taxa de correspondência", "taxa de correspondencia", "solicitações de anúncios"]
    header_idx = 0
    for i, ln in enumerate(lines[:50]):
        ln_norm = unicodedata.normalize("NFKD", ln).lower()
        if sum(1 for k in keys if k in ln_norm) >= 2:
            header_idx = i
            break
    candidates = [";", ",", "\t"]
    best_sep, max_cols = ";", 0
    for sep in candidates:
        ncols = len(lines[header_idx].split(sep))
        if ncols > max_cols:
            best_sep, max_cols = sep, ncols
    return header_idx, best_sep

def read_gam_csv(file):
    raw = file.getvalue().decode("utf-8-sig", errors="ignore")
    header_idx, sep = detect_header_and_sep(raw)
    df = pd.read_csv(io.StringIO(raw), sep=sep, header=header_idx)
    # não descartamos "Total" ainda; vamos usar para cliques P1
    return df

def find_col(df, parts: list[str]):
    for col in df.columns:
        norm = normalize_text(col)
        if all(p in norm for p in parts):
            return col
    return None

# ================= Inputs =================
col_a, col_b, col_c = st.columns(3)
with col_a:
    cliques_p2 = st.number_input("🔘 Cliques P2", min_value=0, format="%d")
with col_b:
    cpa_medio = st.number_input("💰 CPA Médio (US$)", min_value=0.0, format="%.4f")
with col_c:
    roas_input = st.number_input("🎯 ROAS desejado (%)", min_value=0.0, format="%.2f")

arquivo = st.file_uploader("📁 Enviar CSV do GAM", type=["csv"])

if arquivo:
    try:
        df = read_gam_csv(arquivo)
        original_cols = df.columns.tolist()
        first_col = df.columns[0]

        # Mapear colunas (robusto a variações do GAM)
        col_bloco = find_col(df, ["bloco", "anuncios"]) or find_col(df, ["bloco", "anuncio"])
        col_solic = find_col(df, ["solicitacoes"]) or find_col(df, ["solicitacoes", "ad", "exchange"])
        col_cliques = find_col(df, ["cliques"]) or find_col(df, ["cliques", "ad", "exchange"])
        col_taxa = find_col(df, ["taxa", "correspondencia"]) or find_col(df, ["taxa", "correspondencia", "exchange"])
        col_cpc = find_col(df, ["cpc"]) or find_col(df, ["cpc", "exchange"])

        missing = []
        if not col_bloco:   missing.append("Bloco de anúncios")
        if not col_solic:   missing.append("Solicitações de anúncios")
        if not col_cliques: missing.append("Cliques do Ad Exchange")
        if not col_taxa:    missing.append("Taxa de correspondência do Ad Exchange")
        if not col_cpc:     missing.append("CPC do Ad Exchange (US$)")
        if missing:
            st.error("❌ Não encontrei as colunas: " + ", ".join(missing))
            with st.expander("Cabeçalhos detectados"):
                st.code("\n".join(original_cols))
            st.stop()

        # Flags e conversões
        is_total = df[first_col].astype(str).str.strip().str.lower().eq("total")
        df["_solicitacoes"] = df[col_solic].apply(to_number)
        df["_cliques"] = df[col_cliques].apply(to_number)
        df["_taxa"] = df[col_taxa].apply(to_number)     # em %
        df["_cpc"] = df[col_cpc].apply(to_number)       # em US$

        # Cliques P1 = linha "Total" (se houver) ou soma
        if is_total.any():
            cliques_p1_total = int(round(df.loc[is_total, "_cliques"].iloc[0]))
        else:
            cliques_p1_total = int(round(df.loc[~is_total, "_cliques"].sum()))

        # Trabalhar blocos sem a linha Total
        dfx = df.loc[~is_total].dropna(subset=[col_bloco])

        mask_inter = dfx[col_bloco].astype(str).str.contains("interstitial", case=False, na=False)
        mask_mobtop = dfx[col_bloco].astype(str).str.contains("mob_top", case=False, na=False)

        if not mask_inter.any() or not mask_mobtop.any():
            st.error("❌ Não encontrei linhas contendo 'interstitial' e/ou 'mob_top' na coluna de bloco.")
            with st.expander("Exemplos da coluna de Bloco"):
                st.write(dfx[col_bloco].head(10))
            st.stop()

        # ---------- INTERSTITIAL ----------
        li = dfx[mask_inter].iloc[0]
        solicit_i = int(round(li["_solicitacoes"])) if pd.notna(li["_solicitacoes"]) else 0
        taxa_i = float(li["_taxa"]) if pd.notna(li["_taxa"]) else 0.0
        cpc_inter = float(li["_cpc"]) if pd.notna(li["_cpc"]) else float("nan")

        # Perda com Cliques P1 = linha Total (pedido seu)
        perda = 0.0
        if solicit_i > 0:
            perda = (solicit_i - (cliques_p1_total + cliques_p2)) / solicit_i
            perda = max(perda, 0.0)

        roas_dec = roas_input / 100 if roas_input else 0.0
        cpc_alvo = cpa_medio * roas_dec * (1 + perda)

        if taxa_i >= 95:
            acao_i = "✅ Aumentar é uma boa opção"
        elif 85 <= taxa_i < 95:
            acao_i = "✔️ Pode aumentar"
        elif 80 <= taxa_i < 85:
            acao_i = "⚖️ Manter ou diminuir"
        else:
            acao_i = "🔽 Diminuir é a melhor opção"

        # ---------- MOB_TOP ----------
        lt = dfx[mask_mobtop].iloc[0]
        taxa_t = float(lt["_taxa"]) if pd.notna(lt["_taxa"]) else 0.0
        cpc_mob = float(lt["_cpc"]) if pd.notna(lt["_cpc"]) else float("nan")

        if taxa_t <= 30:
            acao_t = "🔽 Diminuir"
        elif 35 <= taxa_t <= 40:
            acao_t = "⚖️ Manter"
        elif 40 < taxa_t < 70:
            acao_t = "✅ Aumentar é uma boa opção"
        else:
            acao_t = "🚀 Aumentar é a melhor opção"

        # ---------- SAÍDA ----------
        st.subheader("📊 Resultados")
        st.markdown(f"""
### 🎯 Interstitial
- **Solicitações**: `{solicit_i}`
- **Cliques P1 (linha Total)**: `{cliques_p1_total}`
- **Cliques P2 (input)**: `{cliques_p2}`
- **Perda estimada**: `{perda:.2%}`
- **CPC Atual (US$)**: `{cpc_inter:.4f}`
- **CPC Alvo calculado (US$)**: `{cpc_alvo:.4f}`
- **Taxa de correspondência**: `{taxa_i:.2f}%`
- 👉 **Ação sugerida**: **{acao_i}**
""")

        st.divider()
        st.markdown(f"""
### 📱 mob_top
- **CPC Atual (US$)**: `{cpc_mob:.4f}`
- **Taxa de correspondência**: `{taxa_t:.2f}%`
- 👉 **Ação sugerida**: **{acao_t}**
""")

        with st.expander("Colunas detectadas e mapeadas"):
            st.write({
                "bloco": col_bloco,
                "solicitações": col_solic,
                "cliques": col_cliques,
                "taxa": col_taxa,
                "cpc": col_cpc
            })

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
