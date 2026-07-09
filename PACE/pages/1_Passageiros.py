import streamlit as st
from database.conexao import conectar
from services.autenticacao import exigir_login, renderizar_menu_usuario

st.set_page_config(page_title="Passageiros - PACE", page_icon="👤", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("👤 Cadastro de Passageiros")


def listar_passageiros(apenas_ativos=True):
    conn = conectar()
    cur = conn.cursor()

    try:
        sql = """
            SELECT id_passageiro, nome, telefone, rua, numero, bairro,
                   complemento, observacoes, responsavel, idade,
                   tempo_no_programa, ativo
            FROM passageiros
        """
        if apenas_ativos:
            sql += " WHERE ativo = TRUE"
        sql += " ORDER BY nome"

        cur.execute(sql)
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_passageiro(id_passageiro):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_passageiro, nome, telefone, rua, numero, bairro,
                   complemento, observacoes, responsavel, idade,
                   tempo_no_programa, ativo
            FROM passageiros
            WHERE id_passageiro = %s
            """,
            (id_passageiro,),
        )
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def cadastrar_passageiro(
    nome, telefone, rua, numero, bairro, complemento, observacoes,
    responsavel, idade, tempo_no_programa,
):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO passageiros
                (nome, telefone, rua, numero, bairro, complemento, observacoes,
                 responsavel, idade, tempo_no_programa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                nome, telefone, rua, numero, bairro, complemento, observacoes,
                responsavel, idade, tempo_no_programa,
            ),
        )
        conn.commit()
        return True, "Passageiro cadastrado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def atualizar_passageiro(
    id_passageiro, nome, telefone, rua, numero, bairro, complemento, observacoes,
    responsavel, idade, tempo_no_programa,
):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE passageiros
            SET nome = %s, telefone = %s, rua = %s, numero = %s,
                bairro = %s, complemento = %s, observacoes = %s,
                responsavel = %s, idade = %s, tempo_no_programa = %s
            WHERE id_passageiro = %s
            """,
            (
                nome, telefone, rua, numero, bairro, complemento, observacoes,
                responsavel, idade, tempo_no_programa, id_passageiro,
            ),
        )
        conn.commit()
        return True, "Passageiro atualizado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def excluir_passageiro(id_passageiro):
    """Exclusão lógica: marca ativo = false."""
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE passageiros SET ativo = FALSE WHERE id_passageiro = %s",
            (id_passageiro,),
        )
        conn.commit()
        return True, "Passageiro desativado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def reativar_passageiro(id_passageiro):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE passageiros SET ativo = TRUE WHERE id_passageiro = %s",
            (id_passageiro,),
        )
        conn.commit()
        return True, "Passageiro reativado!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


# --- Interface ---

if "editar_passageiro_id" not in st.session_state:
    st.session_state.editar_passageiro_id = None

tab_cadastro, tab_listagem = st.tabs(["Cadastrar / Editar", "Listagem"])

with tab_cadastro:
    editando = st.session_state.editar_passageiro_id is not None
    dados_edicao = None

    if editando:
        dados_edicao = buscar_passageiro(st.session_state.editar_passageiro_id)

    titulo_form = "✏️ Editar Passageiro" if editando else "➕ Novo Passageiro"

    with st.expander(titulo_form, expanded=True):
        with st.form("form_passageiro"):
            col1, col2 = st.columns(2)

            with col1:
                nome = st.text_input(
                    "Nome *",
                    value=dados_edicao[1] if dados_edicao else "",
                )
                responsavel = st.text_input(
                    "Responsável",
                    value=dados_edicao[8] or "" if dados_edicao else "",
                )
                idade = st.number_input(
                    "Idade",
                    min_value=0,
                    max_value=150,
                    step=1,
                    value=int(dados_edicao[9]) if dados_edicao and dados_edicao[9] is not None else 0,
                )
                tempo_no_programa = st.text_input(
                    "Tempo no programa",
                    value=dados_edicao[10] or "" if dados_edicao else "",
                    placeholder="Ex: 2 anos, 6 meses",
                )
                telefone = st.text_input(
                    "Telefone",
                    value=dados_edicao[2] or "" if dados_edicao else "",
                )

            with col2:
                rua = st.text_input(
                    "Rua",
                    value=dados_edicao[3] or "" if dados_edicao else "",
                )
                numero = st.text_input(
                    "Número",
                    value=dados_edicao[4] or "" if dados_edicao else "",
                )
                bairro = st.text_input(
                    "Bairro *",
                    value=dados_edicao[5] or "" if dados_edicao else "",
                )
                complemento = st.text_input(
                    "Complemento",
                    value=dados_edicao[6] or "" if dados_edicao else "",
                )
                observacoes = st.text_area(
                    "Observações",
                    value=dados_edicao[7] or "" if dados_edicao else "",
                )

            col_salvar, col_cancelar = st.columns(2)

            with col_salvar:
                salvar = st.form_submit_button("Salvar", use_container_width=True)

            with col_cancelar:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)

            if cancelar:
                st.session_state.editar_passageiro_id = None
                st.rerun()

            if salvar:
                idade_val = int(idade) if idade > 0 else None

                if not nome.strip():
                    st.warning("Informe o nome.")
                elif not bairro.strip():
                    st.warning("Informe o bairro.")
                elif editando:
                    ok, msg = atualizar_passageiro(
                        st.session_state.editar_passageiro_id,
                        nome.strip(),
                        telefone.strip() or None,
                        rua.strip() or None,
                        numero.strip() or None,
                        bairro.strip(),
                        complemento.strip() or None,
                        observacoes.strip() or None,
                        responsavel.strip() or None,
                        idade_val,
                        tempo_no_programa.strip() or None,
                    )
                    if ok:
                        st.success(msg)
                        st.session_state.editar_passageiro_id = None
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    ok, msg = cadastrar_passageiro(
                        nome.strip(),
                        telefone.strip() or None,
                        rua.strip() or None,
                        numero.strip() or None,
                        bairro.strip(),
                        complemento.strip() or None,
                        observacoes.strip() or None,
                        responsavel.strip() or None,
                        idade_val,
                        tempo_no_programa.strip() or None,
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

with tab_listagem:
    col_filtro, col_inativos = st.columns([3, 1])

    with col_filtro:
        pesquisa = st.text_input("Pesquisar por nome")

    with col_inativos:
        mostrar_inativos = st.checkbox("Mostrar inativos")

    dados = listar_passageiros(apenas_ativos=not mostrar_inativos)

    if pesquisa:
        dados = [d for d in dados if pesquisa.lower() in d[1].lower()]

    st.metric("Total", len(dados))

    if not dados:
        st.info("Nenhum passageiro encontrado.")
    else:
        for registro in dados:
            (
                id_passageiro,
                nome,
                telefone,
                rua,
                numero,
                bairro,
                complemento,
                observacoes,
                responsavel,
                idade,
                tempo_no_programa,
                ativo,
            ) = registro

            status = "Ativo" if ativo else "Inativo"
            with st.expander(f"👤 {nome} — {status}"):
                c1, c2 = st.columns(2)

                with c1:
                    st.write(f"**Responsável:** {responsavel or '-'}")
                    st.write(f"**Idade:** {idade if idade is not None else '-'}")
                    st.write(f"**Tempo no programa:** {tempo_no_programa or '-'}")
                    st.write(f"**Telefone:** {telefone or '-'}")
                    st.write(f"**Rua:** {rua or '-'}")
                    st.write(f"**Número:** {numero or '-'}")

                with c2:
                    st.write(f"**Bairro:** {bairro}")
                    st.write(f"**Complemento:** {complemento or '-'}")
                    st.write(f"**Observações:** {observacoes or '-'}")

                b1, b2, b3 = st.columns(3)

                with b1:
                    if st.button("Editar", key=f"edit_{id_passageiro}"):
                        st.session_state.editar_passageiro_id = id_passageiro
                        st.rerun()

                with b2:
                    if ativo and st.button("Desativar", key=f"del_{id_passageiro}"):
                        ok, msg = excluir_passageiro(id_passageiro)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                with b3:
                    if not ativo and st.button("Reativar", key=f"reat_{id_passageiro}"):
                        ok, msg = reativar_passageiro(id_passageiro)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
