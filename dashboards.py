import streamlit as st 
import pandas as pd
import plotly.express as px
import os
import io

# Configuração de página com tema e ícone
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado - caixas pretas e números verde claro
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        color: #0D47A1;
        padding-top: 1rem;
        border-bottom: 1px solid #ccc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        background-color: #1E88E5;
        color: white;
    }
    /* Estilizar diretamente os componentes de métrica do Streamlit */
    div[data-testid="stMetric"] {
        background-color: #212121; /* Preto para as caixas */
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    /* Títulos das métricas em branco */
    div[data-testid="stMetric"] label {
        color: white !important;
        font-weight: bold !important;
    }
    /* Valores das métricas em verde claro */
    div[data-testid="stMetricValue"] {
        color: #8bc34a !important; /* Verde claro */
        font-weight: bold !important;
    }
    /* Delta (percentual) em verde mais claro */
    div[data-testid="stMetricDelta"] {
        color: #c5e1a5 !important; /* Verde ainda mais claro */
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho com título
st.markdown('<h1 class="main-header">Dashboard de Vendas</h1>', unsafe_allow_html=True)

# Verificar se o arquivo existe
arquivo = 'Vendas Simulação.xlsx'
if not os.path.exists(arquivo):
    st.error(f"Arquivo '{arquivo}' não encontrado. Verifique se o arquivo está no diretório correto.")
    st.stop()

try:
    # Carregar o arquivo Excel
    @st.cache_data(ttl=3600)
    def load_data():
        df = pd.read_excel(arquivo, sheet_name='Vendas')
        df['Data da Venda'] = pd.to_datetime(df['Data da Venda'])
        return df
    
    df = load_data()
    
    # Sidebar com filtros
    st.sidebar.title("Filtros")
    
    # Organizar filtros em expansores
    with st.sidebar.expander("📅 Período", expanded=True):
        data_inicial = st.date_input('Data inicial', df['Data da Venda'].min())
        data_final = st.date_input('Data final', df['Data da Venda'].max())
    
    # Aplicar filtro de data
    df_filtrado = df.query('`Data da Venda` >= @data_inicial & `Data da Venda` <= @data_final')
    
    with st.sidebar.expander("🌎 Localização", expanded=True):
        continentes_opcoes = ["Todos"] + sorted(df['Continente'].unique().tolist())
        continente_selecionado = st.selectbox('Continente', continentes_opcoes)
        
        if continente_selecionado != "Todos":
            df_filtrado = df_filtrado.query('Continente == @continente_selecionado')
    
    with st.sidebar.expander("🏷️ Produtos", expanded=True):
        categorias_opcoes = ["Todas"] + sorted(df['Categoria'].unique().tolist())
        categoria_selecionada = st.selectbox('Categoria', categorias_opcoes)
        
        if categoria_selecionada != "Todas":
            df_filtrado = df_filtrado.query('Categoria == @categoria_selecionada')
            produtos_disponiveis = df_filtrado['Produto'].unique().tolist()
        else:
            produtos_disponiveis = df['Produto'].unique().tolist()
        
        produtos_opcoes = ["Todos"] + sorted(produtos_disponiveis)
        produto_selecionado = st.selectbox('Produto', produtos_opcoes)
        
        if produto_selecionado != "Todos":
            df_filtrado = df_filtrado.query('Produto == @produto_selecionado')
        
        marcas_opcoes = ["Todas"] + sorted(df['Marca'].unique().tolist())
        marca_selecionada = st.selectbox('Marca', marcas_opcoes)
        
        if marca_selecionada != "Todas":
            df_filtrado = df_filtrado.query('Marca == @marca_selecionada')
    
    # Modo de visualização
    modo_visualizacao = st.sidebar.radio(
        "Modo de visualização:",
        ["Completo", "Compacto"],
        horizontal=True
    )
    
    # Ajustar layout baseado no modo
    if modo_visualizacao == "Compacto":
        num_colunas = 2
        altura_grafico = 300
    else:
        num_colunas = 4
        altura_grafico = 500
    
    # Botão para resetar filtros
    if st.sidebar.button("Resetar Filtros"):
        st.experimental_rerun()
    
    # Métricas em cartões visuais - CORRIGIDO para remover barras brancas
    st.markdown('<h2 class="subheader">Métricas Principais</h2>', unsafe_allow_html=True)
    
    # Usar colunas do Streamlit diretamente sem divs adicionais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_vendas = df_filtrado['Qtd. Vendida'].sum()
        st.metric("Total de Vendas", f"{total_vendas:,.0f}")
    
    with col2:
        faturamento = df_filtrado['Faturamento'].sum()
        st.metric("Faturamento", f"R$ {faturamento:,.2f}")
    
    with col3:
        custo_total = (df_filtrado['Custo Unitário'] * df_filtrado['Qtd. Vendida']).sum()
        st.metric("Custo Total", f"R$ {custo_total:,.2f}")
    
    with col4:
        lucro = faturamento - custo_total
        margem = (lucro / faturamento * 100) if faturamento > 0 else 0
        st.metric("Lucro", f"R$ {lucro:,.2f}", f"Margem: {margem:.1f}%")
    
    # Abas para diferentes visualizações
    st.markdown('<h2 class="subheader">Análise de Vendas</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Gráficos", "📈 Tendências", "📋 Dados"])
    
    with tab1:
        # Seleção do tipo de gráfico com ícones
        tipo_grafico = st.radio(
            "Escolha o tipo de visualização:",
            ["Barras", "Pizza", "Dispersão"],
            horizontal=True,
            format_func=lambda x: {
                "Barras": "📊 Barras", 
                "Pizza": "🍕 Pizza", 
                "Dispersão": "🔵 Dispersão"
            }[x]
        )
        
        # Gráficos conforme seleção
        if tipo_grafico == "Barras":
            fig = px.bar(
                df_filtrado.groupby('Categoria')['Faturamento'].sum().reset_index().sort_values('Faturamento', ascending=False),
                x='Categoria',
                y='Faturamento',
                title='Faturamento por Categoria',
                color='Categoria',
                template="plotly_white",
                height=altura_grafico
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif tipo_grafico == "Pizza":
            fig = px.pie(
                df_filtrado.groupby('Continente')['Faturamento'].sum().reset_index(),
                values='Faturamento',
                names='Continente',
                title='Faturamento por Continente',
                template="plotly_white",
                height=altura_grafico
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif tipo_grafico == "Dispersão":
            fig = px.scatter(
                df_filtrado,
                x='PrecoUnitario',
                y='Qtd. Vendida',
                size='Faturamento',
                color='Categoria',
                hover_name='Produto',
                title='Relação entre Preço, Quantidade Vendida e Faturamento',
                template="plotly_white",
                height=altura_grafico
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Gráfico de tendência temporal - CORRIGIDO
        st.subheader("Tendência de Vendas ao Longo do Tempo")
        
        # Opções de agregação temporal
        periodo = st.select_slider(
            "Agregação temporal:",
            options=["Diário", "Semanal", "Mensal", "Trimestral", "Anual"],
            value="Mensal"
        )
        
        # Mapeamento de período para frequência pandas
        freq_map = {
            "Diário": "D", "Semanal": "W", "Mensal": "M", 
            "Trimestral": "Q", "Anual": "Y"
        }
        
        # Verificar se há dados suficientes
        if len(df_filtrado) > 0:
            try:
                # Gráfico de linha com área sombreada - com tratamento de erro
                dados_tempo = df_filtrado.groupby(
                    pd.Grouper(key='Data da Venda', freq=freq_map[periodo])
                )['Faturamento'].sum().reset_index()
                
                # Verificar se o agrupamento gerou dados
                if not dados_tempo.empty and dados_tempo['Faturamento'].sum() > 0:
                    fig = px.area(
                        dados_tempo, 
                        x='Data da Venda', 
                        y='Faturamento',
                        title=f'Faturamento {periodo}',
                        template="plotly_white",
                        height=altura_grafico
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Não há dados suficientes para mostrar a tendência {periodo.lower()}. Tente alterar os filtros ou selecionar outro período.")
            except Exception as e:
                st.error(f"Erro ao gerar o gráfico de tendência: {str(e)}")
                st.info("Tente selecionar um período diferente ou ajustar os filtros.")
        else:
            st.info("Não há dados disponíveis para o período selecionado. Ajuste os filtros para visualizar a tendência.")
    
    with tab3:
        # Dados tabulares com opções de download
        st.subheader("Dados Filtrados")
        
        # Opções de colunas para exibir
        colunas_disponiveis = df_filtrado.columns.tolist()
        colunas_selecionadas = st.multiselect(
            "Selecione as colunas para visualizar:",
            colunas_disponiveis,
            default=colunas_disponiveis[:6]  # Primeiras 6 colunas por padrão
        )
        
        # Exibir dados com as colunas selecionadas
        if colunas_selecionadas:
            st.dataframe(df_filtrado[colunas_selecionadas], use_container_width=True)
        else:
            st.info("Selecione pelo menos uma coluna para visualizar os dados.")
        
        # Botões de download em diferentes formatos
        col1, col2 = st.columns(2)
        with col1:
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Baixar como CSV",
                csv,
                "vendas_filtradas.csv",
                "text/csv",
                key='download-csv'
            )
        
        with col2:
            # Função para converter para Excel (requer openpyxl)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, sheet_name='Vendas', index=False)
            
            st.download_button(
                "📥 Baixar como Excel",
                buffer.getvalue(),
                "vendas_filtradas.xlsx",
                "application/vnd.ms-excel",
                key='download-excel'
            )
    
    # Adicionar um footer com informações e ajuda
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("**Dashboard v1.0**")
    
    with col2:
        st.markdown("Desenvolvido com ❤️ usando Streamlit")
    
    with col3:
        with st.expander("ℹ️ Ajuda"):
            st.markdown("""
            **Como usar este dashboard:**
            - Use os filtros na barra lateral para refinar os dados
            - Escolha diferentes visualizações nas abas
            - Baixe os dados filtrados em CSV ou Excel
            
            Para suporte: suporte@empresa.com
            """)

except Exception as e:
    st.error(f"Erro ao carregar o dashboard: {str(e)}")
    st.write("Detalhes do erro para depuração:")
    st.exception(e)
