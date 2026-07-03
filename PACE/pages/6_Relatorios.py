import streamlit as st
import pandas as pd
from datetime import date
from database.conexao import conectar
from services.autenticacao import exigir_login, renderizar_menu_usuario

st.set_page_config(page_title="Relatórios - PACE", page_icon="📊", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("📊 Relatórios de Ordens de Serviço")


def listar_veiculos_filtro():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT v.id_veiculo, v.numero_carro
            FROM veiculos v
            ORDER BY v.numero_carro
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def listar_motoristas_filtro():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id_motorista, nome FROM motoristas ORDER BY nome"
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_relatorio(data_filtro, id_veiculo, id_motorista, status_filtro):
    conn = conectar()
    cur = conn.cursor()

    try:
        sql = """
            SELECT
                o.id_ordem,
                o.data_servico,
                o.tipo_dia,
                o.status,
                v.numero_carro,
                v.placa,
                m.nome AS motorista,
                o.km_inicial,
                o.km_final,
                o.observacoes
            FROM ordens_servico o
            INNER JOIN veiculos v ON v.id_veiculo = o.id_veiculo
            INNER JOIN motoristas m ON m.id_motorista = v.id_motorista
            WHERE 1=1
        """
        params = []

        if data_filtro:
            sql += " AND o.data_servico = %s"
            params.append(data_filtro)

        if id_veiculo:
            sql += " AND v.id_veiculo = %s"
            params.append(id_veiculo)

        if id_motorista:
            sql += " AND m.id_motorista = %s"
            params.append(id_motorista)

        if status_filtro and status_filtro != "TODOS":
            sql += " AND o.status = %s"
            params.append(status_filtro)

        sql += " ORDER BY o.data_servico DESC, v.numero_carro"

        cur.execute(sql, params)
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_passageiros_ordem(id_ordem):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT osp.sequencia_rota, p.nome, osp.bairro, osp.destino, osp.horario_previsto
            FROM ordem_servico_passageiros osp
            INNER JOIN passageiros p ON p.id_passageiro = osp.id_passageiro
            WHERE osp.id_ordem = %s
            ORDER BY osp.sequencia_rota
            """,
            (id_ordem,),
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


# --- Filtros ---

with st.expander("🔍 Filtros", expanded=True):
    c1, c2, c3, c4 = st.columns(4)

    veiculos = listar_veiculos_filtro()
    motoristas = listar_motoristas_filtro()

    mapa_veiculos = {"Todos": None}
    mapa_veiculos.update({f"Carro {v[1]}": v[0] for v in veiculos})

    mapa_motoristas = {"Todos": None}
    mapa_motoristas.update({m[1]: m[0] for m in motoristas})

    with c1:
        usar_data = st.checkbox("Filtrar por data", value=False)
        data_filtro = st.date_input("Data", value=date.today(), disabled=not usar_data)
        data_val = data_filtro if usar_data else None

    with c2:
        veiculo_sel = st.selectbox("Veículo", list(mapa_veiculos.keys()))

    with c3:
        motorista_sel = st.selectbox("Motorista", list(mapa_motoristas.keys()))

    with c4:
        status_sel = st.selectbox(
            "Status",
            ["TODOS", "PROGRAMADA", "REALIZADA", "CANCELADA"],
        )

    aplicar = st.button("Aplicar filtros", use_container_width=True)

# Busca inicial ou após aplicar filtros
ordens = buscar_relatorio(
    data_val if usar_data else None,
    mapa_veiculos[veiculo_sel],
    mapa_motoristas[motorista_sel],
    status_sel,
)

# Métricas resumidas
programadas = len([o for o in ordens if o[3] == "PROGRAMADA"])
realizadas = len([o for o in ordens if o[3] == "REALIZADA"])
canceladas = len([o for o in ordens if o[3] == "CANCELADA"])

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Total de ordens", len(ordens))

with m2:
    st.metric("Programadas", programadas)

with m3:
    st.metric("Realizadas", realizadas)

with m4:
    st.metric("Canceladas", canceladas)

st.divider()

if not ordens:
    st.info("Nenhuma ordem encontrada com os filtros selecionados.")
else:
    tab_programadas, tab_realizadas, tab_todas = st.tabs(
        ["Programadas", "Realizadas", "Todas"]
    )

    def renderizar_ordens(lista_ordens, tab):
        with tab:
            if not lista_ordens:
                st.info("Nenhuma ordem nesta categoria.")
                return

            for ordem in lista_ordens:
                (
                    id_ordem,
                    data_servico,
                    tipo_dia,
                    status,
                    numero_carro,
                    placa,
                    motorista,
                    km_inicial,
                    km_final,
                    observacoes,
                ) = ordem

                km_total = None
                if km_inicial is not None and km_final is not None:
                    km_total = float(km_final) - float(km_inicial)

                with st.expander(
                    f"Ordem #{id_ordem} — {data_servico} — Carro {numero_carro} — {status}"
                ):
                    c1, c2 = st.columns(2)

                    with c1:
                        st.write(f"**Motorista:** {motorista}")
                        st.write(f"**Placa:** {placa or '-'}")
                        st.write(f"**Tipo do dia:** {tipo_dia}")

                    with c2:
                        st.write(f"**Km inicial:** {km_inicial if km_inicial is not None else '-'}")
                        st.write(f"**Km final:** {km_final if km_final is not None else '-'}")
                        st.write(
                            f"**Quilometragem:** {km_total:.1f} km"
                            if km_total is not None
                            else "**Quilometragem:** -"
                        )

                    if observacoes:
                        st.write(f"**Observações:** {observacoes}")

                    passageiros = buscar_passageiros_ordem(id_ordem)

                    if passageiros:
                        st.markdown("**Passageiros da ordem**")
                        df = pd.DataFrame(
                            passageiros,
                            columns=["Seq.", "Passageiro", "Bairro", "Destino", "Horário"],
                        )
                        st.dataframe(df, use_container_width=True, hide_index=True)

    renderizar_ordens([o for o in ordens if o[3] == "PROGRAMADA"], tab_programadas)
    renderizar_ordens([o for o in ordens if o[3] == "REALIZADA"], tab_realizadas)
    renderizar_ordens(ordens, tab_todas)
