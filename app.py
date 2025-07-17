# app.py (versão com correção para exportação Excel)
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database import Database
import io  # ***** PASSO 1: IMPORTAR A BIBLIOTECA IO *****

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Produção",
    page_icon="🔩",
    layout="wide"
)

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
@st.cache_resource
def get_db():
    return Database()

db = get_db()

# --- ESTADO DA SESSÃO ---
if 'periodo_selecionado' not in st.session_state:
    st.session_state.periodo_selecionado = "Hoje"
    st.session_state.start_date = datetime.now().date()
    st.session_state.end_date = datetime.now().date()
    st.session_state.period_name = "Hoje"

# --- LISTA DE OPERADORES E MODELOS ---
OPERADORES = [
    "GILSON ROBERTO DE OLIVEIRA", "JÚLIO BONANCIM SILVA", "FELIPE DOMINGOS MOREIRA",
    "LUIZ HENRIQUE DE JESUS MARQUES", "RAFAEL BARROSO MARQUES", "JOÃO VITOR DA SILVA",
    "KEOLIN MIRELA FERRERA"
]
MODELOS = ["Unidade Compressora 20+", "Unidade Compressora 15+", "Unidade Compressora 10 RED"]


# --- ABAS PRINCIPAIS ---
st.title("🔩 Controle de Produção de Cabeçotes")
tab1, tab2 = st.tabs(["📋 Registrar Produção", "📊 Dashboard & Histórico"])


# --- ABA 1: REGISTRAR PRODUÇÃO ---
with tab1:
    st.header("Registrar Novo Lote de Produção")
    
    with st.form("registro_form", clear_on_submit=True):
        st.subheader("Informações Gerais do Lote")
        modelo_dropdown = st.selectbox("Modelo de Cabeçote", options=MODELOS, index=None, placeholder="Selecione o modelo...")

        st.divider()
        
        st.subheader("Etapas de Produção")
        col_mont, col_pint, col_test = st.columns(3)

        with col_mont:
            st.markdown("**Montagem**")
            op_montagem_dd = st.selectbox("Operador Montagem", options=OPERADORES, index=None, key="op_mont")
            qty_montado_input = st.number_input("Qtd. Montada", min_value=0, step=1, key="qtd_mont")

        with col_pint:
            st.markdown("**Pintura**")
            op_pintura_dd = st.selectbox("Operador Pintura", options=OPERADORES, index=None, key="op_pint")
            qty_pintado_input = st.number_input("Qtd. Pintada", min_value=0, step=1, key="qtd_pint")

        with col_test:
            st.markdown("**Teste**")
            op_teste_dd = st.selectbox("Operador Teste", options=OPERADORES, index=None, key="op_test")
            qty_testado_input = st.number_input("Qtd. Testada", min_value=0, step=1, key="qtd_test")
        
        st.divider()
        
        st.subheader("Retrabalho e Observações")
        col_retr, col_obs = st.columns(2)
        with col_retr:
             op_retrabalho_dd = st.selectbox("Operador Retrabalho", options=OPERADORES, index=None, key="op_retr")
             retrabalho_input = st.number_input("Qtd. Retrabalho", min_value=0, step=1, key="qtd_retr")

        with col_obs:
            observacao_input = st.text_area("Observação (opcional)", height=150)
            
        st.divider()
        
        submitted = st.form_submit_button("✅ Registrar Lote de Produção", use_container_width=True)
        if submitted:
            if not modelo_dropdown:
                st.warning("Por favor, selecione um modelo de cabeçote.")
            elif not any([qty_montado_input, qty_pintado_input, qty_testado_input]):
                 st.warning("Preencha a quantidade de pelo menos uma etapa!")
            else:
                try:
                    db.registrar_producao(
                        modelo_dropdown, op_montagem_dd, qty_montado_input,
                        op_pintura_dd, qty_pintado_input, op_teste_dd, qty_testado_input,
                        op_retrabalho_dd, retrabalho_input, observacao_input
                    )
                    st.success("Produção registrada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao registrar: {e}")


# --- ABA 2: DASHBOARD E HISTÓRICO ---
with tab2:
    st.header("Análise de Produção")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    def set_period(period_name, start_delta_days=0, end_delta_days=0, month_start=False):
        today = datetime.now().date()
        st.session_state.period_name = period_name
        if month_start:
             st.session_state.start_date = today.replace(day=1)
        elif period_name == "Histórico Completo":
             st.session_state.start_date = None
        else:
            st.session_state.start_date = today - timedelta(days=start_delta_days)
        st.session_state.end_date = today - timedelta(days=end_delta_days)

    if col1.button("Hoje", use_container_width=True):
        set_period("Hoje")
    if col2.button("Últimos 7 dias", use_container_width=True):
        set_period("Últimos 7 dias", 6)
    if col3.button("Este Mês", use_container_width=True):
        set_period("Este Mês", month_start=True)
    if col4.button("Histórico Completo", use_container_width=True):
        set_period("Histórico Completo")

    with col5:
        picked_date = st.date_input("Escolher Dia", value=datetime.now().date(), format="DD/MM/YYYY")
        if picked_date != datetime.now().date():
            st.session_state.start_date = picked_date
            st.session_state.end_date = picked_date
            st.session_state.period_name = f"Dia: {picked_date.strftime('%d/%m/%Y')}"

    st.subheader(f"Exibindo período: {st.session_state.period_name}")
    start_str = st.session_state.start_date.strftime("%Y-%m-%d") if st.session_state.start_date else None
    end_str = st.session_state.end_date.strftime("%Y-%m-%d") if st.session_state.end_date else None

    stats = db.get_stats_periodo(start_str, end_str)
    total_montado = stats.get("total_montado", 0)
    total_pintado = stats.get("total_pintado", 0)
    total_testado = stats.get("total_testado", 0)
    total_retrabalho = stats.get("total_retrabalho", 0)
    taxa_retrabalho = (total_retrabalho / total_testado * 100) if total_testado > 0 else 0

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Peças Montadas", f"{total_montado:,}".replace(",", "."))
    metric2.metric("Peças Pintadas", f"{total_pintado:,}".replace(",", "."))
    metric3.metric("Produção Final (Testadas)", f"{total_testado:,}".replace(",", "."))
    metric4.metric("Taxa de Retrabalho", f"{taxa_retrabalho:.1f}%", delta=f"{total_retrabalho} pçs", delta_color="inverse")

    st.divider()

    chart_col1, chart_col2 = st.columns([1, 2])
    with chart_col1:
        st.markdown("**Produção por Modelo (%)**")
        producao_modelo = db.get_producao_por_modelo(start_str, end_str)
        if producao_modelo:
            df_pie = pd.DataFrame(producao_modelo, columns=['Modelo', 'Total'])
            fig_pie = px.pie(df_pie, names='Modelo', values='Total', hole=0.4)
            fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhum dado para exibir no gráfico de pizza.")

    with chart_col2:
        st.markdown("**Produção por Modelo (Unidades)**")
        if producao_modelo:
            df_bar = pd.DataFrame(producao_modelo, columns=['Modelo', 'Total'])
            fig_bar = px.bar(df_bar, x='Modelo', y='Total', text_auto='.2s', color='Modelo')
            fig_bar.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False)
            fig_bar.update_layout(xaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado para exibir no gráfico de barras.")

    st.divider()

    st.subheader("Histórico Detalhado")
    registros = db.get_producao_periodo(start_str, end_str)
    if registros:
        df_hist = pd.DataFrame(registros, columns=[
            "ID", "Modelo", "Op. Montagem", "Qtd. Montado", "Op. Pintura", "Qtd. Pintado",
            "Op. Teste", "Qtd. Testado", "Op. Retrabalho", "Qtd. Retrabalho", "Observação", "Data/Hora"
        ])
        
        df_hist['Data/Hora'] = pd.to_datetime(df_hist['Data/Hora']).dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

        admin_col1, admin_col2, admin_col3 = st.columns([2, 1, 1])
        
        # ***** PASSO 2: FUNÇÃO DE EXPORTAÇÃO CORRIGIDA *****
        @st.cache_data
        def convert_df_to_excel(df):
            output = io.BytesIO()
            # Escreve o dataframe no objeto BytesIO como um arquivo excel
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Producao_Detalhada')
            # Pega o conteúdo do BytesIO
            processed_data = output.getvalue()
            return processed_data

        excel_data = convert_df_to_excel(df_hist)
        admin_col1.download_button(
            label="📥 Exportar para Excel",
            data=excel_data,
            file_name=f"producao_cabecotes_{datetime.now().strftime('%Y%m%d')}.xlsx",
            # O mime type correto para arquivos .xlsx modernos
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        with admin_col2:
            ids = df_hist['ID'].tolist()
            id_to_delete = st.selectbox("ID para excluir", options=ids, index=None, placeholder="Selecione um ID")
            if st.button("Excluir Registro", use_container_width=True, disabled=(id_to_delete is None)):
                db.delete_producao_por_id(id_to_delete)
                st.toast(f"Registro {id_to_delete} excluído com sucesso!")
                st.rerun()

        with admin_col3:
            if st.button("🚨 Limpar Histórico", use_container_width=True, type="primary"):
                if 'confirm_delete' not in st.session_state:
                    st.session_state.confirm_delete = True
                    st.rerun()

            if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
                if st.button("CONFIRMAR EXCLUSÃO TOTAL", use_container_width=True, type="primary"):
                    db.delete_all_producao()
                    st.success("Todo o histórico foi limpo.")
                    del st.session_state.confirm_delete
                    st.rerun()
                if st.button("Cancelar", use_container_width=True):
                     del st.session_state.confirm_delete
                     st.rerun()
    else:
        st.info("Nenhum registro encontrado para o período selecionado.")