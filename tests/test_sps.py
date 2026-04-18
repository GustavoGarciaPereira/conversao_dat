"""Testes para dat2csv.sps e integração com convert()."""
import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from dat2csv.sps import parse_sps
from dat2csv.converter import convert


# ── parse_sps — variable_labels ───────────────────────────────────────────────

class TestParseVariableLabels:
    def test_extrai_todos_os_nomes(self, sps_simples):
        """Deve extrair todos os VARIABLE LABELS do arquivo."""
        m = parse_sps(sps_simples)
        assert m["variable_labels"] == {"V1": "id", "V2": "nome", "V3": "genero"}

    def test_extrai_com_valor_labels_presente(self, sps_com_labels):
        """Deve extrair VARIABLE LABELS mesmo quando VALUE LABELS existem."""
        m = parse_sps(sps_com_labels)
        vl = m["variable_labels"]
        assert vl["V1"] == "id"
        assert vl["V2"] == "pais"
        assert vl["V3"] == "genero"
        assert vl["V4"] == "escolaridade"

    def test_label_com_ponto_final_nao_incluido(self, sps_simples):
        """O ponto que termina a instrução SPSS não deve fazer parte do label."""
        m = parse_sps(sps_simples)
        assert not any(v.endswith(".") for v in m["variable_labels"].values())

    def test_arquivo_sem_variable_labels(self, tmp_path):
        """Arquivo sem VARIABLE LABELS retorna dict vazio."""
        sps = tmp_path / "vazio.sps"
        sps.write_text("SET UNICODE=ON.\n", encoding="utf-8")
        m = parse_sps(sps, encoding="utf-8")
        assert m["variable_labels"] == {}

    def test_label_com_caracteres_especiais(self, tmp_path):
        """Labels com acentos e pontuação devem ser preservados integralmente."""
        sps = tmp_path / "acentos.sps"
        sps.write_text(
            'VARIABLE LABELS V1 "Gênero (não-binário):".\n',
            encoding="utf-8",
        )
        m = parse_sps(sps, encoding="utf-8")
        assert m["variable_labels"]["V1"] == "Gênero (não-binário):"


# ── parse_sps — value_labels ──────────────────────────────────────────────────

class TestParseValueLabels:
    def test_extrai_mapeamentos(self, sps_com_labels):
        """Deve extrair todos os VALUE LABELS do arquivo."""
        m = parse_sps(sps_com_labels)
        val = m["value_labels"]
        assert val["V2"] == {"AO01": "Portugal", "AO02": "Brasil", "AO03": "Outro"}
        assert val["V3"]["AO01"] == "Masculino"
        assert val["V4"] == {"1": "Fundamental", "2": "Médio", "3": "Superior"}

    def test_multiplas_variaveis(self, sps_com_labels):
        """Deve processar múltiplos blocos VALUE LABELS independentes."""
        m = parse_sps(sps_com_labels)
        assert len(m["value_labels"]) == 3

    def test_sem_value_labels(self, sps_simples):
        """Arquivo sem VALUE LABELS retorna dict vazio para essa chave."""
        m = parse_sps(sps_simples)
        assert m["value_labels"] == {}

    def test_label_sem_ponto_no_meio_do_bloco(self, tmp_path):
        """Entradas intermediárias (sem '.') não devem encerrar o bloco."""
        sps = tmp_path / "bloco.sps"
        sps.write_text(
            'VALUE LABELS  V1\n "A" "Alpha"\n "B" "Beta"\n "C" "Gamma".\n',
            encoding="utf-8",
        )
        m = parse_sps(sps, encoding="utf-8")
        assert len(m["value_labels"]["V1"]) == 3

    def test_dois_blocos_sequenciais(self, tmp_path):
        """Dois blocos VALUE LABELS seguidos devem ser parseados corretamente."""
        sps = tmp_path / "dois.sps"
        sps.write_text(
            'VALUE LABELS  V1\n "1" "Sim".\n'
            'VALUE LABELS  V2\n "1" "Alto"\n "2" "Baixo".\n',
            encoding="utf-8",
        )
        m = parse_sps(sps, encoding="utf-8")
        assert m["value_labels"]["V1"] == {"1": "Sim"}
        assert m["value_labels"]["V2"] == {"1": "Alto", "2": "Baixo"}

    def test_linha_inesperada_encerra_bloco(self, tmp_path):
        """Linha não reconhecida dentro de VALUE LABELS deve encerrar o bloco
        silenciosamente, preservando as entradas já lidas (cobre L81-83)."""
        sps = tmp_path / "ruido.sps"
        sps.write_text(
            'VALUE LABELS  V1\n "1" "Sim"\nEXECUTE.\n "2" "Nao".\n',
            encoding="utf-8",
        )
        m = parse_sps(sps, encoding="utf-8")
        # "1" foi lido antes da linha estranha; "2" ficou fora do bloco
        assert "1" in m["value_labels"]["V1"]
        assert "2" not in m["value_labels"].get("V1", {})


# ── parse_sps — concatenação de strings SPSS ─────────────────────────────────

class TestParseVariableLabelsConcatenacao:
    def test_label_2_segmentos(self, sps_concat_labels):
        """Label quebrada em 2 linhas deve ser concatenada corretamente."""
        m = parse_sps(sps_concat_labels)
        assert m["variable_labels"]["V3"] == (
            "primeira parte da label longa"
            "segunda parte da label longa"
        )

    def test_label_3_segmentos(self, sps_concat_labels):
        """Label quebrada em 3 linhas deve acumular todos os segmentos."""
        m = parse_sps(sps_concat_labels)
        assert m["variable_labels"]["V4"] == "segmento Asegmento Bsegmento C"

    def test_regressao_linha_unica_nao_afetada(self, sps_concat_labels):
        """Labels de linha única devem continuar funcionando normalmente."""
        m = parse_sps(sps_concat_labels)
        assert m["variable_labels"]["V1"] == "id"
        assert m["variable_labels"]["V2"] == "label em linha única"

    def test_label_normal_apos_concat(self, sps_concat_labels):
        """Label de linha única após um bloco concat deve ser parseada."""
        m = parse_sps(sps_concat_labels)
        assert m["variable_labels"]["V6"] == "label normal após concat"

    def test_total_de_labels_extraidas(self, sps_concat_labels):
        """Todas as variáveis do fixture devem ser extraídas."""
        m = parse_sps(sps_concat_labels)
        assert set(m["variable_labels"].keys()) == {"V1", "V2", "V3", "V4", "V5", "V6"}

    def test_concat_sem_fechamento_fail_soft(self, tmp_path):
        """Label concatenada sem linha de continuação deve ser descartada
        silenciosamente (fail-soft); não deve lançar exceção."""
        sps = tmp_path / "incompleta.sps"
        sps.write_text(
            'VARIABLE LABELS V1 "completa".\n'
            'VARIABLE LABELS V2 "sem continuacao"+\n',  # EOF sem continução
            encoding="utf-8",
        )
        m = parse_sps(sps, encoding="utf-8")
        assert m["variable_labels"]["V1"] == "completa"
        assert "V2" not in m["variable_labels"]

    def test_concat_interrompida_por_outra_instrucao(self, tmp_path):
        """Linha inesperada no meio de uma concatenação deve descartar
        a label incompleta e continuar processando o restante."""
        sps = tmp_path / "interrompida.sps"
        sps.write_text(
            'VARIABLE LABELS V1 "inicio"+\n'
            'EXECUTE.\n'                          # interrompe a concat
            'VARIABLE LABELS V2 "preservada".\n',
            encoding="utf-8",
        )
        m = parse_sps(sps, encoding="utf-8")
        assert "V1" not in m["variable_labels"]   # incompleta → descartada
        assert m["variable_labels"]["V2"] == "preservada"

    def test_arquivo_real_extrai_175_labels(self):
        """Smoke test com o arquivo .sps real: todos os 175 VARIABLE LABELS
        devem ser extraídos, incluindo os que usam concatenação."""
        from pathlib import Path
        sps_real = Path(__file__).parent.parent / "data_dat" / "survey_512758_SPSS_syntax_file.sps"
        if not sps_real.exists():
            pytest.skip("arquivo .sps real não disponível")
        m = parse_sps(sps_real)
        assert len(m["variable_labels"]) == 175
        # Verifica especificamente labels que usam concatenação
        assert "V55" in m["variable_labels"]
        assert m["variable_labels"]["V55"].startswith("[Esforço-me")
        assert "V59" in m["variable_labels"]
        assert "forte" in m["variable_labels"]["V59"]


# ── parse_sps — fail-soft ─────────────────────────────────────────────────────

class TestParseSpsFail:
    def test_arquivo_inexistente_retorna_vazios(self, tmp_path, capsys):
        """Arquivo ausente deve retornar dicts vazios e avisar no stderr."""
        m = parse_sps(tmp_path / "nao_existe.sps")
        assert m["variable_labels"] == {}
        assert m["value_labels"] == {}
        assert "Aviso" in capsys.readouterr().err

    def test_erro_de_leitura_retorna_vazios(self, tmp_path, capsys):
        """Falha de I/O deve retornar dicts vazios e avisar no stderr."""
        sps = tmp_path / "erro.sps"
        sps.write_text("x", encoding="utf-8")
        with patch("dat2csv.sps.Path.read_text", side_effect=OSError("falha")):
            m = parse_sps(sps)
        assert m["variable_labels"] == {}
        assert "Aviso" in capsys.readouterr().err


# ── Integração: convert() com sps_path ────────────────────────────────────────

class TestConvertComSps:
    def _dat_3col(self, tmp_path: Path) -> Path:
        """Cria um .dat com 3 colunas: id, pais, genero."""
        dat = tmp_path / "dados.dat"
        dat.write_text(
            "1,'AO01','AO01'\n"
            "2,'AO02','AO02'\n"
            "3,'AO01','AO03'\n",
            encoding="utf-8",
        )
        return dat

    def test_cabecalho_adicionado(self, tmp_path, sps_com_labels):
        """Com sps_path, a primeira linha do CSV deve conter os nomes das variáveis."""
        dat = self._dat_3col(tmp_path)
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False, sps_path=sps_com_labels)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert linhas[0] == ["id", "pais", "genero"]

    def test_dados_apos_cabecalho(self, tmp_path, sps_com_labels):
        """Os dados devem aparecer a partir da segunda linha."""
        dat = self._dat_3col(tmp_path)
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False, sps_path=sps_com_labels)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert len(linhas) == 4   # 1 cabeçalho + 3 dados
        assert linhas[1][0] == "1"

    def test_no_header_suprime_cabecalho(self, tmp_path, sps_com_labels):
        """add_header=False deve suprimir o cabeçalho mesmo com sps_path."""
        dat = self._dat_3col(tmp_path)
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False,
                sps_path=sps_com_labels, add_header=False)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert len(linhas) == 3
        assert linhas[0][0] == "1"

    def test_apply_labels_substitui_codigos(self, tmp_path, sps_com_labels):
        """apply_labels=True deve substituir AO01/AO02 pelo texto correspondente."""
        dat = self._dat_3col(tmp_path)
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False,
                sps_path=sps_com_labels, apply_labels=True)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        # Linha 1 (dados): V2=AO01→Portugal, V3=AO01→Masculino
        assert linhas[1][1] == "Portugal"
        assert linhas[1][2] == "Masculino"

    def test_apply_labels_false_mantem_codigos(self, tmp_path, sps_com_labels):
        """Sem apply_labels, os códigos brutos devem permanecer no CSV."""
        dat = self._dat_3col(tmp_path)
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False,
                sps_path=sps_com_labels, apply_labels=False)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        assert linhas[1][1] == "AO01"

    def test_sem_sps_comportamento_original(self, dat_simples, tmp_path):
        """Sem sps_path, o comportamento deve ser idêntico ao original."""
        out = tmp_path / "out.csv"
        result = convert(dat_simples, out, backup=False)
        assert result["rows"] == 3
        assert result["columns"] == 3
        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))
        assert linhas[0][0] == "1"   # sem cabeçalho, começa direto nos dados

    def test_sps_inexistente_continua_sem_metadados(self, dat_simples, tmp_path, capsys):
        """sps_path apontando para arquivo inexistente deve gerar aviso e continuar."""
        out = tmp_path / "out.csv"
        result = convert(dat_simples, out, backup=False,
                         sps_path=tmp_path / "nao_existe.sps")
        assert result["rows"] == 3
        assert "Aviso" in capsys.readouterr().err

    def test_cabecalho_com_variavel_ausente_usa_nome_padrao(self, tmp_path):
        """Colunas sem label no .sps devem usar 'VN' como nome no cabeçalho."""
        dat = tmp_path / "d.dat"
        dat.write_text("1,A,X\n", encoding="utf-8")
        sps = tmp_path / "parcial.sps"
        sps.write_text('VARIABLE LABELS V1 "codigo".\n', encoding="utf-8")
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False, sps_path=sps)

        with out.open(encoding="utf-8") as f:
            cabecalho = next(csv.reader(f))

        assert cabecalho[0] == "codigo"
        assert cabecalho[1] == "V2"
        assert cabecalho[2] == "V3"

    def test_cabecalho_respeita_clean(self, tmp_path, sps_com_labels):
        """Com clean=True, o cabeçalho deve ter as mesmas colunas que os dados."""
        dat = tmp_path / "d.dat"
        # col 2 (V2) será 100% vazia
        dat.write_text("1,,X\n2,,Y\n", encoding="utf-8")
        out = tmp_path / "out.csv"
        convert(dat, out, encoding="utf-8", backup=False,
                sps_path=sps_com_labels, clean=True)

        with out.open(encoding="utf-8") as f:
            linhas = list(csv.reader(f))

        # Cabeçalho e dados devem ter o mesmo número de colunas
        assert len(linhas[0]) == len(linhas[1])
        assert "pais" not in linhas[0]   # coluna vazia removida
