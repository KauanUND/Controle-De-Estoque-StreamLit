import streamlit as st
import pandas as pd
import os
import io

# --- PLANO DE FUNDO E ESTILO ---
st.markdown(
    """
    <style>
    .stApp { background-color: #1e1e2f; color: #f5f5f5; }
    h1, h2, h3, h4, h5, h6 { color: #ffa500; }
    .stTextInput label, .stNumberInput label, .stSelectbox label { color: #f5f5f5; font-weight: bold; }
    div.stButton > button { background-color: #282c34; color: #ffa500; border-radius: 8px; height: 35px; width: 200px; font-weight: bold; }
    .stForm, .stExpander { background-color: #2e2e3e; padding: 10px; border-radius: 10px; }
    .stDataFrame { background-color: #2e2e3e; color: #f5f5f5; }
    .marca-agua { position: fixed; bottom: 20px; right: 20px; opacity: 0.08; font-size: 25px; color: #ffffff; font-weight: bold; pointer-events: none; z-index: 9999; }
    </style>
    <div class="marca-agua">Desenvolvido por Kauan :)</div>
    """,
    unsafe_allow_html=True
)

# --- ARQUIVO DE ESTOQUE ---
ARQUIVO_ESTOQUE = "estoque_limpo.xlsx"

# --- FUNÇÕES ---
def carregar_estoque():
    if os.path.exists(ARQUIVO_ESTOQUE):
        df = pd.read_excel(ARQUIVO_ESTOQUE)
        df["Quantidade"] = pd.to_numeric(df.get("Quantidade"), errors="coerce").fillna(0).astype(int)
        df["Valor de Compra"] = pd.to_numeric(df.get("Valor de Compra"), errors="coerce").fillna(0.0)
        df["Valor Total"] = pd.to_numeric(df.get("Valor Total"), errors="coerce").fillna(0.0)
        df["SKU"] = df.get("SKU", pd.Series(dtype=str)).astype(str)
        df["Descrição"] = df.get("Descrição", pd.Series(dtype=str)).astype(str)
        return df
    else:
        return pd.DataFrame(columns=["SKU", "Descrição", "Quantidade", "Valor de Compra", "Valor Total"])

def salvar_estoque(df):
    try:
        df.to_excel(ARQUIVO_ESTOQUE, index=False)
    except PermissionError:
        st.error("❌ Não foi possível salvar o arquivo. Feche o Excel se ele estiver aberto.")

def mostrar_estoque(df_to_show):
    if df_to_show.empty:
        estoque_container.info("Nenhum produto encontrado para o filtro atual." if filtro else "Nenhum produto cadastrado ainda.")
    else:
        df_exibir = df_to_show.copy()
        df_exibir.insert(0, "#", range(1, len(df_exibir) + 1))

        def color_quantidade(val):
            if val < 200: return 'color: red'
            elif val <= 1000: return 'color: orange'
            else: return 'color: green'

        styled = (
            df_exibir.style
            .format({"Valor de Compra": "{:.2f}", "Valor Total": "{:.2f}"})
            .applymap(color_quantidade, subset=['Quantidade'])
            .set_table_styles([
                {'selector': 'thead th', 'props': [('background-color', '#3e3e50'), ('color', '#b0b0b0'), ('font-weight', 'bold')]},
                {'selector': 'tbody td', 'props': [('color', '#f0f0f0'), ('background-color', '#2e2e3e')]}
            ])
            .set_properties(**{'text-align': 'left'})
            .set_table_attributes('class="dataframe"')
        )
        estoque_container.dataframe(styled, width=1300, use_container_width=False)

def atualizar_resumo():
    total_itens = st.session_state.df["Quantidade"].sum() if not st.session_state.df.empty else 0
    valor_estoque = st.session_state.df["Valor Total"].sum() if not st.session_state.df.empty else 0.0
    quantidade_produtos = st.session_state.df.shape[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de itens", total_itens)
    col2.metric("Valor total do estoque", f"R$ {valor_estoque:,.2f}")
    col3.metric("Produtos cadastrados", quantidade_produtos)

def filtrar_df(termo: str) -> pd.DataFrame:
    if not termo:
        return st.session_state.df.copy()
    ssku = st.session_state.df["SKU"].astype(str)
    sdesc = st.session_state.df["Descrição"].astype(str)
    mask = ssku.str.contains(termo, case=False, na=False) | sdesc.str.contains(termo, case=False, na=False)
    return st.session_state.df.loc[mask].copy()

def gerar_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Estoque')
    return output.getvalue()

# --- CONFIGURAÇÃO DO APP ---
st.set_page_config(page_title="Gerenciador de Estoque RGLED", layout="centered")
st.title("📦 Gerenciador de Estoque Completo RGLED")
st.write("Controle seus produtos, edite todos os campos e remova itens facilmente.")

# --- SESSION STATE ---
if "df" not in st.session_state: st.session_state.df = carregar_estoque()
if "sku_temp" not in st.session_state: st.session_state.sku_temp = ""
if "descricao_temp" not in st.session_state: st.session_state.descricao_temp = ""
if "quantidade_temp" not in st.session_state: st.session_state.quantidade_temp = 0
if "valor_compra_temp" not in st.session_state: st.session_state.valor_compra_temp = 0.0
if "produto_editar" not in st.session_state: st.session_state.produto_editar = None
if "produto_remover" not in st.session_state: st.session_state.produto_remover = None

# --- RESUMO ---
st.subheader("📊 Resumo do Estoque")
atualizar_resumo()

# --- FILTRO ---
st.subheader("🔍 Filtrar Produtos")
filtro = st.text_input("Filtrar por SKU ou Descrição", placeholder="Ex.: RG123 ou Lâmpada")
df_filtrado = filtrar_df(filtro)
st.caption(f"Mostrando {len(df_filtrado)} de {len(st.session_state.df)} produtos.")

# --- TABELA ---
estoque_container = st.empty()
mostrar_estoque(df_filtrado)

# --- ADICIONAR PRODUTO ---
with st.expander("➕ Adicionar Produto"):
    with st.form("adicionar_produto"):
        sku = st.text_input("SKU", value=st.session_state.sku_temp)
        st.session_state.sku_temp = sku
        descricao = st.text_input("Descrição", value=st.session_state.descricao_temp)
        st.session_state.descricao_temp = descricao
        quantidade = st.number_input("Quantidade", min_value=0, step=1, value=int(st.session_state.quantidade_temp))
        st.session_state.quantidade_temp = quantidade
        valor_compra = st.number_input("Valor de Compra", min_value=0.0, format="%.2f", value=float(st.session_state.valor_compra_temp))
        st.session_state.valor_compra_temp = valor_compra
        adicionar = st.form_submit_button("Adicionar Produto")
        if adicionar:
            if sku.strip() == "":
                st.error("❌ SKU não pode ficar vazio!")
            elif sku in st.session_state.df["SKU"].values:
                st.error(f"❌ Produto com SKU **{sku}** já existe!")
            else:
                valor_total = int(quantidade) * float(valor_compra)
                novo_item = pd.DataFrame({"SKU":[sku],"Descrição":[descricao],"Quantidade":[quantidade],
                                          "Valor de Compra":[valor_compra],"Valor Total":[valor_total]})
                st.session_state.df = pd.concat([st.session_state.df, novo_item], ignore_index=True)
                salvar_estoque(st.session_state.df)
                df_filtrado = filtrar_df(filtro)
                mostrar_estoque(df_filtrado)
                atualizar_resumo()
                st.success(f"✅ Produto **{descricao}** adicionado com sucesso!")
                st.session_state.sku_temp = ""
                st.session_state.descricao_temp = ""
                st.session_state.quantidade_temp = 0
                st.session_state.valor_compra_temp = 0.0

# --- EDITAR PRODUTO ---
if not st.session_state.df.empty:
    with st.expander("✏️ Editar Produto"):
        base_df_menus = df_filtrado if not df_filtrado.empty else st.session_state.df
        skus_disponiveis = base_df_menus["SKU"].dropna().astype(str).tolist()
        if skus_disponiveis:
            if st.session_state.produto_editar in skus_disponiveis:
                index_editar = skus_disponiveis.index(st.session_state.produto_editar)
            else:
                index_editar = 0
                st.session_state.produto_editar = skus_disponiveis[0]
            produto_editar = st.selectbox("Selecione o SKU do produto", skus_disponiveis, index=index_editar, key="editar_select")
            st.session_state.produto_editar = produto_editar
            item = st.session_state.df.loc[st.session_state.df["SKU"] == produto_editar].iloc[0]
            with st.form("editar_produto"):
                descricao = st.text_input("Descrição", value=str(item["Descrição"]), key="edit_descricao")
                quantidade = st.number_input("Quantidade", min_value=0, value=int(item["Quantidade"]), key="edit_quantidade")
                valor_compra = st.number_input("Valor de Compra", min_value=0.0, value=float(item["Valor de Compra"]), format="%.2f", key="edit_valor")
                editar = st.form_submit_button("Salvar Alterações")
                if editar:
                    st.session_state.df.loc[st.session_state.df["SKU"] == produto_editar,
                                            ["Descrição","Quantidade","Valor de Compra"]] = [descricao,quantidade,valor_compra]
                    st.session_state.df.loc[st.session_state.df["SKU"] == produto_editar,"Valor Total"] = quantidade*valor_compra
                    salvar_estoque(st.session_state.df)
                    df_filtrado = filtrar_df(filtro)
                    mostrar_estoque(df_filtrado)
                    atualizar_resumo()
                    st.success(f"✅ Produto **{descricao}** atualizado!")

# --- REMOVER PRODUTO ---
if not st.session_state.df.empty:
    with st.expander("🗑️ Remover Produto"):
        base_df_menus = df_filtrado if not df_filtrado.empty else st.session_state.df
        skus_disponiveis = base_df_menus["SKU"].dropna().astype(str).tolist()
        if skus_disponiveis:
            if st.session_state.produto_remover in skus_disponiveis:
                index_remover = skus_disponiveis.index(st.session_state.produto_remover)
            else:
                index_remover = 0
                st.session_state.produto_remover = skus_disponiveis[0]
            produto_remover = st.selectbox(
                "Selecione o SKU do produto para remover",
                skus_disponiveis,
                index=index_remover,
                key="remover_select"
            )
            st.session_state.produto_remover = produto_remover

            if st.button("Remover Produto"):
                st.session_state.df = st.session_state.df[st.session_state.df["SKU"] != produto_remover]
                salvar_estoque(st.session_state.df)
                df_filtrado = filtrar_df(filtro)
                mostrar_estoque(df_filtrado)
                atualizar_resumo()
                if st.session_state.produto_editar == produto_remover:
                    st.session_state.produto_editar = None
                if st.session_state.produto_remover == produto_remover:
                    st.session_state.produto_remover = None
                st.warning(f"⚠️ Produto com SKU **{produto_remover}** removido do estoque!")

# --- BOTÃO DE DOWNLOAD DO EXCEL (sempre visível) ---
excel_bytes = gerar_excel_bytes(st.session_state.df)
st.download_button(
    label="📥 Baixar Estoque Completo",
    data=excel_bytes,
    file_name="estoque_completo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
