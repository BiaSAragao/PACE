"""
Autenticação de usuários com bcrypt e controle de sessão Streamlit.
"""

import streamlit as st
import bcrypt
from database.conexao import conectar


def inicializar_sessao():
    """Garante que as chaves de sessão existam."""
    if "logado" not in st.session_state:
        st.session_state["logado"] = False
        st.session_state["id_usuario"] = None
        st.session_state["nome_usuario"] = None
        st.session_state["usuario"] = None


def hash_senha(senha):
    """Gera hash bcrypt da senha informada."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha, senha_hash):
    """Compara senha informada com o hash armazenado no banco."""
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def criar_admin_inicial():
    """
    Se a tabela usuarios estiver vazia, cria o administrador padrão.
    Senha inicial: admin123 (hash bcrypt).
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total = cur.fetchone()[0]

        if total == 0:
            senha_hash = hash_senha("admin123")
            cur.execute(
                """
                INSERT INTO usuarios (nome, usuario, senha_hash)
                VALUES (%s, %s, %s)
                """,
                ("Administrador", "admin", senha_hash),
            )
            conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def autenticar(usuario, senha):
    """
    Valida credenciais no banco.
    Retorna (sucesso, id_usuario, nome, usuario).
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_usuario, nome, usuario, senha_hash
            FROM usuarios
            WHERE usuario = %s AND ativo = TRUE
            """,
            (usuario.strip(),),
        )
        registro = cur.fetchone()

        if registro and verificar_senha(senha, registro[3]):
            return True, registro[0], registro[1], registro[2]

        return False, None, None, None

    finally:
        cur.close()
        conn.close()


def exigir_login():
    """Bloqueia acesso à página se o usuário não estiver autenticado."""
    inicializar_sessao()

    if not st.session_state.get("logado"):
        st.warning("Faça login para acessar o sistema.")
        st.stop()


def logout():
    """Encerra a sessão e limpa o estado."""
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]

    st.session_state["logado"] = False


def renderizar_menu_usuario():
    """Exibe nome do usuário e botão Sair na barra lateral."""
    inicializar_sessao()

    if st.session_state.get("logado"):
        st.sidebar.markdown(f"**Usuário:** {st.session_state.get('nome_usuario', '')}")

        if st.sidebar.button("Sair"):
            logout()
            st.rerun()


def tela_login():
    """Renderiza a tela de login centralizada."""
    inicializar_sessao()
    criar_admin_inicial()

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col_centro, _ = st.columns([1, 1.2, 1])

    with col_centro:
        st.markdown("## Sistema PACE")
        st.markdown("")

        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

            if entrar:
                if not usuario.strip() or not senha:
                    st.error("Informe usuário e senha.")
                else:
                    ok, id_usuario, nome, login = autenticar(usuario, senha)

                    if ok:
                        st.session_state["logado"] = True
                        st.session_state["id_usuario"] = id_usuario
                        st.session_state["nome_usuario"] = nome
                        st.session_state["usuario"] = login
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos.")
