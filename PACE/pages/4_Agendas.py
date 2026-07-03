import streamlit as st
from datetime import time
from database.conexao import conectar
from services.autenticacao import exigir_login, renderizar_menu_usuario

st.set_page_config(page_title="Agendas - PACE", page_icon="📅", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("📅 Agenda dos Passageiros")

DIAS_SEMANA = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def listar_passageiros_ativos():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_passageiro, nome, telefone, bairro
            FROM passageiros
            WHERE ativo = TRUE
            ORDER BY nome
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def listar_agendas():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT a.id_agenda, p.nome, a.dia_semana, a.horario_saida,
                   a.horario_retorno, a.destino, a.ativo, p.telefone, p.bairro,
                   a.id_passageiro
            FROM agenda_passageiros a
            INNER JOIN passageiros p ON p.id_passageiro = a.id_passageiro
            ORDER BY p.nome, a.dia_semana
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_agenda(id_agenda):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_agenda, id_passageiro, dia_semana, horario_saida,
                   horario_retorno, destino, ativo
            FROM agenda_passageiros
            WHERE id_agenda = %s
            """,
            (id_agenda,),
        )
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def agenda_duplicada(id_passageiro, dia_semana, id_agenda_excluir=None):
    """Verifica se já existe agenda ativa para o mesmo passageiro e dia."""
    conn = conectar()
    cur = conn.cursor()

    try:
        sql = """
            SELECT COUNT(*)
            FROM agenda_passageiros
            WHERE id_passageiro = %s
              AND dia_semana = %s
              AND ativo = TRUE
        """
        params = [id_passageiro, dia_semana]

        if id_agenda_excluir:
            sql += " AND id_agenda != %s"
            params.append(id_agenda_excluir)

        cur.execute(sql, params)
        return cur.fetchone()[0] > 0

    finally:
        cur.close()
        conn.close()


def cadastrar_agenda(id_passageiro, dia_semana, horario_saida, horario_retorno, destino):
    conn = conectar()
    cur = conn.cursor()

    try:
        if agenda_duplicada(id_passageiro, dia_semana):
            return False, "Este passageiro já possui agenda para este dia da semana."

        cur.execute(
            """
            INSERT INTO agenda_passageiros
                (id_passageiro, dia_semana, horario_saida, horario_retorno, destino)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_passageiro, dia_semana, horario_saida, horario_retorno, destino),
        )
        conn.commit()
        return True, "Agenda cadastrada com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def atualizar_agenda(id_agenda, id_passageiro, dia_semana, horario_saida, horario_retorno, destino, ativo):
    conn = conectar()
    cur = conn.cursor()

    try:
        if ativo and agenda_duplicada(id_passageiro, dia_semana, id_agenda):
            return False, "Este passageiro já possui agenda para este dia da semana."

        cur.execute(
            """
            UPDATE agenda_passageiros
            SET id_passageiro = %s, dia_semana = %s, horario_saida = %s,
                horario_retorno = %s, destino = %s, ativo = %s
            WHERE id_agenda = %s
            """,
            (id_passageiro, dia_semana, horario_saida, horario_retorno, destino, ativo, id_agenda),
        )
        conn.commit()
        return True, "Agenda atualizada com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def desativar_agenda(id_agenda):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE agenda_passageiros SET ativo = FALSE WHERE id_agenda = %s",
            (id_agenda,),
        )
        conn.commit()
        return True, "Agenda desativada!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


# --- Interface ---

passageiros = listar_passageiros_ativos()

if not passageiros:
    st.warning("Cadastre passageiros ativos antes de criar agendas.")
    st.stop()

mapa_passageiros = {p[1]: p[0] for p in passageiros}
info_passageiros = {p[0]: {"telefone": p[2], "bairro": p[3]} for p in passageiros}

if "editar_agenda_id" not in st.session_state:
    st.session_state.editar_agenda_id = None

tab_cadastro, tab_listagem = st.tabs(["Cadastrar / Editar", "Listagem"])

with tab_cadastro:
    editando = st.session_state.editar_agenda_id is not None
    dados_edicao = buscar_agenda(st.session_state.editar_agenda_id) if editando else None

    nome_edicao = next(
        (p[1] for p in passageiros if p[0] == dados_edicao[1]),
        list(mapa_passageiros.keys())[0],
    ) if dados_edicao else list(mapa_passageiros.keys())[0]

    with st.expander("✏️ Editar Agenda" if editando else "➕ Nova Agenda", expanded=True):
        with st.form("form_agenda"):
            passageiro_sel = st.selectbox(
                "Passageiro *",
                list(mapa_passageiros.keys()),
                index=list(mapa_passageiros.keys()).index(nome_edicao),
            )

            id_sel = mapa_passageiros[passageiro_sel]
            info = info_passageiros[id_sel]

            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**Telefone:** {info['telefone'] or '-'}")
            with c2:
                st.info(f"**Bairro:** {info['bairro']}")

            dia_opcoes = list(DIAS_SEMANA.keys())
            dia_labels = [DIAS_SEMANA[d] for d in dia_opcoes]
            dia_idx = dia_opcoes.index(dados_edicao[2]) if dados_edicao else 0

            dia_sel = st.selectbox(
                "Dia da semana *",
                dia_labels,
                index=dia_idx,
            )
            dia_semana = dia_opcoes[dia_labels.index(dia_sel)]

            c3, c4 = st.columns(2)

            with c3:
                horario_saida = st.time_input(
                    "Horário de saída",
                    value=dados_edicao[3] if dados_edicao and dados_edicao[3] else time(7, 0),
                )

            with c4:
                horario_retorno = st.time_input(
                    "Horário de retorno",
                    value=dados_edicao[4] if dados_edicao and dados_edicao[4] else time(17, 0),
                )

            destino = st.text_input(
                "Destino",
                value=dados_edicao[5] or "" if dados_edicao else "",
            )

            ativo = True
            if editando:
                ativo = st.checkbox("Ativa", value=dados_edicao[6])

            c_salvar, c_cancelar = st.columns(2)

            with c_salvar:
                salvar = st.form_submit_button("Salvar", use_container_width=True)

            with c_cancelar:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)

            if cancelar:
                st.session_state.editar_agenda_id = None
                st.rerun()

            if salvar:
                destino_fmt = destino.strip() or None

                if editando:
                    ok, msg = atualizar_agenda(
                        st.session_state.editar_agenda_id,
                        id_sel,
                        dia_semana,
                        horario_saida,
                        horario_retorno,
                        destino_fmt,
                        ativo,
                    )
                else:
                    ok, msg = cadastrar_agenda(
                        id_sel,
                        dia_semana,
                        horario_saida,
                        horario_retorno,
                        destino_fmt,
                    )

                if ok:
                    st.success(msg)
                    st.session_state.editar_agenda_id = None
                    st.rerun()
                else:
                    st.error(msg)

with tab_listagem:
    mostrar_inativas = st.checkbox("Mostrar agendas inativas")
    dados = listar_agendas()

    if not mostrar_inativas:
        dados = [d for d in dados if d[6]]

    st.metric("Total", len(dados))

    if not dados:
        st.info("Nenhuma agenda encontrada.")
    else:
        for registro in dados:
            (
                id_agenda,
                nome,
                dia_semana,
                horario_saida,
                horario_retorno,
                destino,
                ativo,
                telefone,
                bairro,
                _,
            ) = registro

            dia_nome = DIAS_SEMANA.get(dia_semana, str(dia_semana))
            status = "Ativa" if ativo else "Inativa"

            with st.expander(f"📅 {nome} — {dia_nome} ({status})"):
                c1, c2 = st.columns(2)

                with c1:
                    st.write(f"**Telefone:** {telefone or '-'}")
                    st.write(f"**Bairro:** {bairro}")
                    st.write(f"**Saída:** {horario_saida or '-'}")

                with c2:
                    st.write(f"**Retorno:** {horario_retorno or '-'}")
                    st.write(f"**Destino:** {destino or '-'}")

                b1, b2 = st.columns(2)

                with b1:
                    if st.button("Editar", key=f"edit_{id_agenda}"):
                        st.session_state.editar_agenda_id = id_agenda
                        st.rerun()

                with b2:
                    if ativo and st.button("Desativar", key=f"del_{id_agenda}"):
                        ok, msg = desativar_agenda(id_agenda)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
