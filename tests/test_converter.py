"""Testes para dat2csv.converter."""
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from dat2csv.converter import _parse_dat, convert


# ── _parse_dat ─────────────────────────────────────────────────────────────────

class TestParseDat:
    def test_linha_simples(self, dat_simples):
        """Campos sem aspas: cada token vira um campo."""
        rows, max_cols = _parse_dat(dat_simples)

        assert len(rows) == 3
        assert rows[0] == ["1", "dois", "3"]
        assert max_cols == 3

    def test_campo_com_virgula_interna(self, dat_aspas_simples):
        """Aspas simples protegem a vírgula interna — campo não deve ser dividido."""
        rows, _ = _parse_dat(dat_aspas_simples)

        assert rows[0][1] == "valor com, virgula"
        assert len(rows[0]) == 3  # 1 + campo com vírgula + 3

    def test_linhas_vazias_ignoradas(self, tmp_path):
        """Linhas em branco não devem gerar entradas em rows."""
        dat = tmp_path / "blank.dat"
        dat.write_text("1,A\n\n\n2,B\n", encoding="utf-8")

        rows, _ = _parse_dat(dat)

        assert len(rows) == 2

    def test_colunas_vazias_direita_removidas(self, tmp_path):
        """Colunas vazias no final de cada linha devem ser descartadas."""
        dat = tmp_path / "trailing.dat"
        dat.write_text("1,A,,,\n2,B,,,\n", encoding="utf-8")

        rows, max_cols = _parse_dat(dat)

        assert rows[0] == ["1", "A"]
        assert max_cols == 2

    def test_arquivo_vazio(self, tmp_path):
        """Arquivo vazio retorna lista vazia e 0 colunas."""
        dat = tmp_path / "vazio.dat"
        dat.write_text("", encoding="utf-8")

        rows, max_cols = _parse_dat(dat)

        assert rows == []
        assert max_cols == 0

    def test_encoding_utf8_sig(self, tmp_path):
        """BOM utf-8-sig não deve aparecer no primeiro campo."""
        dat = tmp_path / "bom.dat"
        dat.write_bytes(b"\xef\xbb\xbf1,A\n2,B\n")  # BOM + conteúdo

        rows, _ = _parse_dat(dat, encoding="utf-8-sig")

        assert rows[0][0] == "1"

    def test_stopiteration_em_csv_reader_e_ignorada(self, tmp_path):
        """Se csv.reader levantar StopIteration inesperadamente, a linha é ignorada.

        Este caminho é defensivo e não ocorre com inputs normais; usamos mock
        para garantir cobertura do except StopIteration (L27-28).
        """
        dat = tmp_path / "qualquer.dat"
        dat.write_text("1,A\n2,B\n", encoding="utf-8")

        # Faz csv.reader retornar um iterador vazio para cada chamada
        iterador_vazio = MagicMock()
        iterador_vazio.__iter__ = lambda s: iter([])
        iterador_vazio.__next__ = MagicMock(side_effect=StopIteration)

        with patch("dat2csv.converter.csv.reader", return_value=iterador_vazio):
            rows, max_cols = _parse_dat(dat)

        # Com o reader sempre lançando StopIteration, nenhuma linha é processada
        assert rows == []
        assert max_cols == 0


# ── normalização de linhas irregulares ────────────────────────────────────────

class TestNormalizarRegistros:
    def test_max_cols_detectado_corretamente(self, dat_linhas_irregulares):
        """max_cols deve refletir a linha mais larga."""
        rows, max_cols = _parse_dat(dat_linhas_irregulares)

        # simples.dat tem linhas de 4, 3 e 2 campos → max = 4
        assert max_cols == 4

    def test_linhas_curtas_preservadas(self, dat_linhas_irregulares):
        """Linhas com menos campos são mantidas como estão (sem padding em _parse_dat)."""
        rows, _ = _parse_dat(dat_linhas_irregulares)

        assert len(rows[1]) == 3  # "2,B,Y"
        assert len(rows[2]) == 2  # "3,C"

    def test_csv_gerado_tem_largura_uniforme(self, dat_linhas_irregulares, tmp_path):
        """convert() deve paddar cada linha até max_cols no CSV final."""
        out = tmp_path / "out.csv"
        result = convert(dat_linhas_irregulares, out, backup=False)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert all(len(linha) == result["columns"] for linha in linhas)


# ── remoção de colunas vazias (--clean) ───────────────────────────────────────

class TestRemoverColunasVazias:
    def test_coluna_vazia_removida(self, dat_colunas_vazias, tmp_path):
        """Coluna do meio (índice 2) está 100% vazia e deve ser removida com clean=True."""
        out = tmp_path / "out.csv"
        result = convert(dat_colunas_vazias, out, clean=True, backup=False)

        assert result["removed_cols"] == 1

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        # Colunas restantes: 0 (número), 1 (letra), 3 (X/Y/Z)
        assert linhas[0] == ["1", "A", "X"]
        assert linhas[1] == ["2", "B", "Y"]

    def test_sem_colunas_vazias_nao_remove_nada(self, dat_simples, tmp_path):
        """Se não há colunas vazias, removed_cols deve ser 0."""
        out = tmp_path / "out.csv"
        result = convert(dat_simples, out, clean=True, backup=False)

        assert result["removed_cols"] == 0
        assert result["columns"] == 3

    def test_clean_false_preserva_colunas_vazias(self, dat_colunas_vazias, tmp_path):
        """Sem clean=True, colunas vazias devem permanecer no CSV."""
        out = tmp_path / "out.csv"
        result = convert(dat_colunas_vazias, out, clean=False, backup=False)

        assert result["columns"] == 4  # inclui a coluna vazia

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert linhas[0][2] == ""  # coluna vazia ainda presente


# ── conversão completa ─────────────────────────────────────────────────────────

class TestConversaoCompleta:
    def test_resultado_estrutural(self, dat_simples, tmp_path):
        """Conversão básica: result dict deve ter todas as chaves esperadas."""
        out = tmp_path / "out.csv"
        result = convert(dat_simples, out, backup=False)

        assert result["rows"] == 3
        assert result["columns"] == 3
        assert result["backup"] is None

    def test_arquivo_csv_criado(self, dat_simples, tmp_path):
        """O arquivo de saída deve ser criado e ser válido."""
        out = tmp_path / "out.csv"
        convert(dat_simples, out, backup=False)

        assert out.exists()
        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))
        assert len(linhas) == 3

    def test_conteudo_preservado(self, dat_aspas_simples, tmp_path):
        """Campos com vírgula interna devem ser escritos corretamente no CSV."""
        out = tmp_path / "out.csv"
        convert(dat_aspas_simples, out, backup=False)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert linhas[0][1] == "valor com, virgula"

    def test_diretorio_saida_criado_automaticamente(self, dat_simples, tmp_path):
        """convert() deve criar subdiretórios de saída que não existam."""
        out = tmp_path / "sub" / "dir" / "out.csv"
        convert(dat_simples, out, backup=False)

        assert out.exists()

    def test_backup_criado_quando_saida_existe(self, dat_simples, tmp_path):
        """Na segunda conversão (backup=True), o CSV anterior vira arquivo de backup."""
        out = tmp_path / "out.csv"
        convert(dat_simples, out, backup=False)   # cria o CSV
        result = convert(dat_simples, out, backup=True)  # deve gerar backup

        assert result["backup"] is not None
        assert result["backup"].exists()
        assert "_backup_" in result["backup"].name

    def test_no_backup_quando_desabilitado(self, dat_simples, tmp_path):
        """backup=False não deve criar arquivo de backup mesmo que saída exista."""
        out = tmp_path / "out.csv"
        convert(dat_simples, out, backup=False)
        result = convert(dat_simples, out, backup=False)

        assert result["backup"] is None
        # Nenhum arquivo _backup_ no diretório
        backups = list(tmp_path.glob("*_backup_*"))
        assert backups == []
