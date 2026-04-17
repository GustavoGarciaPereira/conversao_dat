"""Testes para dat2csv.utils."""
import hashlib
from pathlib import Path

import pytest

from dat2csv.utils import calcular_hash, criar_backup, inspecionar_arquivo


# ── calcular_hash ──────────────────────────────────────────────────────────────

class TestCalcularHash:
    def test_sha256_valor_correto(self, tmp_path):
        """Hash deve coincidir com hashlib direto."""
        arq = tmp_path / "dado.txt"
        arq.write_bytes(b"conteudo de teste")

        esperado = hashlib.sha256(b"conteudo de teste").hexdigest()
        assert calcular_hash(arq) == esperado

    def test_algoritmo_md5(self, tmp_path):
        """Deve aceitar md5 como algoritmo alternativo."""
        arq = tmp_path / "dado.txt"
        arq.write_bytes(b"abc")

        esperado = hashlib.md5(b"abc").hexdigest()
        assert calcular_hash(arq, algoritmo="md5") == esperado

    def test_arquivo_vazio(self, tmp_path):
        """Hash de arquivo vazio deve ser o hash SHA256 da string vazia."""
        arq = tmp_path / "vazio.txt"
        arq.write_bytes(b"")

        assert calcular_hash(arq) == hashlib.sha256(b"").hexdigest()

    def test_hash_deterministico(self, tmp_path):
        """Duas chamadas com o mesmo arquivo devem retornar o mesmo hash."""
        arq = tmp_path / "dado.txt"
        arq.write_bytes(b"repetivel")

        assert calcular_hash(arq) == calcular_hash(arq)

    def test_arquivos_diferentes_geram_hashes_diferentes(self, tmp_path):
        """Conteúdos distintos devem produzir hashes distintos."""
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"conteudo A")
        b.write_bytes(b"conteudo B")

        assert calcular_hash(a) != calcular_hash(b)


# ── criar_backup ───────────────────────────────────────────────────────────────

class TestCriarBackup:
    def test_retorna_none_se_arquivo_nao_existe(self, tmp_path):
        """Arquivo inexistente → retorna None, sem erros."""
        resultado = criar_backup(tmp_path / "nao_existe.csv")
        assert resultado is None

    def test_backup_criado_com_timestamp(self, tmp_path):
        """Backup deve ter padrão <stem>_backup_YYYYMMDD_HHMMSS<suffix>."""
        arq = tmp_path / "saida.csv"
        arq.write_text("linha1\n")

        backup = criar_backup(arq)

        assert backup is not None
        assert backup.exists()
        assert backup.stem.startswith("saida_backup_")
        assert backup.suffix == ".csv"
        # Verifica formato do timestamp (14 dígitos após "_backup_")
        ts_parte = backup.stem.replace("saida_backup_", "")
        assert len(ts_parte) == 15  # YYYYMMDD_HHMMSS
        assert ts_parte[8] == "_"

    def test_arquivo_original_removido_apos_backup(self, tmp_path):
        """Após o backup, o arquivo original não deve mais existir no caminho original."""
        arq = tmp_path / "saida.csv"
        arq.write_text("dados\n")

        criar_backup(arq)

        assert not arq.exists()

    def test_conteudo_preservado_no_backup(self, tmp_path):
        """O conteúdo do arquivo deve ser idêntico no backup."""
        arq = tmp_path / "saida.csv"
        arq.write_text("linha1,linha2\n")

        backup = criar_backup(arq)

        assert backup.read_text() == "linha1,linha2\n"

    def test_backup_de_arquivo_sem_extensao(self, tmp_path):
        """Deve funcionar para arquivos sem extensão."""
        arq = tmp_path / "dados"
        arq.write_text("x")

        backup = criar_backup(arq)

        assert backup is not None
        assert backup.suffix == ""
        assert "_backup_" in backup.name


# ── inspecionar_arquivo ────────────────────────────────────────────────────────

class TestInspecionarArquivo:
    def test_retorna_dict_completo(self, dat_simples):
        """Retorno deve conter todas as chaves esperadas."""
        chaves_esperadas = {
            "path", "size_bytes", "encoding", "rows",
            "max_cols", "short_rows", "empty_cols", "sample",
        }
        info = inspecionar_arquivo(dat_simples)
        assert chaves_esperadas == set(info.keys())

    def test_contagem_de_linhas(self, dat_simples):
        """rows deve contar apenas linhas não-vazias."""
        info = inspecionar_arquivo(dat_simples)
        assert info["rows"] == 3

    def test_max_cols(self, dat_simples):
        """max_cols deve refletir a linha com mais campos."""
        info = inspecionar_arquivo(dat_simples)
        assert info["max_cols"] == 3

    def test_short_rows_zerado_quando_uniforme(self, dat_simples):
        """Se todas as linhas têm o mesmo número de colunas, short_rows == 0."""
        info = inspecionar_arquivo(dat_simples)
        assert info["short_rows"] == 0

    def test_short_rows_detectado(self, dat_linhas_irregulares):
        """Linhas mais curtas que max_cols devem incrementar short_rows."""
        info = inspecionar_arquivo(dat_linhas_irregulares)
        # max_cols=4; linhas de 3 e 2 campos → 2 linhas curtas
        assert info["short_rows"] == 2

    def test_sample_limita_cinco_linhas(self, tmp_path):
        """sample deve ter no máximo 5 entradas."""
        dat = tmp_path / "grande.dat"
        dat.write_text("\n".join(f"{i},val" for i in range(20)), encoding="utf-8")

        info = inspecionar_arquivo(dat)
        assert len(info["sample"]) == 5

    def test_sample_menos_de_cinco_linhas(self, dat_simples):
        """Se o arquivo tem menos de 5 linhas, sample tem todas elas."""
        info = inspecionar_arquivo(dat_simples)
        assert len(info["sample"]) == 3

    def test_size_bytes_correto(self, dat_simples):
        """size_bytes deve coincidir com o tamanho real do arquivo."""
        info = inspecionar_arquivo(dat_simples)
        assert info["size_bytes"] == dat_simples.stat().st_size

    def test_encoding_preservado(self, dat_simples):
        """Encoding passado deve aparecer no resultado."""
        info = inspecionar_arquivo(dat_simples, encoding="utf-8")
        assert info["encoding"] == "utf-8"

    def test_empty_cols_vazio_sem_aplicar_clean(self, dat_colunas_vazias):
        """Sem aplicar_clean=True, empty_cols deve ser lista vazia."""
        info = inspecionar_arquivo(dat_colunas_vazias, aplicar_clean=False)
        assert info["empty_cols"] == []

    def test_empty_cols_detectado_com_aplicar_clean(self, dat_colunas_vazias):
        """Com aplicar_clean=True, colunas 100% vazias devem aparecer em empty_cols."""
        info = inspecionar_arquivo(dat_colunas_vazias, aplicar_clean=True)
        # Coluna de índice 2 está vazia em todas as linhas
        assert 2 in info["empty_cols"]

    def test_nao_modifica_arquivo_original(self, dat_simples):
        """inspecionar_arquivo nunca deve alterar o arquivo de entrada."""
        conteudo_antes = dat_simples.read_bytes()
        inspecionar_arquivo(dat_simples)
        assert dat_simples.read_bytes() == conteudo_antes
