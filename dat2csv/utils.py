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


def preview_csv_preview(
    input_path: str | Path,
    output_path: str | Path | None = None,
    sps_path: str | Path | None = None,
    apply_labels: bool = False,
    clean: bool = False,
    add_header: bool = True,
    encoding: str = "utf-8-sig",
    n: int = 5,
) -> str:
    """
    Processa o .dat como convert() faria e retorna uma string formatada como CSV
    contendo as primeiras n linhas.

    Args:
        input_path:   Caminho para o arquivo .dat de entrada.
        output_path:  Caminho para o arquivo .csv de saída (ignorado, mantido para
                      compatibilidade com a assinatura de convert).
        sps_path:     Caminho opcional para arquivo .sps com metadados SPSS.
        apply_labels: Se True (requer sps_path), substitui códigos por rótulos de valor.
        clean:        Se True, remove colunas 100% vazias do CSV final.
        add_header:   Se True (padrão) e sps_path fornecido, adiciona linha de cabeçalho.
        encoding:     Encoding do arquivo de entrada (padrão: utf-8-sig).
        n:            Número de linhas a incluir no preview (padrão: 5).

    Returns:
        String CSV com as primeiras n linhas (incluindo cabeçalho, se aplicável).
    """
    import csv
    from io import StringIO
    from .sps import parse_sps

    input_path = Path(input_path)

    # ── Metadados do .sps ────────────────────────────────────────────────────
    metadata: dict = {"variable_labels": {}, "value_labels": {}}
    if sps_path is not None:
        metadata = parse_sps(sps_path)

    rows, max_cols = _parse_dat(input_path, encoding)

    # ── Substituição de labels ───────────────────────────────────────────────
    if apply_labels and metadata["value_labels"]:
        from .converter import _apply_value_labels
        rows = _apply_value_labels(rows, max_cols, metadata["value_labels"])

    # ── Limpeza de colunas 100% vazias ───────────────────────────────────────
    keep_cols: list[int] | None = None
    if clean and rows:
        empty = {
            col_idx
            for col_idx in range(max_cols)
            if all((col_idx >= len(r) or r[col_idx] == "") for r in rows)
        }
        keep_cols = [i for i in range(max_cols) if i not in empty]

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    header: list[str] | None = None
    if sps_path is not None and add_header and metadata["variable_labels"]:
        all_headers = [
            metadata["variable_labels"].get(f"V{i + 1}", f"V{i + 1}")
            for i in range(max_cols)
        ]
        header = (
            [all_headers[i] for i in keep_cols]
            if keep_cols is not None
            else all_headers
        )

    # ── Seleção das primeiras n linhas ───────────────────────────────────────
    preview_rows = rows[:n]

    # ── Formatação CSV em memória ────────────────────────────────────────────
    buffer = StringIO()
    writer = csv.writer(buffer)
    if header is not None:
        writer.writerow(header)
    for row in preview_rows:
        padded = row + [""] * (max_cols - len(row))
        out_row = [padded[i] for i in keep_cols] if keep_cols is not None else padded
        writer.writerow(out_row)

    return buffer.getvalue()


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


def format_csv_table(
    csv_string: str,
    max_width: int = 120,
    max_col_width: int = 30,
    max_cols_display: int = 10,
    force_transpose: bool = False,
    has_header: bool = True,
) -> str:
    """
    Formata uma string CSV como tabela alinhada (horizontal) ou lista vertical (transposta).

    Modo transposto é ativado automaticamente quando o CSV tiver mais de 20 colunas,
    ou explicitamente via force_transpose=True. No modo transposto, cada linha de dados
    é exibida verticalmente no formato "  nome_coluna : valor".

    Args:
        csv_string:       String contendo CSV (com cabeçalho opcional).
        max_width:        Largura máxima total da tabela no modo horizontal.
        max_col_width:    Largura máxima de cada célula (conteúdo truncado com "...").
        max_cols_display: Número máximo de colunas a exibir (padrão: 10).
        force_transpose:  Se True, força o modo vertical independente do nº de colunas.
        has_header:       Se True (padrão), trata a primeira linha como cabeçalho no
                          modo transposto. Ignorado no modo horizontal.

    Returns:
        String formatada.
    """
    import csv
    from io import StringIO

    if not csv_string or not csv_string.strip():
        return ""

    reader = csv.reader(StringIO(csv_string))
    rows = [row for row in reader if any(cell != "" for cell in row)]
    if not rows:
        return ""

    num_cols = max(len(row) for row in rows)
    padded = [row + [""] * (num_cols - len(row)) for row in rows]

    use_transpose = force_transpose or num_cols > 20

    # ── Modo transposto (vertical) ────────────────────────────────────────────
    if use_transpose:
        if has_header and len(padded) > 1:
            headers = padded[0]
            data_rows = padded[1:]
        else:
            headers = [f"col_{i + 1}" for i in range(num_cols)]
            data_rows = padded

        display_cols = min(max_cols_display, num_cols)
        omitted = num_cols - display_cols

        # Truncar labels longos para não distorcer o alinhamento
        display_headers = []
        for h in headers[:display_cols]:
            if len(h) > max_col_width:
                display_headers.append(h[: max_col_width - 3] + "...")
            else:
                display_headers.append(h)
        label_width = max((len(h) for h in display_headers), default=0)

        segments = []
        for row_idx, row in enumerate(data_rows):
            sep_line = f"── Linha {row_idx + 1} ".ljust(max_width, "─")
            lines = [sep_line]
            for col_idx in range(display_cols):
                label = display_headers[col_idx].ljust(label_width)
                value = row[col_idx] if col_idx < len(row) else ""
                if len(value) > max_col_width:
                    value = value[: max_col_width - 3] + "..."
                lines.append(f"  {label} : {value}")
            if omitted > 0:
                lines.append(f"  (+ {omitted} colunas omitidas de {num_cols})")
            segments.append("\n".join(lines))

        return "\n\n".join(segments)

    # ── Modo horizontal (tabela) ──────────────────────────────────────────────
    display_cols = min(max_cols_display, num_cols)
    omitted = num_cols - display_cols
    sliced = [row[:display_cols] for row in padded]

    col_widths = []
    for col_idx in range(display_cols):
        max_len = 0
        for row in sliced:
            cell = row[col_idx]
            display_len = min(len(cell), max_col_width)
            if len(cell) > max_col_width:
                display_len += 3
            max_len = max(max_len, display_len)
        col_widths.append(max(1, max_len))

    total_width = sum(col_widths) + (display_cols - 1) * 3 + 4
    if total_width > max_width:
        excess = total_width - max_width
        sorted_indices = sorted(range(display_cols), key=lambda i: col_widths[i], reverse=True)
        for idx in sorted_indices:
            if excess <= 0:
                break
            reduction = min(excess, col_widths[idx] - 1)
            col_widths[idx] -= reduction
            excess -= reduction

    lines = []

    def make_separator() -> str:
        parts = ["+"]
        for w in col_widths:
            parts.append("-" * (w + 2))
            parts.append("+")
        return "".join(parts)

    separador = make_separator()
    lines.append(separador)

    for row_idx, row in enumerate(sliced):
        cells = []
        for col_idx, cell in enumerate(row):
            width = col_widths[col_idx]
            if len(cell) > width:
                if width > 3:
                    truncated = cell[: width - 3] + "..."
                else:
                    truncated = "." * width
                cells.append(truncated.ljust(width))
            else:
                cells.append(cell.ljust(width))
        lines.append("| " + " | ".join(cells) + " |")
        if row_idx == 0 and len(sliced) > 1:
            lines.append(separador)

    lines.append(separador)
    result = "\n".join(lines)

    if omitted > 0:
        result += f"\n(+ {omitted} colunas omitidas de {num_cols})"

    return result
