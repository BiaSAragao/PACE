import streamlit as st
from database.conexao import conectar

st.title("🚐 Veículos")

with st.form("cad_veiculo"):

    numero = st.number_input(
        "Número do carro",
        min_value=1
    )

    placa = st.text_input("Placa")

    capacidade = st.number_input(
        "Capacidade",
        min_value=1
    )

    salvar = st.form_submit_button("Salvar")

    if salvar:

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO veiculos
            (
                numero_carro,
                placa,
                capacidade
            )
            VALUES (%s,%s,%s)
        """,
        (
            numero,
            placa,
            capacidade
        ))

        conn.commit()

        cur.close()
        conn.close()

        st.success("Veículo cadastrado!")

conn = conectar()

cur = conn.cursor()

cur.execute("""
    SELECT
        numero_carro,
        placa,
        capacidade
    FROM veiculos
""")

st.dataframe(cur.fetchall())

cur.close()
conn.close()