"""
Parser de arquivos de sintaxe SPSS (.sps) gerados pelo LimeSurvey.

Extrai VARIABLE LABELS e VALUE LABELS para enriquecer a conversão CSV.

Suporta labels de linha única e labels com concatenação de strings SPSS:

    VARIABLE LABELS V55 "parte inicial da label"+
    "continuação da label".
"""
import re
import sys
from pathlib import Path


# Linha única: VARIABLE LABELS V1 "label".
# Usa .+ (greedy) para lidar com aspas internas no texto da label.
_RE_VAR_LABEL = re.compile(
    r'^VARIABLE\s+LABELS\s+(\w+)\s+"(.+)"\.?\s*$',
    re.IGNORECASE,
)

# Início de label concatenada: VARIABLE LABELS V55 "primeira parte"+
_RE_VAR_LABEL_CONCAT_START = re.compile(
    r'^VARIABLE\s+LABELS\s+(\w+)\s+"(.+)"\+\s*$',
    re.IGNORECASE,
)

# Segmento de continuação: "texto"+ (mais segmentos) ou "texto". (último)
_RE_VAR_LABEL_CONCAT_CONT = re.compile(
    r'^\s*"(.+)"([+.])\s*$',
)

# Cabeçalho de bloco VALUE LABELS: VALUE LABELS  V6
_RE_VALUE_BLOCK_START = re.compile(
    r'^VALUE\s+LABELS\s+(\w+)\s*$',
    re.IGNORECASE,
)

# Entrada de valor:  "AO01" "Portuguesa". (o ponto pode ou não estar)
_RE_VALUE_ENTRY = re.compile(
    r'^\s+"(.+?)"\s+"(.+?)"\.?\s*$',
)


def parse_sps(caminho: str | Path, encoding: str = "utf-8-sig") -> dict:
    """
    Extrai VARIABLE LABELS e VALUE LABELS de um arquivo de sintaxe SPSS.

    Suporta labels de linha única e labels com concatenação de strings (`"+`).

    Args:
        caminho:  Caminho para o arquivo .sps.
        encoding: Encoding do arquivo (padrão: utf-8-sig).

    Returns:
        Dict com chaves:
          - 'variable_labels': {nome_var: label_str}
          - 'value_labels':    {nome_var: {codigo: label_str}}

        Em caso de erro de leitura, retorna dicionários vazios e imprime
        aviso em stderr (fail-soft).
    """
    caminho = Path(caminho)

    variable_labels: dict[str, str] = {}
    value_labels: dict[str, dict[str, str]] = {}

    try:
        linhas = caminho.read_text(encoding=encoding).splitlines()
    except OSError as exc:
        print(f"Aviso: não foi possível ler '{caminho}': {exc}", file=sys.stderr)
        return {"variable_labels": variable_labels, "value_labels": value_labels}

    # Estado da state machine
    val_var: str | None = None    # variável do bloco VALUE LABELS em curso
    concat_var: str | None = None  # variável de VARIABLE LABELS em concatenação
    concat_accum: str = ""         # texto acumulado da label concatenada

    for linha in linhas:
        # ── Continuação de label concatenada ─────────────────────────────
        # Verificar primeiro para não tentar re-parsear como outra instrução
        if concat_var is not None:
            m = _RE_VAR_LABEL_CONCAT_CONT.match(linha)
            if m:
                concat_accum += m.group(1)
                if m.group(2) == ".":
                    # Último segmento: salva e encerra acumulação
                    variable_labels[concat_var] = concat_accum
                    concat_var = None
                    concat_accum = ""
                # Senão: mais segmentos virão; continua acumulando
                continue
            else:
                # Linha inesperada durante acumulação → descarta label incompleta
                concat_var = None
                concat_accum = ""
                # Cai para processar a linha normalmente abaixo

        # ── Início de label concatenada ───────────────────────────────────
        m = _RE_VAR_LABEL_CONCAT_START.match(linha)
        if m:
            val_var = None  # sai de qualquer bloco VALUE LABELS aberto
            concat_var = m.group(1)
            concat_accum = m.group(2)
            continue

        # ── VARIABLE LABELS de linha única ────────────────────────────────
        m = _RE_VAR_LABEL.match(linha)
        if m:
            val_var = None
            variable_labels[m.group(1)] = m.group(2)
            continue

        # ── Início de bloco VALUE LABELS ──────────────────────────────────
        m = _RE_VALUE_BLOCK_START.match(linha)
        if m:
            val_var = m.group(1)
            value_labels.setdefault(val_var, {})
            continue

        # ── Entrada de valor dentro de bloco VALUE LABELS ─────────────────
        if val_var is not None:
            m = _RE_VALUE_ENTRY.match(linha)
            if m:
                value_labels[val_var][m.group(1)] = m.group(2)
                if linha.rstrip().endswith("."):
                    val_var = None
            elif linha.strip() and not linha.strip().startswith("*"):
                val_var = None

    return {"variable_labels": variable_labels, "value_labels": value_labels}
