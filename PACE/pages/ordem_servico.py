import streamlit as st
from database.conexao import conectar
from datetime import date

st.title("📄 Ordem de Serviço")

data_servico = st.date_input(
    "Data",
    value=date.today()
)

tipo_dia = st.selectbox(
    "Tipo do Dia",
    [
        "UTIL",
        "SABADO",
        "DOMINGO",
        "FERIADO"
    ]
)

if st.button("Gerar Ordem"):

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id_veiculo
        FROM veiculos
        WHERE status = TRUE
        LIMIT 1
    """)

    veiculo = cur.fetchone()

    if not veiculo:

        st.error("Nenhum veículo disponível")

    else:

        cur.execute("""
            INSERT INTO ordens_servico
            (
                data_servico,
                tipo_dia,
                id_veiculo
            )
            VALUES (%s,%s,%s)
            RETURNING id_ordem
        """,
        (
            data_servico,
            tipo_dia,
            veiculo[0]
        ))

        ordem = cur.fetchone()[0]

        conn.commit()

        st.success(
            f"Ordem {ordem} criada!"
        )

    cur.close()
    conn.close()

st.divider()

conn = conectar()

cur = conn.cursor()

cur.execute("""
SELECT
    id_ordem,
    data_servico,
    tipo_dia,
    status
FROM ordens_servico
ORDER BY data_servico DESC
""")

st.dataframe(
    cur.fetchall(),
    use_container_width=True
)

cur.close()
conn.close()