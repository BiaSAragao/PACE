import streamlit as st

st.set_page_config(layout="wide")

st.title("PACE")

pagina = st.sidebar.selectbox(
    "Menu",
    [
        "Passageiros",
        "Motoristas",
        "Veículos",
        "Agendas",
        "Ordens de Serviço"
    ]
)