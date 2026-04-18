from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def dat_simples() -> Path:
    """Arquivo .dat com campos simples sem aspas."""
    return FIXTURES_DIR / "simples.dat"


@pytest.fixture()
def dat_aspas_simples() -> Path:
    """Arquivo .dat com campos que contêm vírgula interna entre aspas simples."""
    return FIXTURES_DIR / "aspas_simples.dat"


@pytest.fixture()
def dat_colunas_vazias() -> Path:
    """Arquivo .dat com coluna do meio 100% vazia."""
    return FIXTURES_DIR / "colunas_vazias.dat"


@pytest.fixture()
def dat_linhas_irregulares() -> Path:
    """Arquivo .dat cujas linhas têm números diferentes de colunas."""
    return FIXTURES_DIR / "linhas_irregulares.dat"


@pytest.fixture()
def sps_simples() -> Path:
    """Arquivo .sps apenas com VARIABLE LABELS, sem VALUE LABELS."""
    return FIXTURES_DIR / "simples.sps"


@pytest.fixture()
def sps_com_labels() -> Path:
    """Arquivo .sps com VARIABLE LABELS e VALUE LABELS."""
    return FIXTURES_DIR / "com_labels.sps"


@pytest.fixture()
def sps_concat_labels() -> Path:
    """Arquivo .sps com VARIABLE LABELS no formato de concatenação SPSS."""
    return FIXTURES_DIR / "concat_labels.sps"
