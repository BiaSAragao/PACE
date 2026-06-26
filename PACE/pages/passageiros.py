import streamlit as st
from database.conexao import conectar

st.title("👤 Passageiros")

with st.form("cadastro_passageiro"):

    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")
    observacoes = st.text_area("Observações")

    salvar = st.form_submit_button("Salvar")

    if salvar:

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO passageiros
            (nome, telefone, observacoes)
            VALUES (%s,%s,%s)
        """, (nome, telefone, observacoes))

        conn.commit()

        cur.close()
        conn.close()

        st.success("Passageiro cadastrado!")

st.divider()

conn = conectar()

cur = conn.cursor()

cur.execute("""
    SELECT
        id_passageiro,
        nome,
        telefone
    FROM passageiros
    ORDER BY nome
""")

dados = cur.fetchall()

cur.close()
conn.close()

st.dataframe(
    dados,
    use_container_width=True
)