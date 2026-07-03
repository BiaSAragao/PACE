"""
Lógica de geração automática de ordens de serviço.
"""

from services.agrupador import agrupar_por_bairro, flatten_grupos


def _montar_endereco(rua, numero, complemento):
    """Monta string de origem a partir do endereço do passageiro."""
    partes = []

    if rua:
        partes.append(rua.strip())
    if numero:
        partes.append(f"nº {numero.strip()}")
    if complemento:
        partes.append(complemento.strip())

    return ", ".join(partes) if partes else None


def buscar_passageiros_agendados(cur, dia_semana):
    """
    Busca passageiros ativos com agenda ativa para o dia da semana informado.
    """
    cur.execute(
        """
        SELECT
            p.id_passageiro,
            p.nome,
            p.rua,
            p.numero,
            p.complemento,
            p.bairro,
            a.horario_saida,
            a.horario_retorno,
            a.destino
        FROM agenda_passageiros a
        INNER JOIN passageiros p
            ON p.id_passageiro = a.id_passageiro
        WHERE a.dia_semana = %s
          AND a.ativo = TRUE
          AND p.ativo = TRUE
        ORDER BY p.bairro, p.nome
        """,
        (dia_semana,),
    )

    passageiros = []

    for row in cur.fetchall():
        (
            id_passageiro,
            nome,
            rua,
            numero,
            complemento,
            bairro,
            horario_saida,
            horario_retorno,
            destino,
        ) = row

        # Horário previsto: saída em dias úteis, retorno pode ser usado conforme destino
        horario_previsto = horario_saida or horario_retorno

        passageiros.append(
            {
                "id_passageiro": id_passageiro,
                "nome": nome,
                "rua": rua,
                "numero": numero,
                "complemento": complemento,
                "bairro": bairro,
                "origem": _montar_endereco(rua, numero, complemento),
                "destino": destino,
                "horario_previsto": horario_previsto,
            }
        )

    return passageiros


def buscar_veiculos_disponiveis(cur):
    """Retorna veículos ativos ordenados por número do carro."""
    cur.execute(
        """
        SELECT id_veiculo, numero_carro, capacidade
        FROM veiculos
        WHERE status = TRUE
        ORDER BY numero_carro
        """
    )

    return [
        {"id_veiculo": row[0], "numero_carro": row[1], "capacidade": row[2]}
        for row in cur.fetchall()
    ]


def _criar_alocacao(veiculos):
    """Inicializa estrutura de alocação por veículo."""
    return {
        veiculo["id_veiculo"]: {
            "veiculo": veiculo,
            "passageiros": [],
        }
        for veiculo in veiculos
    }


def _veiculo_com_menos_passageiros(alocacao, id_veiculos):
    """Encontra veículo com menor ocupação entre os candidatos."""
    return min(
        id_veiculos,
        key=lambda vid: (
            len(alocacao[vid]["passageiros"]),
            alocacao[vid]["veiculo"]["numero_carro"],
        ),
    )


def _veiculo_com_capacidade(alocacao, bairro=None):
    """
    Retorna id de veículo com vaga disponível.
    Prioriza veículo que já transporta passageiros do mesmo bairro.
    """
    candidatos_mesmo_bairro = []
    candidatos_gerais = []

    for vid, dados in alocacao.items():
        capacidade = dados["veiculo"]["capacidade"]
        ocupacao = len(dados["passageiros"])

        if ocupacao >= capacidade:
            continue

        candidatos_gerais.append(vid)

        if bairro and any(p["bairro"] == bairro for p in dados["passageiros"]):
            candidatos_mesmo_bairro.append(vid)

    if candidatos_mesmo_bairro:
        return _veiculo_com_menos_passageiros(alocacao, candidatos_mesmo_bairro)

    if candidatos_gerais:
        return _veiculo_com_menos_passageiros(alocacao, candidatos_gerais)

    return None


def distribuir_passageiros(passageiros, veiculos, tipo_dia):
    """
    Distribui passageiros nos veículos respeitando capacidade.
    Em SABADO, DOMINGO e FERIADO, aloca primeiro um passageiro por veículo.
    """
    if not veiculos:
        return {}

    if not passageiros:
        return {}

    alocacao = _criar_alocacao(veiculos)
    restantes = flatten_grupos(agrupar_por_bairro(passageiros))

    # Fins de semana e feriados: um passageiro por veículo antes da distribuição normal
    if tipo_dia in ("SABADO", "DOMINGO", "FERIADO"):
        for veiculo in veiculos:
            if not restantes:
                break

            vid = veiculo["id_veiculo"]
            if len(alocacao[vid]["passageiros"]) >= veiculo["capacidade"]:
                continue

            alocacao[vid]["passageiros"].append(restantes.pop(0))

    # Distribuição normal: prioriza manter passageiros do mesmo bairro no mesmo veículo
    while restantes:
        passageiro = restantes.pop(0)
        bairro = passageiro.get("bairro")

        vid = _veiculo_com_capacidade(alocacao, bairro)

        if vid is None:
            raise ValueError(
                "Capacidade insuficiente nos veículos para atender todos os passageiros."
            )

        alocacao[vid]["passageiros"].append(passageiro)

    # Remove veículos sem passageiros alocados
    return {
        vid: dados
        for vid, dados in alocacao.items()
        if dados["passageiros"]
    }


def _ordenar_passageiros_rota(passageiros):
    """Define sequência da rota por bairro e horário previsto."""
    return sorted(
        passageiros,
        key=lambda p: (
            (p.get("bairro") or "").lower(),
            str(p.get("horario_previsto") or ""),
            p.get("nome", "").lower(),
        ),
    )


def gerar_ordens_servico(conn, data_servico, tipo_dia):
    """
    Gera ordens de serviço para a data informada.
    Retorna lista de ids das ordens criadas.
    """
    cur = conn.cursor()

    try:
        dia_semana = data_servico.weekday()

        # Verifica se já existem ordens para a mesma data
        cur.execute(
            """
            SELECT COUNT(*)
            FROM ordens_servico
            WHERE data_servico = %s
              AND status != 'CANCELADA'
            """,
            (data_servico,),
        )

        if cur.fetchone()[0] > 0:
            raise ValueError(
                "Já existem ordens de serviço ativas para esta data."
            )

        passageiros = buscar_passageiros_agendados(cur, dia_semana)

        if not passageiros:
            raise ValueError(
                "Nenhum passageiro agendado para este dia da semana."
            )

        veiculos = buscar_veiculos_disponiveis(cur)

        if not veiculos:
            raise ValueError("Nenhum veículo disponível.")

        alocacao = distribuir_passageiros(passageiros, veiculos, tipo_dia)

        if not alocacao:
            raise ValueError("Não foi possível alocar passageiros nos veículos.")

        ids_ordens = []

        for vid, dados in alocacao.items():
            cur.execute(
                """
                INSERT INTO ordens_servico
                    (data_servico, tipo_dia, id_veiculo, status)
                VALUES (%s, %s, %s, 'PROGRAMADA')
                RETURNING id_ordem
                """,
                (data_servico, tipo_dia, vid),
            )

            id_ordem = cur.fetchone()[0]
            ids_ordens.append(id_ordem)

            passageiros_rota = _ordenar_passageiros_rota(dados["passageiros"])

            for sequencia, passageiro in enumerate(passageiros_rota, start=1):
                cur.execute(
                    """
                    INSERT INTO ordem_servico_passageiros
                    (
                        id_ordem,
                        id_passageiro,
                        origem,
                        destino,
                        bairro,
                        horario_previsto,
                        sequencia_rota
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_ordem,
                        passageiro["id_passageiro"],
                        passageiro["origem"],
                        passageiro["destino"],
                        passageiro["bairro"],
                        passageiro["horario_previsto"],
                        sequencia,
                    ),
                )

        conn.commit()
        return ids_ordens

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
