import streamlit as st
from database.conexao import conectar
from services.autenticacao import exigir_login, renderizar_menu_usuario

st.set_page_config(page_title="Veículos - PACE", page_icon="🚐", layout="wide")

exigir_login()
renderizar_menu_usuario()

st.title("🚐 Cadastro de Veículos")


def listar_motoristas_disponiveis(id_motorista_atual=None):
    """Motoristas ativos sem veículo, ou o motorista atual em edição."""
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_motorista, nome
            FROM motoristas
            WHERE status = TRUE
              AND (
                  id_motorista NOT IN (SELECT id_motorista FROM veiculos)
                  OR id_motorista = %s
              )
            ORDER BY nome
            """,
            (id_motorista_atual,),
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def listar_veiculos():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT v.id_veiculo, v.numero_carro, v.placa, v.capacidade,
                   m.nome, v.status, v.id_motorista
            FROM veiculos v
            INNER JOIN motoristas m ON m.id_motorista = v.id_motorista
            ORDER BY v.numero_carro
            """
        )
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def buscar_veiculo(id_veiculo):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id_veiculo, numero_carro, placa, capacidade, id_motorista, status
            FROM veiculos
            WHERE id_veiculo = %s
            """,
            (id_veiculo,),
        )
        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def cadastrar_veiculo(numero, placa, capacidade, id_motorista):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO veiculos (numero_carro, placa, capacidade, id_motorista)
            VALUES (%s, %s, %s, %s)
            """,
            (numero, placa, capacidade, id_motorista),
        )
        conn.commit()
        return True, "Veículo cadastrado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def atualizar_veiculo(id_veiculo, numero, placa, capacidade, id_motorista, status):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE veiculos
            SET numero_carro = %s, placa = %s, capacidade = %s,
                id_motorista = %s, status = %s
            WHERE id_veiculo = %s
            """,
            (numero, placa, capacidade, id_motorista, status, id_veiculo),
        )
        conn.commit()
        return True, "Veículo atualizado com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


def excluir_veiculo(id_veiculo):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT COUNT(*) FROM ordens_servico WHERE id_veiculo = %s",
            (id_veiculo,),
        )

        if cur.fetchone()[0] > 0:
            return False, "Este veículo possui ordens de serviço e não pode ser excluído."

        cur.execute("DELETE FROM veiculos WHERE id_veiculo = %s", (id_veiculo,))
        conn.commit()
        return True, "Veículo excluído com sucesso!"

    except Exception as erro:
        conn.rollback()
        return False, str(erro)

    finally:
        cur.close()
        conn.close()


# --- Interface ---

if "editar_veiculo_id" not in st.session_state:
    st.session_state.editar_veiculo_id = None

tab_cadastro, tab_listagem = st.tabs(["Cadastrar / Editar", "Listagem"])

with tab_cadastro:
    editando = st.session_state.editar_veiculo_id is not None
    dados_edicao = buscar_veiculo(st.session_state.editar_veiculo_id) if editando else None
    id_motorista_atual = dados_edicao[4] if dados_edicao else None

    motoristas = listar_motoristas_disponiveis(id_motorista_atual)

    if not motoristas and not editando:
        st.warning("Cadastre um motorista disponível antes de cadastrar um veículo.")
    else:
        mapa_motoristas = {m[1]: m[0] for m in motoristas}
        nome_motorista_atual = next(
            (m[1] for m in motoristas if m[0] == id_motorista_atual),
            list(mapa_motoristas.keys())[0] if mapa_motoristas else "",
        )

        with st.expander("✏️ Editar Veículo" if editando else "➕ Novo Veículo", expanded=True):
            with st.form("form_veiculo"):
                c1, c2 = st.columns(2)

                with c1:
                    numero = st.number_input(
                        "Número do carro *",
                        min_value=1,
                        step=1,
                        value=int(dados_edicao[1]) if dados_edicao else 1,
                    )
                    placa = st.text_input(
                        "Placa",
                        value=dados_edicao[2] or "" if dados_edicao else "",
                    )

                with c2:
                    capacidade = st.number_input(
                        "Capacidade *",
                        min_value=1,
                        max_value=20,
                        step=1,
                        value=int(dados_edicao[3]) if dados_edicao else 4,
                    )
                    motorista_sel = st.selectbox(
                        "Motorista *",
                        list(mapa_motoristas.keys()),
                        index=list(mapa_motoristas.keys()).index(nome_motorista_atual)
                        if nome_motorista_atual in mapa_motoristas
                        else 0,
                    )

                status = True
                if editando:
                    status = st.checkbox("Ativo", value=dados_edicao[5])

                c_salvar, c_cancelar = st.columns(2)

                with c_salvar:
                    salvar = st.form_submit_button("Salvar", use_container_width=True)

                with c_cancelar:
                    cancelar = st.form_submit_button("Cancelar", use_container_width=True)

                if cancelar:
                    st.session_state.editar_veiculo_id = None
                    st.rerun()

                if salvar:
                    placa_fmt = placa.strip().upper() if placa.strip() else None
                    id_motorista = mapa_motoristas[motorista_sel]

                    if editando:
                        ok, msg = atualizar_veiculo(
                            st.session_state.editar_veiculo_id,
                            numero,
                            placa_fmt,
                            capacidade,
                            id_motorista,
                            status,
                        )
                    else:
                        ok, msg = cadastrar_veiculo(numero, placa_fmt, capacidade, id_motorista)

                    if ok:
                        st.success(msg)
                        st.session_state.editar_veiculo_id = None
                        st.rerun()
                    else:
                        st.error(msg)

with tab_listagem:
    dados = listar_veiculos()
    st.metric("Total", len(dados))

    if not dados:
        st.info("Nenhum veículo cadastrado.")
    else:
        for registro in dados:
            id_veiculo, numero, placa, capacidade, motorista, status, _ = registro
            status_txt = "Ativo" if status else "Inativo"

            with st.expander(f"🚐 Carro {numero} — {status_txt}"):
                c1, c2 = st.columns(2)

                with c1:
                    st.write(f"**Placa:** {placa or '-'}")
                    st.write(f"**Capacidade:** {capacidade}")

                with c2:
                    st.write(f"**Motorista:** {motorista}")
                    st.write(f"**Status:** {status_txt}")

                b1, b2 = st.columns(2)

                with b1:
                    if st.button("Editar", key=f"edit_{id_veiculo}"):
                        st.session_state.editar_veiculo_id = id_veiculo
                        st.rerun()

                with b2:
                    if st.button("Excluir", key=f"del_{id_veiculo}"):
                        ok, msg = excluir_veiculo(id_veiculo)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
