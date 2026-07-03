import streamlit as st
import pandas as pd
from datetime import date
from database.conexao import conectar
from services.gerador_ordens import gerar_ordens_servico
from services.autenticacao import exigir_login, renderizar_menu_usuario

st.set_page_config(page_title="Ordens de Serviço - PACE", page_icon="📄", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("📄 Ordens de Serviço")

TIPOS_DIA = ["UTIL", "SABADO", "DOMINGO", "FERIADO"]
STATUS_OPCOES = ["PROGRAMADA", "REALIZADA", "CANCELADA"]


def listar_ordens():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT o.id_ordem, o.data_servico, o.tipo_dia, v.numero_carro,
                   m.nome, o.km_inicial, o.km_final, o.status, o.observacoes,
                   o.id_veiculo, COUNT(osp.id_item) AS qtd_passageiros
            FROM ordens_servico o
            INNER JOIN veiculos v ON v.id_veiculo = o.id_veiculo
            INNER JOIN motoristas m ON m.id_motorista = v.id_motorista
            LEFT JOIN ordem_servico_passageiros osp ON osp.id_ordem = o.id_ordem
            GROUP BY o.id_ordem, v.numero_carro, m.nome
            ORDER BY o.data_servico DESC, v.numero_carro
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_ordem(id_ordem):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_ordem, data_servico, tipo_dia, id_veiculo,
                   km_inicial, km_final, observacoes, status
            FROM ordens_servico
            WHERE id_ordem = %s
            """,
            (id_ordem,),
        )
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def listar_passageiros_ordem(id_ordem):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT osp.sequencia_rota, p.nome, osp.bairro, osp.origem,
                   osp.destino, osp.horario_previsto
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


def atualizar_ordem(id_ordem, km_inicial, km_final, observacoes, status):
    conn = conectar()
    cur = conn.cursor()

    try:
        if km_inicial is not None and km_final is not None and km_final < km_inicial:
            return False, "Km final não pode ser menor que km inicial."

        cur.execute(
            """
            UPDATE ordens_servico
            SET km_inicial = %s, km_final = %s, observacoes = %s, status = %s
            WHERE id_ordem = %s
            """,
            (km_inicial, km_final, observacoes, status, id_ordem),
        )
        conn.commit()
        return True, "Ordem atualizada com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


# --- Interface ---

if "editar_ordem_id" not in st.session_state:
    st.session_state.editar_ordem_id = None

tab_gerar, tab_listagem = st.tabs(["Gerar Ordem", "Ordens Cadastradas"])

with tab_gerar:
    st.subheader("Gerar Ordens Automaticamente")

    st.markdown(
        """
        O sistema busca os passageiros agendados para o dia da semana da data informada,
        agrupa por bairro, distribui nos veículos disponíveis e cria uma ordem por veículo.
        """
    )

    with st.form("form_gerar_ordem"):
        c1, c2 = st.columns(2)

        with c1:
            data_servico = st.date_input("Data do serviço", value=date.today())

        with c2:
            tipo_dia = st.selectbox("Tipo do dia", TIPOS_DIA)

        gerar = st.form_submit_button("Gerar Ordem", use_container_width=True)

    if gerar:
        conn = conectar()

        try:
            ids = gerar_ordens_servico(conn, data_servico, tipo_dia)
            st.success(f"{len(ids)} ordem(ns) gerada(s): {', '.join(map(str, ids))}")
            st.rerun()

        except Exception as erro:
            st.error(str(erro))

        finally:
            conn.close()

with tab_listagem:
    ordens = listar_ordens()

    if not ordens:
        st.info("Nenhuma ordem de serviço cadastrada.")
    else:
        df_resumo = pd.DataFrame(
            ordens,
            columns=[
                "ID", "Data", "Tipo", "Carro", "Motorista",
                "Km Inicial", "Km Final", "Status", "Observações",
                "ID Veículo", "Passageiros",
            ],
        )
        st.dataframe(
            df_resumo[
                ["ID", "Data", "Tipo", "Carro", "Motorista", "Passageiros", "Status", "Km Inicial", "Km Final"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("Detalhes e Atualização")

        for ordem in ordens:
            (
                id_ordem,
                data_servico,
                tipo_dia,
                numero_carro,
                motorista,
                km_inicial,
                km_final,
                status,
                observacoes,
                _,
                qtd_passageiros,
            ) = ordem

            km_percorrido = None
            if km_inicial is not None and km_final is not None:
                km_percorrido = float(km_final) - float(km_inicial)

            titulo = f"Ordem #{id_ordem} — {data_servico} — Carro {numero_carro} ({status})"

            with st.expander(titulo):
                m1, m2, m3, m4 = st.columns(4)

                with m1:
                    st.metric("Passageiros", qtd_passageiros)

                with m2:
                    st.metric("Motorista", motorista)

                with m3:
                    st.metric("Tipo do dia", tipo_dia)

                with m4:
                    st.metric("Km percorrido", f"{km_percorrido:.1f}" if km_percorrido is not None else "-")

                passageiros = listar_passageiros_ordem(id_ordem)

                if passageiros:
                    st.markdown("**Rota — Passageiros**")
                    df_pass = pd.DataFrame(
                        passageiros,
                        columns=["Seq.", "Passageiro", "Bairro", "Origem", "Destino", "Horário"],
                    )
                    st.dataframe(df_pass, use_container_width=True, hide_index=True)

                with st.form(f"form_ordem_{id_ordem}"):
                    st.markdown("**Registrar execução**")

                    c1, c2, c3 = st.columns(3)

                    with c1:
                        km_ini = st.number_input(
                            "Km inicial",
                            min_value=0.0,
                            step=0.1,
                            value=float(km_inicial) if km_inicial is not None else 0.0,
                            key=f"km_ini_{id_ordem}",
                        )

                    with c2:
                        km_fim = st.number_input(
                            "Km final",
                            min_value=0.0,
                            step=0.1,
                            value=float(km_final) if km_final is not None else 0.0,
                            key=f"km_fim_{id_ordem}",
                        )

                    with c3:
                        status_sel = st.selectbox(
                            "Status",
                            STATUS_OPCOES,
                            index=STATUS_OPCOES.index(status),
                            key=f"status_{id_ordem}",
                        )

                    obs = st.text_area(
                        "Observações",
                        value=observacoes or "",
                        key=f"obs_{id_ordem}",
                    )

                    if st.form_submit_button("Salvar alterações", use_container_width=True):
                        km_ini_val = km_ini if km_ini > 0 else None
                        km_fim_val = km_fim if km_fim > 0 else None

                        ok, msg = atualizar_ordem(
                            id_ordem,
                            km_ini_val,
                            km_fim_val,
                            obs.strip() or None,
                            status_sel,
                        )

                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
