import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import io
import time
import os
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(layout="wide")

# Função para se conectar ao banco de dados
@st.cache_resource
def get_connection():
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    db_name = os.getenv("DB_NAME")

    # Adiciona `?sslmode=require` para forçar a conexão via SSL
    engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}/{db_name}?sslmode=require')
    return engine

# Função para rodar a query no banco de dados e retornar um DataFrame
@st.cache_data(ttl=15)  # Cache renovado a cada 10 segundos
def run_query():
    query = """
    SELECT id, status, created_at as Data, customer_name as Nome, customer_phone_number as Celular, is_attended
    FROM public.ft_events
    WHERE status = 'ABANDONED_CART' OR status = 'REFUSED'
    ORDER BY created_at DESC
    """
    conn = get_connection().connect()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Interface do Streamlit
st.title("Carrinhos Abandonados - Atualização em Tempo Real")

# Exibir mensagem de recarregamento dos dados
st.write("Os dados são recarregados a cada 15 segundos.")

# Rodar a query e exibir os dados em tempo real
df = run_query()

# Limitar o número de registros exibidos por vez para melhorar a performance
rows_per_page = 15
total_rows = len(df)
total_pages = (total_rows // rows_per_page) + 1
page = st.number_input("Página", min_value=1, max_value=total_pages, step=1, value=1)

# Selecionar apenas os dados da página atual
start_row = (page - 1) * rows_per_page
end_row = start_row + rows_per_page
df_page = df.iloc[start_row:end_row]

# Criar a tabela sem checkboxes, apenas exibição
for index, row in df_page.iterrows():
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.write(row['nome'])  # Nome do cliente
    with col2:
        st.write(row['celular'])  # Número de celular
    with col3:
        st.write(row['data'])  # Data
    with col4:
        st.write(row['status'])  # Status do carrinho
    with col5:
        # Criar link do WhatsApp
        whatsapp_link = f"https://wa.me/{row['celular']}"
        st.markdown(f"[Abrir no WhatsApp]({whatsapp_link})", unsafe_allow_html=True)

# Botão para baixar o arquivo Excel
def download_as_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Abandoned Carts')
    writer.close()
    output.seek(0)
    return output

st.download_button(
    label="Baixar Tabela como Excel",
    data=download_as_excel(df),
    file_name='carts_abandonados.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
