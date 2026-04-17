import argparse
import sys
from pathlib import Path

from .converter import convert
from .utils import calcular_hash, inspecionar_arquivo, imprimir_inspecao


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dat2csv",
        description="Converte arquivos .dat (aspas simples, vírgula) para CSV.",
    )
    parser.add_argument("input", type=Path, help="Arquivo .dat de entrada")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Arquivo .csv de saída (padrão: mesmo nome, extensão .csv)",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Encoding do arquivo de entrada (padrão: utf-8-sig)",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Apenas analisa o arquivo .dat, sem gerar CSV de saída.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help=(
            "Remove colunas 100%% vazias do CSV gerado. "
            "Com --inspect, simula quantas colunas seriam removidas."
        ),
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Não criar backup do arquivo de saída caso já exista.",
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Exibe o hash SHA256 do arquivo de entrada ao final da conversão.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Erro: arquivo '{args.input}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    if args.inspect:
        info = inspecionar_arquivo(
            args.input,
            encoding=args.encoding,
            aplicar_clean=args.clean,
        )
        imprimir_inspecao(info)
        return

    output = args.output or args.input.with_suffix(".csv")
    result = convert(
        args.input,
        output,
        encoding=args.encoding,
        clean=args.clean,
        backup=not args.no_backup,
    )
    if result["backup"]:
        print(f"\U0001f4e6 Backup criado: {result['backup'].name} (arquivo anterior preservado)")
    if args.hash:
        digest = calcular_hash(args.input)
        print(f"\U0001f512 Hash SHA256 do original: {digest}")
    print(f"Arquivo convertido com sucesso!")
    print(f"  Entrada:  {args.input}")
    print(f"  Saída:    {output}")
    print(f"  Linhas:   {result['rows']}")
    print(f"  Colunas:  {result['columns']}")
    if args.clean and result.get("removed_cols"):
        print(f"  Colunas removidas (--clean): {result['removed_cols']}")


if __name__ == "__main__":
    main()
