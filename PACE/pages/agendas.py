import streamlit as st
from database.conexao import conectar

st.title("📅 Agenda dos Passageiros")

conn = conectar()
cur = conn.cursor()

cur.execute("""
SELECT
    id_passageiro,
    nome
FROM passageiros
ORDER BY nome
""")

passageiros = cur.fetchall()

cur.close()
conn.close()

nomes = {
    p[1]: p[0]
    for p in passageiros
}

with st.form("agenda"):

    passageiro = st.selectbox(
        "Passageiro",
        list(nomes.keys())
    )

    dia_semana = st.selectbox(
        "Dia",
        [
            0,1,2,3,4,5,6
        ]
    )

    horario_saida = st.time_input(
        "Horário Saída"
    )

    horario_retorno = st.time_input(
        "Horário Retorno"
    )

    destino = st.text_input(
        "Destino"
    )

    salvar = st.form_submit_button(
        "Salvar"
    )

    if salvar:

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO agenda_passageiros
            (
                id_passageiro,
                dia_semana,
                horario_saida,
                horario_retorno,
                destino
            )
            VALUES (%s,%s,%s,%s,%s)
        """,
        (
            nomes[passageiro],
            dia_semana,
            horario_saida,
            horario_retorno,
            destino
        ))

        conn.commit()

        cur.close()
        conn.close()

        st.success("Agenda salva!")