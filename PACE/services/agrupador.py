"""
Agrupa passageiros por bairro para distribuição nas ordens de serviço.
"""


def agrupar_por_bairro(passageiros):
    """
    Recebe lista de dicts com chave 'bairro' e retorna dict {bairro: [passageiros]}.
    Passageiros sem bairro são agrupados em 'Sem bairro'.
    """
    grupos = {}

    for passageiro in passageiros:
        bairro = (passageiro.get("bairro") or "").strip()
        if not bairro:
            bairro = "Sem bairro"

        if bairro not in grupos:
            grupos[bairro] = []

        grupos[bairro].append(passageiro)

    return grupos


def flatten_grupos(grupos):
    """
    Converte grupos de bairros em lista ordenada por bairro,
    mantendo passageiros do mesmo bairro juntos.
    """
    resultado = []

    for bairro in sorted(grupos.keys()):
        resultado.extend(grupos[bairro])

    return resultado
