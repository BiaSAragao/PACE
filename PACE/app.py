import streamlit as st
from database.conexao import conectar
from services.autenticacao import (
    inicializar_sessao,
    tela_login,
    renderizar_menu_usuario,
)

st.set_page_config(
    page_title="PACE",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="expanded",
)

inicializar_sessao()

if not st.session_state.get("logado"):
    tela_login()
    st.stop()

renderizar_menu_usuario()

st.title("🚐 Sistema de Gestão de Carros Especiais - PACE")

st.markdown("---")

st.markdown(
    """
### Bem-vindo!

Este sistema foi desenvolvido para auxiliar na gestão dos carros especiais do **PACE**.

### Funcionalidades

- 👤 Cadastro de passageiros
- 🚗 Cadastro de motoristas
- 🚐 Cadastro de veículos
- 📅 Cadastro da agenda dos passageiros
- 📄 Geração automática de Ordens de Serviço
- 📊 Relatórios

---

### Como utilizar

Escolha uma opção no **menu lateral** para começar.
"""
)

st.info("Utilize o menu à esquerda para navegar entre as funcionalidades do sistema.")

st.markdown("---")


def contar_registros():
    """Busca totais para exibir nos cards da página inicial."""
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM passageiros WHERE ativo = TRUE")
        total_passageiros = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM veiculos WHERE status = TRUE")
        total_veiculos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM motoristas WHERE status = TRUE")
        total_motoristas = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ordens_servico WHERE status = 'PROGRAMADA'")
        ordens_programadas = cur.fetchone()[0]

        return total_passageiros, total_veiculos, total_motoristas, ordens_programadas

    except Exception:
        return 0, 0, 0, 0

    finally:
        cur.close()
        conn.close()


try:
    total_passageiros, total_veiculos, total_motoristas, ordens_programadas = contar_registros()
except Exception:
    total_passageiros = total_veiculos = total_motoristas = ordens_programadas = "-"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Passageiros ativos", total_passageiros)

with col2:
    st.metric("Veículos ativos", total_veiculos)

with col3:
    st.metric("Motoristas ativos", total_motoristas)

with col4:
    st.metric("Ordens programadas", ordens_programadas)

st.markdown("---")

st.caption("Sistema desenvolvido para o Programa de Atendimento aos Carros Especiais (PACE).")
