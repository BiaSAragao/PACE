import streamlit as st
from database.conexao import conectar
from services.autenticacao import exigir_login, renderizar_menu_usuario

st.set_page_config(page_title="Motoristas - PACE", page_icon="🚗", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("🚗 Cadastro de Motoristas")


def listar_motoristas():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT m.id_motorista, m.nome, m.telefone, m.status,
                   CASE WHEN v.id_veiculo IS NOT NULL THEN TRUE ELSE FALSE END AS vinculado
            FROM motoristas m
            LEFT JOIN veiculos v ON v.id_motorista = m.id_motorista
            ORDER BY m.nome
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_motorista(id_motorista):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id_motorista, nome, telefone, status FROM motoristas WHERE id_motorista = %s",
            (id_motorista,),
        )
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def cadastrar_motorista(nome, telefone):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO motoristas (nome, telefone) VALUES (%s, %s)",
            (nome, telefone),
        )
        conn.commit()
        return True, "Motorista cadastrado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def atualizar_motorista(id_motorista, nome, telefone, status):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE motoristas
            SET nome = %s, telefone = %s, status = %s
            WHERE id_motorista = %s
            """,
            (nome, telefone, status, id_motorista),
        )
        conn.commit()
        return True, "Motorista atualizado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def excluir_motorista(id_motorista):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT COUNT(*) FROM veiculos WHERE id_motorista = %s",
            (id_motorista,),
        )

        if cur.fetchone()[0] > 0:
            return False, "Este motorista está vinculado a um veículo e não pode ser excluído."

        cur.execute("DELETE FROM motoristas WHERE id_motorista = %s", (id_motorista,))
        conn.commit()
        return True, "Motorista excluído com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


# --- Interface ---

if "editar_motorista_id" not in st.session_state:
    st.session_state.editar_motorista_id = None

tab_cadastro, tab_listagem = st.tabs(["Cadastrar / Editar", "Listagem"])

with tab_cadastro:
    editando = st.session_state.editar_motorista_id is not None
    dados_edicao = buscar_motorista(st.session_state.editar_motorista_id) if editando else None

    with st.expander("✏️ Editar Motorista" if editando else "➕ Novo Motorista", expanded=True):
        with st.form("form_motorista"):
            nome = st.text_input("Nome *", value=dados_edicao[1] if dados_edicao else "")
            telefone = st.text_input("Telefone", value=dados_edicao[2] or "" if dados_edicao else "")

            status = True
            if editando:
                status = st.checkbox("Ativo", value=dados_edicao[3])

            col1, col2 = st.columns(2)

            with col1:
                salvar = st.form_submit_button("Salvar", use_container_width=True)

            with col2:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)

            if cancelar:
                st.session_state.editar_motorista_id = None
                st.rerun()

            if salvar:
                if not nome.strip():
                    st.warning("Informe o nome do motorista.")
                elif editando:
                    ok, msg = atualizar_motorista(
                        st.session_state.editar_motorista_id,
                        nome.strip(),
                        telefone.strip() or None,
                        status,
                    )
                    if ok:
                        st.success(msg)
                        st.session_state.editar_motorista_id = None
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    ok, msg = cadastrar_motorista(nome.strip(), telefone.strip() or None)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

with tab_listagem:
    pesquisa = st.text_input("Pesquisar por nome")
    dados = listar_motoristas()

    if pesquisa:
        dados = [d for d in dados if pesquisa.lower() in d[1].lower()]

    st.metric("Total", len(dados))

    if not dados:
        st.info("Nenhum motorista encontrado.")
    else:
        for registro in dados:
            id_motorista, nome, telefone, status, vinculado = registro
            status_txt = "Ativo" if status else "Inativo"
            veiculo_txt = "Sim" if vinculado else "Não"

            with st.expander(f"🚗 {nome} — {status_txt}"):
                c1, c2 = st.columns(2)

                with c1:
                    st.write(f"**Telefone:** {telefone or '-'}")
                    st.write(f"**Status:** {status_txt}")

                with c2:
                    st.write(f"**Vinculado a veículo:** {veiculo_txt}")

                b1, b2 = st.columns(2)

                with b1:
                    if st.button("Editar", key=f"edit_{id_motorista}"):
                        st.session_state.editar_motorista_id = id_motorista
                        st.rerun()

                with b2:
                    if st.button("Excluir", key=f"del_{id_motorista}", disabled=vinculado):
                        ok, msg = excluir_motorista(id_motorista)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                    if vinculado:
                        st.caption("Motorista vinculado a veículo.")
