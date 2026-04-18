import csv
from pathlib import Path


def _parse_dat(
    input_path: Path, encoding: str = "utf-8-sig"
) -> tuple[list[list[str]], int]:
    """
    Lê e parseia um arquivo .dat.

    Retorna (rows, max_cols) onde rows é a lista de campos por linha
    (já sem colunas vazias à direita) e max_cols é o maior número de
    colunas encontrado.
    """
    rows: list[list[str]] = []
    max_cols = 0

    with input_path.open(encoding=encoding) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            reader = csv.reader([raw_line], quotechar="'", skipinitialspace=True)
            try:
                fields = next(reader)
            except StopIteration:
                continue

            while fields and fields[-1] == "":
                fields.pop()

            if fields:
                rows.append(fields)
                if len(fields) > max_cols:
                    max_cols = len(fields)

    return rows, max_cols


def _apply_value_labels(
    rows: list[list[str]],
    max_cols: int,
    value_labels: dict[str, dict[str, str]],
) -> list[list[str]]:
    """Substitui códigos pelos rótulos de valor nas colunas que possuem mapeamento."""
    resultado = []
    for row in rows:
        nova = list(row)
        for col_idx in range(len(nova)):
            var = f"V{col_idx + 1}"
            mapa = value_labels.get(var)
            if mapa and nova[col_idx] in mapa:
                nova[col_idx] = mapa[nova[col_idx]]
        resultado.append(nova)
    return resultado


def convert(
    input_path: str | Path,
    output_path: str | Path,
    encoding: str = "utf-8-sig",
    clean: bool = False,
    backup: bool = True,
    sps_path: str | Path | None = None,
    apply_labels: bool = False,
    add_header: bool = True,
) -> dict:
    """
    Converte um arquivo .dat para CSV.

    Args:
        input_path:   Caminho para o arquivo .dat de entrada.
        output_path:  Caminho para o arquivo .csv de saída.
        encoding:     Encoding do arquivo de entrada (padrão: utf-8-sig).
        clean:        Se True, remove colunas 100% vazias do CSV final.
        backup:       Se True (padrão), cria backup do arquivo de saída caso já exista.
        sps_path:     Caminho opcional para arquivo .sps com metadados SPSS.
        apply_labels: Se True (requer sps_path), substitui códigos por rótulos de valor.
        add_header:   Se True (padrão) e sps_path fornecido, adiciona linha de cabeçalho.

    Returns:
        dict com chaves 'rows', 'columns', 'backup' (Path ou None) e,
        se clean=True, 'removed_cols'.
    """
    # Importação local para evitar ciclo (utils importa converter)
    from .utils import criar_backup

    input_path = Path(input_path)
    output_path = Path(output_path)

    # ── Metadados do .sps ────────────────────────────────────────────────────
    metadata: dict = {"variable_labels": {}, "value_labels": {}}
    if sps_path is not None:
        from .sps import parse_sps
        metadata = parse_sps(sps_path)

    rows, max_cols = _parse_dat(input_path, encoding)

    # ── Substituição de labels ───────────────────────────────────────────────
    if apply_labels and metadata["value_labels"]:
        rows = _apply_value_labels(rows, max_cols, metadata["value_labels"])

    # ── Limpeza de colunas 100% vazias ───────────────────────────────────────
    keep_cols: list[int] | None = None
    removed = 0
    if clean and rows:
        empty = {
            col_idx
            for col_idx in range(max_cols)
            if all((col_idx >= len(r) or r[col_idx] == "") for r in rows)
        }
        keep_cols = [i for i in range(max_cols) if i not in empty]
        removed = len(empty)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = criar_backup(output_path) if backup else None

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

    # ── Escrita do CSV ───────────────────────────────────────────────────────
    with output_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        if header is not None:
            writer.writerow(header)
        for row in rows:
            padded = row + [""] * (max_cols - len(row))
            out_row = [padded[i] for i in keep_cols] if keep_cols is not None else padded
            writer.writerow(out_row)

    final_cols = len(keep_cols) if keep_cols is not None else max_cols
    result: dict = {"rows": len(rows), "columns": final_cols, "backup": backup_path}
    if clean:
        result["removed_cols"] = removed
    return result
