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

**Propósito:** Converter arquivos `.dat` gerados por plataformas de pesquisa (LimeSurvey, SPSS,
Sniffy) para CSV limpo. Os diferenciais em relação a um simples `split(',')` são:

- Backup automático com timestamp antes de sobrescrever qualquer saída
- Hash SHA256 do arquivo de entrada para auditoria de integridade
- Modo inspeção (`--inspect`) que analisa o arquivo sem gerar saída
- Limpeza opcional de colunas 100% vazias (`--clean`)
- Parse correto de campos com vírgula interna (aspas simples como quotechar)

---

## Estrutura de Diretórios

```
conversao_dat/
├── dat2csv/
│   ├── __init__.py        # Expõe convert(); define __version__
│   ├── __main__.py        # Permite execução com python -m dat2csv
│   ├── converter.py       # _parse_dat() + convert() — lógica principal
│   ├── cli.py             # Interface argparse; entry point do comando dat2csv
│   └── utils.py           # calcular_hash(), criar_backup(), inspecionar_arquivo()
├── tests/
│   ├── conftest.py        # Fixtures de Path para os arquivos .dat de exemplo
│   ├── test_converter.py  # Testes de _parse_dat() e convert()
│   ├── test_utils.py      # Testes de calcular_hash(), criar_backup(), inspecionar_arquivo()
│   └── fixtures/          # Arquivos .dat pequenos usados nos testes
│       ├── simples.dat
│       ├── aspas_simples.dat
│       ├── colunas_vazias.dat
│       └── linhas_irregulares.dat
├── pyproject.toml         # Metadados, entry point (dat2csv = dat2csv.cli:main), [dev] extras
├── README.md              # Documentação voltada ao usuário final
├── LICENSE                # MIT
└── CLAUDE.md              # Este arquivo
```

---

## Decisões de Design

### Por que `csv.reader` com `quotechar="'"`?
Os arquivos `.dat` alvo usam aspas simples para envolver strings que podem conter vírgulas
(ex.: `'valor com, vírgula'`). Um `split(',')` quebraria esse campo incorretamente.

### Por que `_parse_dat()` é privada e compartilhada?
`utils.inspecionar_arquivo()` precisa usar exatamente a mesma lógica de leitura de
`converter.convert()`. Centralizar o parse em `_parse_dat()` (em `converter.py`) garante
isso. `utils.py` importa `_parse_dat` de `converter`; a importação inversa dentro de
`convert()` (para `criar_backup`) é feita localmente para evitar ciclo.

### Por que o backup é feito antes da escrita?
Para preservar dados do usuário em caso de interrupção ou arrependimento. O arquivo anterior
é movido (não copiado) para `<stem>_backup_YYYYMMDD_HHMMSS<suffix>` antes de o arquivo de
saída ser aberto para escrita.

### Por que o hash é calculado em blocos de 64 KB?
Para não carregar arquivos grandes inteiros na memória. Ver `utils.calcular_hash()`.

---

## Comandos Úteis

```bash
# Instalar em modo editável (recomendado para desenvolvimento)
pip install -e .

# Instalar com dependências de desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest -v

# Rodar a ferramenta (após instalação)
dat2csv dados.dat
dat2csv dados.dat --inspect --clean
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

---

## Fluxo de Trabalho com Git

- Branch principal: `main`
- Commits seguem padrão semântico: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- **Não incluir** linha `Co-Authored-By:` nas mensagens de commit

---

## Notas para Assistentes de IA

- Manter separação clara entre `converter.py` (parse/escrita), `utils.py` (auxiliares) e
  `cli.py` (interface). Não misturar responsabilidades.
- Ao adicionar novas funcionalidades, criar testes em `tests/` antes de considerar concluído.
- Novas flags da CLI devem aparecer no `--help` (argparse), na tabela do README e neste arquivo.
- Manter compatibilidade com Windows: usar `Path` em vez de strings de caminho, respeitar
  `encoding` explícito em todas as operações de I/O.
- O arquivo `.dat` de entrada **nunca** deve ser modificado — apenas lido.
- `*.csv` está no `.gitignore`; arquivos de saída gerados localmente não entram no repositório.
