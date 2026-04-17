import hashlib
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .converter import _parse_dat


def calcular_hash(arquivo: str | Path, algoritmo: str = "sha256") -> str:
    """
    Calcula o hash do arquivo usando o algoritmo especificado.

    Args:
        arquivo:   Caminho para o arquivo.
        algoritmo: Algoritmo de hash (padrão: sha256).

    Returns:
        String hexadecimal do hash calculado.
    """
    h = hashlib.new(algoritmo)
    with Path(arquivo).open("rb") as f:
        for bloco in iter(lambda: f.read(65_536), b""):
            h.update(bloco)
    return h.hexdigest()


def criar_backup(arquivo: str | Path) -> Path | None:
    """
    Renomeia o arquivo para um nome com timestamp, preservando-o como backup.

    O novo nome segue o padrão: ``<stem>_backup_YYYYMMDD_HHMMSS<suffix>``.

    Args:
        arquivo: Caminho para o arquivo a ser preservado.

    Returns:
        Path do backup criado, ou None se o arquivo não existir ou o backup
        falhar (neste último caso um aviso é impresso em stderr).
    """
    arquivo = Path(arquivo)
    if not arquivo.exists():
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = arquivo.with_name(f"{arquivo.stem}_backup_{ts}{arquivo.suffix}")
    try:
        shutil.move(str(arquivo), destino)
        return destino
    except OSError as exc:
        print(f"Aviso: não foi possível criar backup de '{arquivo}': {exc}", file=sys.stderr)
        return None


def inspecionar_arquivo(
    caminho: str | Path,
    encoding: str = "utf-8-sig",
    aplicar_clean: bool = False,
) -> dict:
    """
    Analisa um arquivo .dat sem gerar CSV de saída.

    Args:
        caminho:       Caminho para o arquivo .dat.
        encoding:      Encoding do arquivo (padrão: utf-8-sig).
        aplicar_clean: Se True, calcula quantas colunas seriam removidas
                       por serem 100% vazias.

    Retorna um dict com:
      - path        : Path do arquivo
      - size_bytes  : tamanho em bytes
      - encoding    : encoding usado
      - rows        : número de linhas não-vazias
      - max_cols    : número máximo de colunas detectado
      - short_rows  : linhas com menos colunas que max_cols
      - empty_cols  : lista de índices de colunas 100% vazias (se aplicar_clean)
      - sample      : lista com até 5 primeiras linhas (campos brutos)
    """
    caminho = Path(caminho)

    rows, max_cols = _parse_dat(caminho, encoding)

    short_rows = sum(1 for r in rows if len(r) < max_cols)

    empty_cols: list[int] = []
    if aplicar_clean and rows:
        empty_cols = [
            col_idx
            for col_idx in range(max_cols)
            if all((col_idx >= len(r) or r[col_idx] == "") for r in rows)
        ]

    return {
        "path": caminho,
        "size_bytes": caminho.stat().st_size,
        "encoding": encoding,
        "rows": len(rows),
        "max_cols": max_cols,
        "short_rows": short_rows,
        "empty_cols": empty_cols,
        "sample": rows[:5],
    }


# ── Helpers de formatação ──────────────────────────────────────────────────────

def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    return f"{size_bytes / 1_024:.1f} KB"


def _truncate(value: str, max_len: int = 50) -> str:
    return value if len(value) <= max_len else value[:max_len] + "…"


def imprimir_inspecao(info: dict) -> None:
    """Imprime o relatório de inspeção no terminal."""
    linhas_fmt = f"{info['rows']:,}".replace(",", ".")

    print(f"\U0001f4c4 Arquivo:  {info['path'].name}")
    print(f"\U0001f4cf Tamanho:  {_format_size(info['size_bytes'])}")
    print(f"\U0001f524 Encoding: {info['encoding']}")
    print(f"\U0001f4ca Linhas:   {linhas_fmt}")
    print(f"\U0001f4d0 Colunas máximas: {info['max_cols']}")

    if info["short_rows"]:
        n = info["short_rows"]
        verbo = "possui" if n == 1 else "possuem"
        print(
            f"\n\u26a0\ufe0f  Atenção: {n} linha{'' if n == 1 else 's'} {verbo} "
            f"menos colunas que o máximo.\n"
            f"   Serão preenchidas com vazio na conversão."
        )

    if info["empty_cols"] is not None:
        n = len(info["empty_cols"])
        if n:
            print(f"\n\U0001f527 Com --clean: {n} colunas seriam removidas (100% vazias).")
        else:
            print("\n\U0001f527 Com --clean: nenhuma coluna 100% vazia encontrada.")

    print("\n\U0001f4cb Amostra (5 primeiras linhas):")
    for i, row in enumerate(info["sample"], start=1):
        truncated = [_truncate(f) for f in row]
        preview = truncated[:6]
        suffix = ",…" if len(row) > 6 else ""
        print(f"  [{i}] {','.join(preview)}{suffix}")
