import streamlit as st
from database.conexao import conectar
from services.autenticacao import exigir_login, renderizar_menu_usuario, hash_senha

st.set_page_config(page_title="Usuários - PACE", page_icon="🔐", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("🔐 Cadastro de Usuários")


def listar_usuarios():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_usuario, nome, usuario, ativo
            FROM usuarios
            ORDER BY nome
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_usuario(id_usuario):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_usuario, nome, usuario, ativo
            FROM usuarios
            WHERE id_usuario = %s
            """,
            (id_usuario,),
        )
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def usuario_duplicado(usuario, id_usuario_excluir=None):
    conn = conectar()
    cur = conn.cursor()

    try:
        sql = "SELECT COUNT(*) FROM usuarios WHERE usuario = %s"
        params = [usuario.strip()]

        if id_usuario_excluir:
            sql += " AND id_usuario != %s"
            params.append(id_usuario_excluir)

        cur.execute(sql, params)
        return cur.fetchone()[0] > 0

    finally:
        cur.close()
        conn.close()


def cadastrar_usuario(nome, usuario, senha):
    conn = conectar()
    cur = conn.cursor()

    try:
        if usuario_duplicado(usuario):
            return False, "Este nome de usuário já está em uso."

        senha_hash = hash_senha(senha)

        cur.execute(
            """
            INSERT INTO usuarios (nome, usuario, senha_hash)
            VALUES (%s, %s, %s)
            """,
            (nome.strip(), usuario.strip(), senha_hash),
        )
        conn.commit()
        return True, "Usuário cadastrado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def atualizar_nome(id_usuario, nome):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE usuarios SET nome = %s WHERE id_usuario = %s",
            (nome.strip(), id_usuario),
        )
        conn.commit()
        return True, "Nome atualizado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def redefinir_senha(id_usuario, nova_senha):
    conn = conectar()
    cur = conn.cursor()

    try:
        senha_hash = hash_senha(nova_senha)

        cur.execute(
            "UPDATE usuarios SET senha_hash = %s WHERE id_usuario = %s",
            (senha_hash, id_usuario),
        )
        conn.commit()
        return True, "Senha redefinida com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def alterar_status(id_usuario, ativo):
    conn = conectar()
    cur = conn.cursor()

    try:
        # Impede desativar o próprio usuário logado
        if id_usuario == st.session_state.get("id_usuario") and not ativo:
            return False, "Você não pode desativar o seu próprio usuário."

        cur.execute(
            "UPDATE usuarios SET ativo = %s WHERE id_usuario = %s",
            (ativo, id_usuario),
        )
        conn.commit()
        return True, "Status atualizado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


# --- Interface ---

if "editar_usuario_id" not in st.session_state:
    st.session_state.editar_usuario_id = None

if "redefinir_senha_id" not in st.session_state:
    st.session_state.redefinir_senha_id = None

tab_cadastro, tab_listagem = st.tabs(["Cadastrar / Editar", "Listagem"])

with tab_cadastro:
    editando = st.session_state.editar_usuario_id is not None
    dados_edicao = buscar_usuario(st.session_state.editar_usuario_id) if editando else None

    with st.expander("✏️ Editar Usuário" if editando else "➕ Novo Usuário", expanded=True):
        with st.form("form_usuario"):
            nome = st.text_input(
                "Nome *",
                value=dados_edicao[1] if dados_edicao else "",
            )

            if editando:
                st.text_input("Login", value=dados_edicao[2], disabled=True)
                ativo = st.checkbox("Ativo", value=dados_edicao[3])
            else:
                usuario = st.text_input("Usuário (login) *")
                senha = st.text_input("Senha *", type="password")
                confirmar = st.text_input("Confirmar senha *", type="password")

            c1, c2 = st.columns(2)

            with c1:
                salvar = st.form_submit_button("Salvar", use_container_width=True)

            with c2:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)

            if cancelar:
                st.session_state.editar_usuario_id = None
                st.rerun()

            if salvar:
                if not nome.strip():
                    st.warning("Informe o nome.")
                elif editando:
                    ok, msg = atualizar_nome(st.session_state.editar_usuario_id, nome)

                    if ok and dados_edicao[3] != ativo:
                        ok_status, msg_status = alterar_status(
                            st.session_state.editar_usuario_id,
                            ativo,
                        )
                        ok = ok and ok_status
                        msg = msg_status if not ok_status else msg

                    if ok:
                        if st.session_state.get("id_usuario") == st.session_state.editar_usuario_id:
                            st.session_state["nome_usuario"] = nome.strip()

                        st.success(msg)
                        st.session_state.editar_usuario_id = None
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    if not usuario.strip():
                        st.warning("Informe o usuário (login).")
                    elif not senha:
                        st.warning("Informe a senha.")
                    elif senha != confirmar:
                        st.warning("As senhas não conferem.")
                    else:
                        ok, msg = cadastrar_usuario(nome, usuario, senha)

                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    if st.session_state.redefinir_senha_id is not None:
        usuario_senha = buscar_usuario(st.session_state.redefinir_senha_id)

        with st.expander(f"🔑 Redefinir senha — {usuario_senha[2]}", expanded=True):
            with st.form("form_senha"):
                nova_senha = st.text_input("Nova senha *", type="password")
                confirmar_senha = st.text_input("Confirmar nova senha *", type="password")

                c1, c2 = st.columns(2)

                with c1:
                    salvar_senha = st.form_submit_button("Salvar senha", use_container_width=True)

                with c2:
                    cancelar_senha = st.form_submit_button("Cancelar", use_container_width=True)

                if cancelar_senha:
                    st.session_state.redefinir_senha_id = None
                    st.rerun()

                if salvar_senha:
                    if not nova_senha:
                        st.warning("Informe a nova senha.")
                    elif nova_senha != confirmar_senha:
                        st.warning("As senhas não conferem.")
                    else:
                        ok, msg = redefinir_senha(
                            st.session_state.redefinir_senha_id,
                            nova_senha,
                        )

                        if ok:
                            st.success(msg)
                            st.session_state.redefinir_senha_id = None
                            st.rerun()
                        else:
                            st.error(msg)

with tab_listagem:
    usuarios = listar_usuarios()
    st.metric("Total", len(usuarios))

    if not usuarios:
        st.info("Nenhum usuário cadastrado.")
    else:
        for registro in usuarios:
            id_usuario, nome, usuario, ativo = registro
            status = "Ativo" if ativo else "Inativo"

            with st.expander(f"🔐 {nome} ({usuario}) — {status}"):
                c1, c2 = st.columns(2)

                with c1:
                    st.write(f"**Login:** {usuario}")

                with c2:
                    st.write(f"**Status:** {status}")

                b1, b2, b3 = st.columns(3)

                with b1:
                    if st.button("Editar", key=f"edit_{id_usuario}"):
                        st.session_state.editar_usuario_id = id_usuario
                        st.session_state.redefinir_senha_id = None
                        st.rerun()

                with b2:
                    if st.button("Redefinir senha", key=f"senha_{id_usuario}"):
                        st.session_state.redefinir_senha_id = id_usuario
                        st.session_state.editar_usuario_id = None
                        st.rerun()

                with b3:
                    if ativo:
                        if st.button("Desativar", key=f"off_{id_usuario}"):
                            ok, msg = alterar_status(id_usuario, False)

                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        if st.button("Ativar", key=f"on_{id_usuario}"):
                            ok, msg = alterar_status(id_usuario, True)

                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
