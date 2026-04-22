"""Testes para a funcionalidade de preview do CSV."""
import csv
from io import StringIO
from pathlib import Path

import pytest

from dat2csv.utils import preview_csv_preview, format_csv_table


class TestPreviewCsvPreview:
    """Testes da função preview_csv_preview."""

    def test_preview_basico(self, dat_simples):
        """Preview com n=2 deve retornar as duas primeiras linhas em formato CSV."""
        resultado = preview_csv_preview(dat_simples, n=2)
        # O arquivo simples.dat tem 3 linhas: "1,dois,3", "4,cinco,6", "7,oito,9"
        linhas = resultado.strip().splitlines()
        assert len(linhas) == 2
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        assert rows == [["1", "dois", "3"], ["4", "cinco", "6"]]

    def test_preview_com_aspas_simples(self, dat_aspas_simples):
        """Campos com vírgula interna devem ser preservados como um único campo."""
        resultado = preview_csv_preview(dat_aspas_simples, n=1)
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        # O arquivo aspas_simples.dat tem: 1,'valor com, virgula',3
        assert rows == [["1", "valor com, virgula", "3"]]

    def test_preview_com_clean(self, dat_colunas_vazias):
        """Colunas 100% vazias devem ser removidas quando clean=True."""
        resultado = preview_csv_preview(dat_colunas_vazias, clean=True, n=3)
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        # O arquivo colunas_vazias.dat tem 4 colunas, a terceira vazia.
        # Após clean, restam 3 colunas.
        assert len(rows) == 3  # 3 linhas
        for row in rows:
            assert len(row) == 3  # coluna vazia removida
        # Conteúdo esperado: coluna 2 (índice 1) vazia removida
        # Linha 1: ["1","A","X"]
        assert rows[0] == ["1", "A", "X"]
        assert rows[1] == ["2", "B", "Y"]
        assert rows[2] == ["3", "C", "Z"]

    def test_preview_com_sps_header(self, dat_simples, sps_simples):
        """Se sps_path fornecido e add_header=True, deve incluir linha de cabeçalho."""
        resultado = preview_csv_preview(
            dat_simples, sps_path=sps_simples, add_header=True, n=2
        )
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        # O .sps simples define labels: V1 "id", V2 "nome", V3 "genero"
        assert rows[0] == ["id", "nome", "genero"]
        assert rows[1] == ["1", "dois", "3"]
        assert rows[2] == ["4", "cinco", "6"]

    def test_preview_com_sps_sem_header(self, dat_simples, sps_simples):
        """Com add_header=False, não deve incluir cabeçalho mesmo com sps."""
        resultado = preview_csv_preview(
            dat_simples, sps_path=sps_simples, add_header=False, n=2
        )
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        assert rows[0] == ["1", "dois", "3"]
        assert rows[1] == ["4", "cinco", "6"]

    def test_preview_com_apply_labels(self, tmp_path):
        """Substitui códigos pelos rótulos de valor quando apply_labels=True."""
        # Criar um .dat com códigos que correspondem aos value labels
        dat = tmp_path / "test.dat"
        dat.write_text("AO01,AO02,3\nAO02,AO03,6")
        # Usar o sps_com_labels que mapeia V2 e V3
        sps = Path("tests/fixtures/com_labels.sps")
        resultado = preview_csv_preview(
            dat,
            sps_path=sps,
            apply_labels=True,
            add_header=True,
            n=2,
        )
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        # Cabeçalho: id, pais, genero (V1, V2, V3)
        assert rows[0] == ["id", "pais", "genero"]
        # Linha 1: V1="AO01" (sem label), V2="AO02" -> "Brasil", V3="3" (sem label)
        assert rows[1] == ["AO01", "Brasil", "3"]
        # Linha 2: V1="AO02" (sem label), V2="AO03" -> "Outro", V3="6" (sem label)
        assert rows[2] == ["AO02", "Outro", "6"]

    def test_preview_n_maior_que_linhas(self, dat_simples):
        """Se n > total de linhas, retorna todas as linhas."""
        resultado = preview_csv_preview(dat_simples, n=10)
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        assert len(rows) == 3  # total de linhas do arquivo

    def test_preview_com_encoding(self, dat_simples):
        """Encoding deve ser respeitado (utf-8-sig padrão)."""
        resultado = preview_csv_preview(dat_simples, encoding="utf-8-sig", n=1)
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        assert rows == [["1", "dois", "3"]]

    def test_preview_output_path_ignorado(self, dat_simples, tmp_path):
        """O parâmetro output_path é ignorado (mantido para compatibilidade)."""
        dummy = tmp_path / "dummy.csv"
        resultado = preview_csv_preview(dat_simples, output_path=dummy, n=1)
        reader = csv.reader(StringIO(resultado))
        rows = list(reader)
        assert rows == [["1", "dois", "3"]]
        assert not dummy.exists()  # nenhum arquivo foi criado


class TestPreviewCli:
    """Testes da flag --preview na interface de linha de comando."""

    def test_preview_flag_sem_n(self, dat_simples, capsys):
        """--preview sem argumento deve mostrar 5 linhas (padrão)."""
        from dat2csv.cli import main
        import sys

        sys.argv = ["dat2csv", str(dat_simples), "--preview", "--raw"]
        main()
        captured = capsys.readouterr()
        # O arquivo tem apenas 3 linhas, então o preview terá 3 linhas
        # Remove linhas vazias no final (causadas por newline extra)
        output_lines = [line for line in captured.out.splitlines() if line]
        assert len(output_lines) == 3
        # Verifica que é CSV válido
        reader = csv.reader(StringIO(captured.out))
        rows = [row for row in reader if row]  # ignora linha vazia
        assert rows == [["1", "dois", "3"], ["4", "cinco", "6"], ["7", "oito", "9"]]

    def test_preview_flag_com_n(self, dat_simples, capsys):
        """--preview 2 deve mostrar apenas as duas primeiras linhas."""
        from dat2csv.cli import main
        import sys

        sys.argv = ["dat2csv", str(dat_simples), "--preview", "2", "--raw"]
        main()
        captured = capsys.readouterr()
        reader = csv.reader(StringIO(captured.out))
        rows = [row for row in reader if row]
        assert rows == [["1", "dois", "3"], ["4", "cinco", "6"]]

    def test_preview_com_sps_e_apply_labels(self, tmp_path, capsys):
        """--preview com --sps e --apply-labels deve substituir códigos."""
        from dat2csv.cli import main
        import sys

        # Criar .dat com códigos
        dat = tmp_path / "test.dat"
        dat.write_text("AO01,AO02,3")
        sps = Path("tests/fixtures/com_labels.sps")
        sys.argv = [
            "dat2csv",
            str(dat),
            "--sps",
            str(sps),
            "--apply-labels",
            "--preview",
            "1",
            "--raw",
        ]
        main()
        captured = capsys.readouterr()
        reader = csv.reader(StringIO(captured.out))
        rows = [row for row in reader if row]
        # Cabeçalho + uma linha de dados
        assert rows == [["id", "pais", "genero"], ["AO01", "Brasil", "3"]]

    def test_preview_com_clean(self, dat_colunas_vazias, capsys):
        """--preview com --clean remove colunas 100% vazias."""
        from dat2csv.cli import main
        import sys

        sys.argv = ["dat2csv", str(dat_colunas_vazias), "--clean", "--preview", "1", "--raw"]
        main()
        captured = capsys.readouterr()
        reader = csv.reader(StringIO(captured.out))
        rows = [row for row in reader if row]
        assert len(rows[0]) == 3  # coluna vazia removida
        assert rows[0] == ["1", "A", "X"]

    def test_preview_com_no_header(self, dat_simples, sps_simples, capsys):
        """--preview com --no-header não deve incluir cabeçalho mesmo com --sps."""
        from dat2csv.cli import main
        import sys

        sys.argv = [
            "dat2csv",
            str(dat_simples),
            "--sps",
            str(sps_simples),
            "--no-header",
            "--preview",
            "1",
            "--raw",
        ]
        main()
        captured = capsys.readouterr()
        reader = csv.reader(StringIO(captured.out))
        rows = [row for row in reader if row]
        assert rows == [["1", "dois", "3"]]

    def test_preview_incompativel_com_inspect(self, dat_simples, capsys):
        """--preview e --inspect não podem ser usados juntos."""
        from dat2csv.cli import main
        import sys
        import pytest

        sys.argv = ["dat2csv", str(dat_simples), "--preview", "--inspect"]
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "Erro: --preview não pode ser usado junto com --inspect." in captured.err

    def test_preview_nao_cria_arquivo(self, dat_simples, tmp_path):
        """A flag --preview não deve criar arquivo de saída."""
        from dat2csv.cli import main
        import sys

        output = tmp_path / "saida.csv"
        sys.argv = ["dat2csv", str(dat_simples), "--preview", "1", str(output)]
        main()
        assert not output.exists()


class TestFormatCsvTable:
    """Testes da função format_csv_table."""

    def test_format_csv_table_basic(self):
        """Verifica alinhamento e truncagem."""
        csv = "id,nome,valor\n1,João Silva,100\n2,Maria,200"
        formatted = format_csv_table(csv, max_width=120, max_col_width=30)
        # Deve conter bordas e separadores
        assert "+" in formatted
        assert "|" in formatted
        # Deve conter os dados
        assert "id" in formatted
        assert "João Silva" in formatted
        # Verificar estrutura básica: separadores horizontais
        lines = formatted.splitlines()
        assert len(lines) == 6  # top border, header, separator, row1, row2, bottom border
        # Cada linha de borda começa e termina com +
        assert lines[0].startswith("+") and lines[0].endswith("+")
        assert lines[2].startswith("+") and lines[2].endswith("+")
        assert lines[5].startswith("+") and lines[5].endswith("+")
        # Células alinhadas
        header_line = lines[1]
        # Deve ter 3 colunas separadas por " | "
        assert " | " in header_line
        # Verificar que os valores estão presentes
        assert "id" in header_line
        assert "nome" in header_line
        assert "valor" in header_line

    def test_format_csv_table_truncate_long_cells(self):
        """Células longas devem ser truncadas com '...'."""
        csv = "coluna\n" + ("x" * 40)  # 40 caracteres, max_col_width padrão 30
        formatted = format_csv_table(csv, max_width=120, max_col_width=30)
        # Deve conter "..."
        assert "..." in formatted
        # O comprimento da célula truncada deve ser <= 30 + 3 (os pontos)
        lines = formatted.splitlines()
        data_line = lines[1]  # linha de dados
        # Extrair conteúdo entre pipes
        between_pipes = data_line.split("|")[1].strip()
        assert len(between_pipes) <= 33  # 30 + 3 pontos

    def test_format_csv_table_adjust_total_width(self):
        """Ajusta largura total para não exceder max_width."""
        csv = "a,b,c\n1,2,3"
        # Forçar largura máxima pequena
        formatted = format_csv_table(csv, max_width=20, max_col_width=10)
        # Calcular largura total da tabela (contando bordas e espaços)
        lines = formatted.splitlines()
        top_border = lines[0]
        assert len(top_border) <= 20

    def test_format_csv_table_empty(self):
        """CSV vazio retorna string vazia."""
        assert format_csv_table("") == ""
        assert format_csv_table("\n") == ""

    def test_format_csv_table_single_row(self):
        """Uma única linha (sem cabeçalho) ainda gera bordas."""
        csv = "1,2,3"
        formatted = format_csv_table(csv)
        lines = formatted.splitlines()
        # Deve ter borda superior, linha de dados, borda inferior
        assert len(lines) == 3
        assert lines[0].startswith("+")
        assert lines[2].startswith("+")


class TestFormatCsvTableMuitasColunas:
    """Testes de format_csv_table com datasets de muitas colunas (modo transposto)."""

    def _csv_largo(self, n_cols: int = 50, n_data_rows: int = 2) -> str:
        headers = [f"col{i}" for i in range(1, n_cols + 1)]
        rows = [[str(i * n_cols + j) for j in range(1, n_cols + 1)] for i in range(n_data_rows)]
        lines = [",".join(headers)] + [",".join(r) for r in rows]
        return "\n".join(lines)

    def test_auto_transposto_acima_de_20_colunas(self):
        """CSV com >20 colunas deve ativar modo transposto automaticamente."""
        formatted = format_csv_table(self._csv_largo(50))
        # Modo transposto: sem linha de borda +---+ no início
        assert not formatted.splitlines()[0].startswith("+")
        assert "Linha 1" in formatted

    def test_formato_vertical_col_valor(self):
        """Modo transposto exibe colunas no formato '  col_name : value'."""
        formatted = format_csv_table(self._csv_largo(50, n_data_rows=1))
        # col1 deve aparecer como label
        assert "col1" in formatted
        # deve haver " : " separando label e valor
        assert " : " in formatted

    def test_respeita_max_cols_display(self):
        """max_cols_display controla quantas colunas aparecem no modo transposto."""
        formatted = format_csv_table(self._csv_largo(50), max_cols_display=4)
        assert "col1" in formatted
        assert "col4" in formatted
        # col5 não deve aparecer como label (pode aparecer como valor numérico)
        lines = formatted.splitlines()
        label_lines = [ln for ln in lines if " : " in ln]
        labels = [ln.split(" : ")[0].strip() for ln in label_lines]
        assert "col5" not in labels

    def test_indica_colunas_omitidas(self):
        """Deve indicar quantas colunas foram omitidas."""
        # 50 colunas, max_cols_display=10 → 40 omitidas
        formatted = format_csv_table(self._csv_largo(50), max_cols_display=10)
        assert "omitidas" in formatted
        assert "40" in formatted

    def test_duas_linhas_de_dados_separadas(self):
        """Cada linha de dados deve ter sua própria seção 'Linha N'."""
        formatted = format_csv_table(self._csv_largo(50, n_data_rows=2))
        assert "Linha 1" in formatted
        assert "Linha 2" in formatted

    def test_sem_omissao_quando_cols_suficientes(self):
        """Se max_cols_display >= num_cols, não deve indicar omissão."""
        formatted = format_csv_table(self._csv_largo(50), max_cols_display=50)
        assert "omitidas" not in formatted

    def test_force_transpose_com_poucas_colunas(self):
        """force_transpose=True ativa modo vertical mesmo com poucas colunas."""
        csv_str = "id,nome\n1,João"
        formatted = format_csv_table(csv_str, force_transpose=True, has_header=True)
        assert "Linha 1" in formatted
        assert "id" in formatted
        assert "nome" in formatted
        assert not formatted.splitlines()[0].startswith("+")

    def test_sem_header_usa_col_n(self):
        """has_header=False: usa 'col_N' como nomes de coluna no modo transposto."""
        csv_str = ",".join(str(i) for i in range(1, 25))  # 24 valores, sem header
        formatted = format_csv_table(csv_str, has_header=False)
        assert "col_1" in formatted
        assert "col_2" in formatted


def test_cols_flag_cli(tmp_path, capsys):
    """--cols N controla o número de colunas exibidas no preview."""
    from dat2csv.cli import main
    import sys

    # Cria .dat com 30 colunas e 1 linha de dados (sem sps → sem header)
    n_cols = 30
    dat = tmp_path / "wide.dat"
    dat.write_text(",".join(str(i) for i in range(1, n_cols + 1)))

    sys.argv = ["dat2csv", str(dat), "--preview", "1", "--cols", "5"]
    main()
    captured = capsys.readouterr()

    # Deve estar em modo transposto (>20 colunas) e mostrar apenas 5
    assert "Linha 1" in captured.out
    lines = captured.out.splitlines()
    label_lines = [ln for ln in lines if " : " in ln]
    assert len(label_lines) == 5

    # Deve indicar colunas omitidas (30 - 5 = 25)
    assert "omitidas" in captured.out
    assert "25" in captured.out


def test_preview_raw_flag(dat_simples, capsys):
    """--preview --raw imprime CSV sem formatação."""
    from dat2csv.cli import main
    import sys

    sys.argv = ["dat2csv", str(dat_simples), "--preview", "1", "--raw"]
    main()
    captured = capsys.readouterr()
    # Saída deve ser CSV bruto, sem bordas
    assert "+" not in captured.out
    assert "|" not in captured.out
    # Deve conter os dados CSV
    reader = csv.reader(StringIO(captured.out))
    rows = [row for row in reader if row]
    assert rows == [["1", "dois", "3"]]

    # Agora sem --raw deve ter formatação
    sys.argv = ["dat2csv", str(dat_simples), "--preview", "1"]
    main()
    captured2 = capsys.readouterr()
    # Deve conter bordas
    assert "+" in captured2.out
    assert "|" in captured2.out