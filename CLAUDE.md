# CLAUDE.md – dat2csv

Este arquivo contém informações essenciais para que assistentes de IA (como o Claude Code)
entendam rapidamente a estrutura, as convenções e as decisões de design deste projeto.

---

## Visão Geral

| Campo | Valor |
|---|---|
| **Nome do pacote** | `dat2csv` |
| **Nome do repositório** | `conversao_dat` |
| **Público-alvo** | Pesquisadores e usuários não técnicos |
| **Python mínimo** | 3.10 |
| **Dependências externas** | Nenhuma (somente biblioteca padrão) |
| **Testes** | 117 passando, cobertura 100% |

**Propósito:** Converter arquivos `.dat` gerados por plataformas de pesquisa (LimeSurvey, SPSS,
Sniffy) para CSV limpo. Os diferenciais em relação a um simples `split(',')` são:

- Parse correto de campos com vírgula interna (aspas simples como quotechar)
- Backup automático com timestamp antes de sobrescrever qualquer saída
- Hash SHA256 do arquivo de entrada para auditoria de integridade
- Modo inspeção (`--inspect`) que analisa o arquivo sem gerar saída
- Limpeza opcional de colunas 100% vazias (`--clean`)
- Suporte a metadados SPSS (`--sps`): cabeçalho com nomes das variáveis e substituição de códigos por rótulos
- Preview inteligente (`--preview`): tabela horizontal para poucos campos, modo vertical automático para datasets com mais de 20 colunas; `--cols N` controla quantas colunas exibir

---

## Estrutura de Diretórios

```
conversao_dat/
├── dat2csv/
│   ├── __init__.py        # Expõe convert(); define __version__
│   ├── __main__.py        # Permite execução com python -m dat2csv
│   ├── converter.py       # _parse_dat(), _apply_value_labels(), convert()
│   ├── cli.py             # Interface argparse; entry point do comando dat2csv
│   ├── utils.py           # calcular_hash(), criar_backup(), inspecionar_arquivo()
│   └── sps.py             # parse_sps() — lê VARIABLE LABELS e VALUE LABELS do .sps
├── tests/
│   ├── conftest.py        # Fixtures de Path para os arquivos de exemplo
│   ├── test_converter.py  # Testes de _parse_dat() e convert()
│   ├── test_utils.py      # Testes de calcular_hash(), criar_backup(), inspecionar_arquivo()
│   ├── test_sps.py        # Testes de parse_sps() e integração convert()+sps
│   └── fixtures/          # Arquivos de exemplo usados nos testes
│       ├── simples.dat
│       ├── aspas_simples.dat
│       ├── colunas_vazias.dat
│       ├── linhas_irregulares.dat
│       ├── simples.sps    # Apenas VARIABLE LABELS
│       └── com_labels.sps # VARIABLE LABELS + VALUE LABELS
├── .coveragerc            # Exclui cli.py e __main__.py do relatório de cobertura
├── pyproject.toml         # Metadados, entry point, [dev] extras, [project.urls]
├── README.md              # Documentação voltada ao usuário final
├── LICENSE                # MIT
└── CLAUDE.md              # Este arquivo
```

---

## Módulos — Responsabilidades

| Módulo | Responsabilidade |
|---|---|
| `converter.py` | Parse do `.dat` (`_parse_dat`), substituição de labels, limpeza de colunas, escrita do CSV |
| `utils.py` | Hash de integridade, backup com timestamp, inspeção sem saída, preview do CSV, formatação de tabela, formatação de terminal |
| `sps.py` | Parser de sintaxe SPSS: extrai `variable_labels` e `value_labels` |
| `cli.py` | Interface argparse, validação de argumentos, saída no terminal |

---

## Decisões de Design

### Por que `csv.reader` com `quotechar="'"`?
Os arquivos `.dat` alvo usam aspas simples para envolver strings que podem conter vírgulas
(ex.: `'valor com, vírgula'`). Um `split(',')` quebraria esse campo incorretamente.

### Por que `_parse_dat()` é privada e compartilhada?
`utils.inspecionar_arquivo()` precisa usar exatamente a mesma lógica de leitura de
`converter.convert()`. Centralizar o parse em `_parse_dat()` garante consistência.
`utils.py` importa `_parse_dat` de `converter`; a importação inversa dentro de
`convert()` (para `criar_backup`) é feita localmente para evitar ciclo de importação.

### Por que o backup é feito antes da escrita?
Para preservar dados do usuário em caso de interrupção ou arrependimento. O arquivo anterior
é movido (não copiado) para `<stem>_backup_YYYYMMDD_HHMMSS<suffix>` antes de o arquivo de
saída ser aberto para escrita.

### Por que o hash é calculado em blocos de 64 KB?
Para não carregar arquivos grandes inteiros na memória. Ver `utils.calcular_hash()`.

### Por que o parser do `.sps` usa state machine em vez de regex multi-linha?
O formato real do LimeSurvey tem blocos `VALUE LABELS` com número variável de linhas,
terminados por `.` na última entrada. Uma state machine linha a linha é mais robusta e
mais fácil de depurar do que uma regex multi-linha. O parser é fail-soft: erros de leitura
geram aviso em stderr e retornam dicts vazios, sem interromper a conversão.

### Formato real do `.sps` (LimeSurvey)
```
VARIABLE LABELS V1 "id".          ← uma por linha, termina com ponto
VARIABLE LABELS V2 "Género:".

VALUE LABELS  V12                  ← cabeçalho do bloco
 "AO01" "Masculino"                ← entradas sem ponto (exceto a última)
 "AO02" "Feminino"
 "AO03" "Não binário".             ← ponto encerra o bloco
```
Os nomes de variáveis seguem o padrão `V1`, `V2`, …, `VN` correspondendo às colunas do `.dat`.

---

## Comandos Úteis

```bash
# Instalar em modo editável (recomendado para desenvolvimento)
pip install -e .

# Instalar com dependências de desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest -v

# Cobertura de testes
pytest --cov=dat2csv --cov-report=term-missing

# Conversão básica
dat2csv dados.dat

# Com metadados SPSS (cabeçalho + substituição de labels)
dat2csv dados.dat --sps sintaxe.sps --apply-labels

# Preview das primeiras linhas (sem criar arquivo)
dat2csv dados.dat --preview 3

# Preview de dataset com muitas colunas — modo vertical automático, 5 colunas por linha
dat2csv survey.dat --sps sintaxe.sps --apply-labels --preview 2 --cols 5

# Inspecionar + simular limpeza
dat2csv dados.dat --inspect --clean

# Com hash e sem backup
dat2csv dados.dat saida.csv --hash --no-backup

# Rodar sem instalar (útil no Windows com PowerShell)
python -m dat2csv dados.dat

# Gerar distribuição
python -m build

# Publicar no PyPI
twine upload dist/*
```

---

## Flags da CLI

| Flag | Padrão | Descrição |
|---|---|---|
| `input` | — | Arquivo `.dat` de entrada (obrigatório) |
| `output` | `<input>.csv` | Arquivo `.csv` de saída (opcional) |
| `--encoding` | `utf-8-sig` | Encoding do arquivo de entrada |
| `--inspect` | `False` | Analisa sem gerar CSV |
| `--clean` | `False` | Remove colunas 100% vazias |
| `--hash` | `False` | Exibe SHA256 do arquivo de entrada |
| `--no-backup` | `False` | Desabilita backup automático da saída |
| `--sps` | `None` | Arquivo `.sps` com metadados SPSS |
| `--apply-labels` | `False` | Substitui códigos pelos rótulos do `.sps` (requer `--sps`) |
| `--no-header` | `False` | Suprime cabeçalho mesmo quando `--sps` é fornecido |
| `--preview` | `None` | Exibe as primeiras N linhas do CSV que seria gerado, sem criar arquivo (padrão: 5). Não pode ser usado com `--inspect`. |
| `--raw` | `False` | Com `--preview`, imprime o CSV bruto (sem formatação de tabela). |
| `--cols` | `10` | Número máximo de colunas a exibir no preview. No modo vertical (>20 colunas) lista as primeiras N colunas por linha; no modo horizontal trunca a tabela. |

---

## API Python

```python
from dat2csv import convert
from dat2csv.utils import calcular_hash, inspecionar_arquivo
from dat2csv.sps import parse_sps

# Conversão simples
result = convert("dados.dat", "saida.csv", backup=False)
# → {'rows': 242, 'columns': 175, 'backup': None}

# Com metadados SPSS
result = convert(
    "dados.dat", "saida.csv",
    sps_path="sintaxe.sps",
    apply_labels=True,
    add_header=True,
    backup=False,
)

# Apenas parse do .sps
meta = parse_sps("sintaxe.sps")
# → {'variable_labels': {'V1': 'id', ...}, 'value_labels': {'V6': {'AO01': 'Portuguesa', ...}}}

# Inspecionar sem gerar arquivo
info = inspecionar_arquivo("dados.dat", aplicar_clean=True)
# → {'rows': 242, 'max_cols': 175, 'short_rows': 241, 'empty_cols': [...], ...}

# Preview do CSV (sem criar arquivo)
from dat2csv.utils import preview_csv_preview, format_csv_table
preview = preview_csv_preview("dados.dat", sps_path="sintaxe.sps", n=3)
# → "id,nome,genero\n1,dois,3\n4,cinco,6\n7,oito,9"

# Formatar CSV como tabela (horizontal ≤20 colunas, vertical >20 colunas)
tabela = format_csv_table(preview, max_cols_display=10, has_header=True)
# Com force_transpose=True: força modo vertical independente do nº de colunas
```

---

## Fluxo de Trabalho com Git

- Branch principal: `main`
- Commits seguem padrão semântico: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- **Não incluir** linha `Co-Authored-By:` nas mensagens de commit

---

## Notas para Assistentes de IA

- Manter separação clara entre módulos: `converter.py` (parse/escrita), `utils.py` (auxiliares),
  `sps.py` (metadados SPSS), `cli.py` (interface). Não misturar responsabilidades.
- Ao adicionar novas funcionalidades, criar testes em `tests/` antes de considerar concluído.
- Novas flags da CLI devem aparecer: no `--help` (argparse), na tabela de flags deste arquivo,
  na tabela do README e na `pyproject.toml` se relevante.
- Manter compatibilidade com Windows: usar `Path` em vez de strings de caminho, respeitar
  `encoding` explícito em todas as operações de I/O.
- O arquivo `.dat` e o `.sps` de entrada **nunca** devem ser modificados — apenas lidos.
- `*.csv` está no `.gitignore`; arquivos de saída gerados localmente não entram no repositório.
- Cobertura de testes deve permanecer em 100% para todos os módulos (exceto `cli.py` e
  `__main__.py`, excluídos via `.coveragerc`).
- O parser `sps.py` é fail-soft: sempre retorna dicts (possivelmente vazios) e nunca lança
  exceção — avisa em stderr e segue em frente.
