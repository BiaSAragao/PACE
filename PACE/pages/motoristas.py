import streamlit as st
from database.conexao import conectar

st.title("🚗 Motoristas")

with st.form("cad_motorista"):

    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")

    salvar = st.form_submit_button("Salvar")

    if salvar:

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO motoristas
            (nome, telefone)
            VALUES (%s,%s)
        """,(nome,telefone))

        conn.commit()

        cur.close()
        conn.close()

        st.success("Motorista cadastrado!")

conn = conectar()

cur = conn.cursor()

cur.execute("""
    SELECT *
    FROM motoristas
    ORDER BY nome
""")

st.dataframe(cur.fetchall())

cur.close()
conn.close()