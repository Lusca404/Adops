# pages/IAdops.py
import streamlit as st
import pandas as pd
import re, unicodedata, io
import math

st.set_page_config(page_title="IAdops")

st.title("🤖 IAdops – Overview P1 + P2")
st.markdown(
    "Envie os relatórios **P1** e **P2** do GAM. Exibimos **P1** e **P2** separados, "
    "calculamos o **CPC Alvo (P1)** e o **CPC Corrigido (P2 – rewarded/offerwall)**."
)
st.divider()

# ===================== Helpers =====================

def normalize_text(s: str) -> str:
    s = str(s).replace("\u00A0", " ").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def to_number(x):
    """Conversor pt-BR/en-US robusto (para %/CPC etc.)."""
    s = str(x).strip().replace("\u00A0", " ")
    s = s.replace("US$", "").replace("R$", "").replace("%", "").strip()
    s = s.replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        if "," in s:
            s = s.replace(".", "")
            s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return float("nan")

def to_count(x):
    """CONTAGENS (Solicitações/Cliques/Impressões) — entende '.' como milhar."""
    s = str(x).strip().replace("\u00A0", " ")
    s = s.replace("US$", "").replace("R$", "").replace("%", "")
    s = s.replace(" ", "")
    s = re.sub(r"[^0-9,\.]", "", s)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "")
            s = s.split(",")[0]
        else:
            s = s.replace(",", "")
            s = s.split(".")[0]
    elif "," in s:
        s = s.split(",")[0].replace(".", "")
    elif "." in s:
        if re.match(r"^\d{1,3}(\.\d{3})+$", s):
            s = s.replace(".", "")
        else:
            s = s.split(".")[0]
    s = s or "0"
    try:
        return int(s)
    except Exception:
        try:
            return int(float(s))
        except Exception:
            return 0

def detect_header_and_sep(raw: str):
    """Identifica linha de cabeçalho real e separador (; , \t)."""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    keys = [
        "bloco de anúncios","bloco de anuncios",
        "cliques do ad exchange","ctr do ad exchange",
        "taxa de correspondência","taxa de correspondencia",
        "solicitações de anúncios","solicitacoes de anuncios",
        "impressões do ad exchange","receita do ad exchange",
        "cpc do ad exchange","ecpm medio do ad exchange"
    ]
    header_idx = 0
    for i, ln in enumerate(lines[:60]):
        ln_norm = unicodedata.normalize("NFKD", ln).lower()
        if sum(1 for k in keys if k in ln_norm) >= 2:
            header_idx = i
            break
    best_sep, max_cols = ";", 0
    for sep in [";", ",", "\t"]:
        ncols = len(lines[header_idx].split(sep))
        if ncols > max_cols:
            best_sep, max_cols = sep, ncols
    return header_idx, best_sep

def read_gam_csv(file):
    raw = file.getvalue().decode("utf-8-sig", errors="ignore")
    h, sep = detect_header_and_sep(raw)
    return pd.read_csv(io.StringIO(raw), sep=sep, header=h)

def find_col(df, parts):
    for col in df.columns:
        if all(p in normalize_text(col) for p in parts):
            return col
    return None

def map_cols(df):
    """Mapeia colunas importantes (algumas podem não existir no P2)."""
    return {
        "bloco":        find_col(df, ["bloco","anuncios"]) or find_col(df, ["bloco","anuncio"]),
        "solicitacoes": find_col(df, ["solicitacoes"]),
        "cliques":      find_col(df, ["cliques"]),
        "ctr":          find_col(df, ["ctr"]),  # opcional no P2
        "taxa":         find_col(df, ["taxa","correspondencia"]),
        "cpc":          find_col(df, ["cpc"]),  # opcional no P2
        "impressoes":   find_col(df, ["impressoes"]),
        "receita":      find_col(df, ["receita"]),
    }

def get_total_or_sum(df, col_name, count=True):
    """Usa linha 'Total' se existir; senão, soma linhas."""
    conv = to_count if count else to_number
    first_col = df.columns[0]
    is_total = df[first_col].astype(str).str.strip().str.lower().eq("total")
    if is_total.any():
        return conv(df.loc[is_total, col_name].iloc[0])
    return df.loc[~is_total, col_name].apply(conv).sum()

def get_row(df, col_bloco, token):
    """Retorna a primeira linha do bloco (ignorando 'Total')."""
    first_col = df.columns[0]
    dfx = df.loc[df[first_col].astype(str).str.strip().str.lower() != "total"]
    dfx = dfx.dropna(subset=[col_bloco])
    m = dfx[col_bloco].astype(str).str.contains(token, case=False, na=False)
    return dfx[m].iloc[0] if m.any() else None

def badge(text, color="#22c55e"):
    return f"""<span style="display:inline-block;padding:.22rem .6rem;border-radius:12px;
    background:{color};color:#0b1120;font-weight:700;opacity:.95">{text}</span>"""

def fmt_money(val):
    return "—" if (val is None or pd.isna(val)) else f"US$ {val:.4f}"

def fmt_pct(val):
    return "—" if (val is None or pd.isna(val)) else f"{val:.2f}%"

# ===================== Inputs =====================
col_in1, col_in2 = st.columns(2)
with col_in1:
    cpa_medio = st.number_input("💰 CPA Médio (US$)", min_value=0.0, value=0.0, format="%.4f")
with col_in2:
    roas_meta = st.number_input("🎯 ROAS desejado (%)", min_value=0.0, value=0.0, format="%.2f")

c1, c2 = st.columns(2)
with c1:
    file_p1 = st.file_uploader("📁 Enviar CSV **P1**", type=["csv"])
with c2:
    file_p2 = st.file_uploader("📁 Enviar CSV **P2**", type=["csv"])

if file_p1 and file_p2:
    try:
        # --------- P1 ---------
        p1 = read_gam_csv(file_p1)
        m1 = map_cols(p1)
        need1 = ["bloco","solicitacoes","cliques","ctr","taxa","cpc"]
        miss1 = [k for k in need1 if not m1[k]]
        if miss1:
            st.error("❌ P1: faltam colunas: " + ", ".join(miss1))
            st.stop()

        p1["_sol"]  = p1[m1["solicitacoes"]].apply(to_count)
        p1["_cli"]  = p1[m1["cliques"]].apply(to_count)
        p1["_ctr"]  = p1[m1["ctr"]].apply(to_number)          # %
        p1["_taxa"] = p1[m1["taxa"]].apply(to_number)         # %
        p1["_cpc"]  = p1[m1["cpc"]].apply(to_number)          # US$

        inter_p1 = get_row(p1, m1["bloco"], "interstitial")
        if inter_p1 is None:
            inter_p1 = get_row(p1, m1["bloco"], "offerwall")
        mob_p1   = get_row(p1, m1["bloco"], "mob_top")
        cliques_p1_total = int(get_total_or_sum(p1, m1["cliques"], count=True))

        solicit_i  = int(inter_p1["_sol"]) if inter_p1 is not None else 0
        ctr_i      = float(inter_p1["_ctr"]) if inter_p1 is not None else float("nan")
        taxa_i     = float(inter_p1["_taxa"]) if inter_p1 is not None else float("nan")
        cpc_i      = float(inter_p1["_cpc"]) if inter_p1 is not None else float("nan")

        solicit_m1 = int(mob_p1["_sol"]) if mob_p1 is not None else 0
        ctr_mob1   = float(mob_p1["_ctr"]) if mob_p1 is not None else float("nan")
        taxa_mob1  = float(mob_p1["_taxa"]) if mob_p1 is not None else float("nan")
        cpc_mob1   = float(mob_p1["_cpc"]) if mob_p1 is not None else float("nan")

        # --------- P2 ---------
        p2 = read_gam_csv(file_p2)
        m2 = map_cols(p2)
        need2 = ["bloco","solicitacoes","cliques","impressoes","taxa","receita"]  # cpc/ctr opcionais
        miss2 = [k for k in need2 if not m2[k]]
        if miss2:
            st.error("❌ P2: faltam colunas: " + ", ".join(miss2))
            st.stop()

        p2["_sol"]  = p2[m2["solicitacoes"]].apply(to_count)
        p2["_cli"]  = p2[m2["cliques"]].apply(to_count)
        p2["_imp"]  = p2[m2["impressoes"]].apply(to_count)
        p2["_taxa"] = p2[m2["taxa"]].apply(to_number)         # %
        p2["_rec"]  = p2[m2["receita"]].apply(to_number)      # US$
        if m2["cpc"]:
            p2["_cpc"] = p2[m2["cpc"]].apply(to_number)
        if m2["ctr"]:
            p2["_ctr"] = p2[m2["ctr"]].apply(to_number)

        cliques_p2_total = int(get_total_or_sum(p2, m2["cliques"], count=True))

        mob_p2 = get_row(p2, m2["bloco"], "mob_top")

        # guardamos o CPC atual do mob_top P2 para usar depois no comparativo
        cpc_mob2_val = float("nan")
        if mob_p2 is not None and m2["cpc"] and "_cpc" in mob_p2.index and pd.notna(mob_p2.get("_cpc")):
            cpc_mob2_val = to_number(mob_p2.get("_cpc"))

        rewarded, rewarded_name = None, None
        for tk in ["rewarded","reward","offerwall","offer_wall","offwall"]:
            rewarded = get_row(p2, m2["bloco"], tk)
            if rewarded is not None:
                rewarded_name = tk
                break

        # ===================== OVERVIEW =====================

        # ---------- P1 ----------
        st.subheader("📘 P1")

        r1c1, r1c2, r1c3 = st.columns(3)
        r1c1.metric("Solicitações (Interstitial/Offerwall)", f"{solicit_i:,}".replace(",", "."))
        r1c2.metric("Cliques P1 (Total)", f"{cliques_p1_total:,}".replace(",", "."))
        r1c3.metric("CPC Atual (Interstitial)", fmt_money(cpc_i))

        r2c1, r2c2, r2c3 = st.columns(3)
        r2c1.metric("Solicitações (mob_top)", f"{solicit_m1:,}".replace(",", "."))
        r2c2.metric("CPC Atual (mob_top)", fmt_money(cpc_mob1))
        r2c3.metric("CTR (Interstitial)", fmt_pct(ctr_i))

        st.markdown("&nbsp;")
        if pd.notna(taxa_i):
            cor_i = "#22c55e" if taxa_i >= 40 else "#f59e0b"
            st.markdown(f"**Taxa Interstitial/Offerwall:** {badge(f'{taxa_i:.2f}%', cor_i)}", unsafe_allow_html=True)
        else:
            st.markdown("**Taxa Interstitial/Offerwall:** —")
        if pd.notna(taxa_mob1):
            cor_m1 = "#22c55e" if taxa_mob1 >= 40 else "#f59e0b"
            st.markdown(f"**Taxa mob_top (P1):** {badge(f'{taxa_mob1:.2f}%', cor_m1)}", unsafe_allow_html=True)
        else:
            st.markdown("**Taxa mob_top (P1):** —")
        if pd.notna(ctr_mob1):
            st.markdown(f"**CTR (mob_top P1):** {badge(f'{ctr_mob1:.2f}%', '#38bdf8')}", unsafe_allow_html=True)

        st.divider()

        # ---------- P2 ----------
        st.subheader("📗 P2")

        p2c1, p2c2, p2c3 = st.columns(3)
        p2c1.metric("Cliques P2 (Total)", f"{cliques_p2_total:,}".replace(",", "."))

        if mob_p2 is not None:
            mob_p2_solic = int(mob_p2["_sol"]) if pd.notna(mob_p2["_sol"]) else 0
            p2c2.metric("Solicitações (mob_top)", f"{mob_p2_solic:,}".replace(",", "."))
            p2c3.metric("CPC Atual (mob_top)", fmt_money(cpc_mob2_val))
        else:
            p2c2.metric("Solicitações (mob_top)", "—")
            p2c3.metric("CPC Atual (mob_top)", "—")

        p2d1, p2d2, p2d3 = st.columns(3)
        if mob_p2 is not None:
            ctr_mob2_val = to_number(mob_p2.get("_ctr")) if (m2["ctr"] and "_ctr" in mob_p2.index) else float("nan")
            p2d1.metric("CTR (mob_top)", fmt_pct(ctr_mob2_val))
            taxa_mob2_val = to_number(mob_p2["_taxa"])
            cor_m2 = "#22c55e" if taxa_mob2_val >= 40 else "#f59e0b"
            st.markdown(f"**Taxa mob_top (P2):** {badge(f'{taxa_mob2_val:.2f}%', cor_m2)}", unsafe_allow_html=True)
        else:
            p2d1.metric("CTR (mob_top)", "—")

        if rewarded is not None:
            st.markdown("&nbsp;")
            rw1, rw2, rw3 = st.columns(3)
            rw_solic = int(rewarded["_sol"]) if pd.notna(rewarded["_sol"]) else 0
            rw_cli   = int(rewarded["_cli"]) if pd.notna(rewarded["_cli"]) else 0
            rw1.metric(f"Solicitações ({rewarded_name})", f"{rw_solic:,}".replace(",", "."))
            rw2.metric(f"Cliques ({rewarded_name})", f"{rw_cli:,}".replace(",", "."))
            cpc_rw_val = to_number(rewarded.get("_cpc")) if (m2["cpc"] and "_cpc" in rewarded.index and pd.notna(rewarded.get("_cpc"))) else float("nan")
            rw3.metric(f"CPC Atual ({rewarded_name})", fmt_money(cpc_rw_val))

            rw4, rw5, rw6 = st.columns(3)
            rw_imp = int(rewarded["_imp"]) if pd.notna(rewarded["_imp"]) else 0
            rw4.metric(f"Impressões ({rewarded_name})", f"{rw_imp:,}".replace(",", "."))
            ctr_rw_val = to_number(rewarded.get("_ctr")) if (m2["ctr"] and "_ctr" in rewarded.index) else float("nan")
            rw5.metric(f"CTR ({rewarded_name})", fmt_pct(ctr_rw_val))
            taxa_rw_val = to_number(rewarded["_taxa"])
            st.markdown(f"**Taxa {rewarded_name}:** {badge(f'{taxa_rw_val:.2f}%')}", unsafe_allow_html=True)
        else:
            st.info("P2 não contém rewarded/offerwall (ok).")

        # ===================== CÁLCULO: CPC Alvo (P1) =====================
        st.divider()
        st.subheader("🎯 CPC Alvo (P1)")

        if solicit_i > 0:
            perda = (solicit_i - (cliques_p1_total + cliques_p2_total)) / solicit_i
            perda = max(perda, 0.0)
        else:
            perda = 0.0

        roas_dec = (roas_meta or 0.0) / 100.0
        cpc_alvo = (cpa_medio or 0.0) * roas_dec * (1.0 + perda)

        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Perda (P1)", f"{perda:.2%}")
        cc2.metric("CPC Alvo (P1)", fmt_money(cpc_alvo))
        cc3.metric("ROAS x CPA", f"{roas_meta:.2f}%  •  US$ {cpa_medio:.4f}")

        def cmp_badge_greater_equal(a, b):
            if pd.isna(a) or pd.isna(b):
                return badge("—", "#94a3b8")
            return badge("Bom (≥ alvo)", "#22c55e") if a >= b else badge("Abaixo do alvo", "#ef4444")

        st.markdown("&nbsp;")
        st.markdown(
            f"**Interstitial/Offerwall** — CPC atual: {fmt_money(cpc_i)} • CPC alvo: {fmt_money(cpc_alvo)} {cmp_badge_greater_equal(cpc_i, cpc_alvo)}",
            unsafe_allow_html=True
        )
        st.markdown(
            f"**mob_top** — CPC atual: {fmt_money(cpc_mob1)} • CPC alvo: {fmt_money(cpc_alvo)} {cmp_badge_greater_equal(cpc_mob1, cpc_alvo)}",
            unsafe_allow_html=True
        )

        # ===================== CÁLCULO: CPC Corrigido (P2) =====================
        st.divider()
        st.subheader("🧮 CPC Corrigido (P2 – rewarded/offerwall)")

        if rewarded is None:
            st.info("Não há linha de rewarded/offerwall na P2. Envie um CSV que contenha esse bloco para calcular o CPC Corrigido.")
        else:
            # Perda de Usuário = (Solicitações * Cobertura) - Impressões
            rw_sol   = to_count(rewarded["_sol"])
            rw_taxa  = to_number(rewarded["_taxa"]) / 100.0  # cobertura em decimal
            rw_imp   = to_count(rewarded["_imp"])
            rw_cli   = to_count(rewarded["_cli"])
            rw_rec   = to_number(rewarded["_rec"])

            perda_usuario = (rw_sol * rw_taxa) - rw_imp
            # evita negativo:
            perda_usuario = max(perda_usuario, 0.0)

            denom = rw_cli + perda_usuario
            cpc_corrigido = (rw_rec / denom) if denom > 0 else float("nan")

            # Comparar com CPC do mob_top (P2)
            status_badge = badge("—", "#94a3b8")
            if not pd.isna(cpc_corrigido) and not pd.isna(cpc_mob2_val):
                if cpc_corrigido >= cpc_mob2_val:
                    status_badge = badge("Bom (corrigido ≥ mob_top)", "#22c55e")
                else:
                    status_badge = badge("Abaixo (corrigido < mob_top)", "#ef4444")

            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("Perda de Usuário", f"{int(round(perda_usuario)):,}".replace(",", "."))
            pc2.metric("CPC Corrigido", fmt_money(cpc_corrigido))
            pc3.metric("CPC Atual (mob_top P2)", fmt_money(cpc_mob2_val))

            st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)

            with st.expander("Como calculamos (P2)?"):
                st.markdown(
                    "- **Perda de Usuário** = (Solicitações × Cobertura) − Impressões\n"
                    "- **CPC Corrigido** = Receita ÷ (Cliques + Perda de Usuário)\n"
                    "- Status: **Bom** se CPC Corrigido ≥ CPC atual do **mob_top** da P2."
                )

        with st.expander("Mapeamento de colunas"):
            st.write({"P1": m1, "P2": m2})

    except Exception as e:
        st.error(f"Erro ao processar os arquivos: {e}")
