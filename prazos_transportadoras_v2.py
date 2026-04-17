import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA INTERFACE
st.set_page_config(page_title="Consulta de Prazos - Transportadoras", page_icon="🚚", layout="wide")

st.title("🚚 Portal de Consulta de Prazos")
st.markdown("---")

# 2. UPLOAD DA PLANILHA (substituindo caminho fixo)
NOME_ABA = "Prazos Transportadoras"

@st.cache_data
def carregar_dados(arquivo, aba):
    try:
        df = pd.read_excel(arquivo, sheet_name=aba)
        # Padroniza todas as colunas de texto para maiúsculo e sem espaços extras
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar a planilha: {e}")
        return None

# Sidebar com upload
with st.sidebar:
    st.header("📂 Carregar Planilha")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo Excel (.xlsx)",
        type=["xlsx"],
        help="A planilha deve conter a aba 'Prazos Transportadoras'"
    )
    st.markdown("---")
    st.caption("Colunas esperadas:\n- TRANSPORTADORA\n- UF_ORIGEM\n- CIDADE_DESTINO\n- UF_DESTINO\n- PRAZO_ENTREGA_DIAS")

# 3. CARREGAMENTO DOS DADOS
if uploaded_file is not None:
    df_base = carregar_dados(uploaded_file, NOME_ABA)

    if df_base is not None:

        # 4. CAMPOS DE BUSCA
        st.subheader("🔍 Filtros de Busca")
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            transp_input = st.text_input("Transportadora", "").strip().upper()
        with col2:
            uf_origem_input = st.text_input("UF Origem", "").strip().upper()
        with col3:
            cidade_input = st.text_input("Cidade Destino", "").strip().upper()
        with col4:
            uf_destino_input = st.text_input("UF Destino", "").strip().upper() 

        # 5. NOMES DAS COLUNASd
        COL_TRANSP     = 'TRANSPORTADORA'
        COL_CIDADE     = 'CIDADE_DESTINO'
        COL_UF_ORIGEM  = 'UF_ORIGEM'
        COL_UF_DESTINO = 'UF_DESTINO'
        COL_PRAZO      = 'PRAZO_ENTREGA_DIAS'

        # 6. FILTRO CORRIGIDO — UF ORIGEM e UF DESTINO são campos separados
        if transp_input or uf_origem_input or cidade_input or uf_destino_input:
            try:
                mask = (
                    df_base[COL_TRANSP].str.contains(transp_input, case=False, na=False) &
                    df_base[COL_UF_ORIGEM].str.contains(uf_origem_input, case=False, na=False) &
                    df_base[COL_UF_DESTINO].str.contains(uf_destino_input, case=False, na=False) &
                    df_base[COL_CIDADE].str.contains(cidade_input, case=False, na=False)
                )

                resultado = df_base.loc[
                    mask,
                    [COL_TRANSP, COL_UF_ORIGEM, COL_CIDADE, COL_UF_DESTINO, COL_PRAZO]
                ].drop_duplicates().reset_index(drop=True)

                if not resultado.empty:
                    st.success(f"✅ {len(resultado)} registro(s) encontrado(s):")

                    # Métricas resumidas
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Registros encontrados", len(resultado))
                    m2.metric("Prazo mínimo (dias)", int(resultado[COL_PRAZO].min()))
                    m3.metric("Prazo máximo (dias)", int(resultado[COL_PRAZO].max()))

                    st.dataframe(
                        resultado,
                        use_container_width=True,
                        hide_index=True
                    )

                    # GRÁFICO 1 — Prazo médio por transportadora (só aparece quando há resultado)
                    st.markdown("#### 📊 Prazo Médio por Transportadora")
                    prazo_medio = (
                        resultado.groupby(COL_TRANSP)[COL_PRAZO]
                        .mean()
                        .round(1)
                        .reset_index()
                        .sort_values(COL_PRAZO)
                        .rename(columns={COL_TRANSP: "Transportadora", COL_PRAZO: "Prazo Médio (dias)"})
                    )
                    fig_bar = px.bar(
                        prazo_medio,
                        x="Prazo Médio (dias)",
                        y="Transportadora",
                        orientation="h",
                        text="Prazo Médio (dias)",
                        color="Prazo Médio (dias)",
                        color_continuous_scale="RdYlGn_r",  # verde = rápido, vermelho = lento
                    )
                    fig_bar.update_traces(textposition="outside")
                    fig_bar.update_layout(
                        coloraxis_showscale=False,
                        yaxis_title=None,
                        xaxis_title="Dias",
                        height=max(300, len(prazo_medio) * 45),
                        margin=dict(l=10, r=40, t=20, b=20),
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                    # Download dos resultados
                    csv = resultado.to_csv(index=False, sep=";", encoding="utf-8-sig")
                    st.download_button(
                        label="⬇️ Baixar resultado em CSV",
                        data=csv,
                        file_name="prazos_filtrados.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ Nenhum prazo localizado para os filtros aplicados.")

            except KeyError as e:
                st.error(f"❌ Coluna não encontrada: {e}. Verifique se os nomes das colunas na planilha estão corretos.")
        else:
            st.info("💡 Use os filtros acima para buscar prazos por transportadora, cidade ou UF.")

        # 7. VISÃO GERAL (bônus)
        with st.expander("📊 Ver visão geral da base carregada"):
            st.write(f"Total de registros: **{len(df_base)}**")
            st.write(f"Transportadoras na base: **{df_base[COL_TRANSP].nunique()}**")
            st.dataframe(df_base.head(10), use_container_width=True, hide_index=True)

            # GRÁFICO 2 — Distribuição geral de prazos (histograma)
            st.markdown("#### 📊 Distribuição Geral de Prazos")
            fig_hist = px.histogram(
                df_base,
                x=COL_PRAZO,
                nbins=20,
                labels={COL_PRAZO: "Prazo (dias)", "count": "Quantidade de rotas"},
                color_discrete_sequence=["#2563EB"],
            )
            fig_hist.update_layout(
                xaxis_title="Prazo (dias)",
                yaxis_title="Quantidade de rotas",
                bargap=0.1,
                margin=dict(l=10, r=10, t=20, b=20),
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            st.caption("Este gráfico mostra como os prazos estão distribuídos em toda a base — útil para entender o perfil geral das transportadoras.")

else:
    # Tela de boas-vindas quando nenhum arquivo foi carregado
    st.info("👈 Faça o upload da planilha de prazos no menu lateral para começar.")
    st.markdown("""
    ### Como usar
    1. Clique em **Browse files** no menu lateral
    2. Selecione o arquivo `.xlsx` com a aba **Prazos Transportadoras**
    3. Use os filtros para buscar por transportadora, cidade ou UF
    """)

# 8. RODAPÉ
st.markdown("---")
st.caption("🚀 Desenvolvido por Bruno Maciel | github.com/CaptLink14")
