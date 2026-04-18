# dat2csv

> Conversor seguro de arquivos `.dat` de pesquisas para CSV

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-86%20passed-brightgreen)

Converte arquivos `.dat` gerados por plataformas de pesquisa (LimeSurvey, SPSS, etc.)
para CSV limpo, com suporte a aspas simples, detecção de colunas vazias, backup automático,
verificação de integridade via hash SHA256 e metadados SPSS (cabeçalho + rótulos de valor).

---

## Instalação

> **Atenção:** é necessário ter o `pip` instalado na sua máquina.

**A partir do repositório local:**

```bash
git clone https://github.com/GustavoGarciaPereira/conversao_dat.git
cd conversao_dat
pip install -e .
```

**A partir do GitHub (sem clonar):**

```bash
pip install git+https://github.com/GustavoGarciaPereira/conversao_dat.git
```

**Atualizar para a versão mais recente:**

```bash
# Se instalou via git clone (modo editável)
cd conversao_dat
git pull
pip install -e .

# Se instalou via git+ URL (Linux / macOS)
pip install --upgrade git+https://github.com/GustavoGarciaPereira/conversao_dat.git

# Windows — forçar re-download (PowerShell)
pip install --upgrade --force-reinstall --no-cache-dir git+https://github.com/GustavoGarciaPereira/conversao_dat.git
```

Após a instalação, o comando `dat2csv` estará disponível no terminal.

---

## Uso — linha de comando

### Conversão básica (Linux / macOS)

```bash
dat2csv dados.dat
# Saída: dados.csv (mesmo diretório)

dat2csv dados.dat resultados/limpo.csv
# Saída: resultados/limpo.csv
```

```
Arquivo convertido com sucesso!
  Entrada:  dados.dat
  Saída:    dados.csv
  Linhas:   1280
  Colunas:  147
```

### Conversão básica (PowerShell Windows)

```bash
python -m dat2csv dados.dat
```

```
Arquivo convertido com sucesso!
  Entrada:  dados.dat
  Saída:    dados.csv
  Linhas:   1280
  Colunas:  147
```

### Usar metadados SPSS (`--sps`)

Adiciona cabeçalho com os nomes das variáveis a partir de um arquivo `.sps`:

```bash
dat2csv dados.dat --sps sintaxe.sps
```

```
Arquivo convertido com sucesso!
  Entrada:  dados.dat
  Saída:    dados.csv
  Linhas:   1280
  Colunas:  147
  Metadados .sps: sintaxe.sps
```

### Substituir códigos por rótulos (`--sps --apply-labels`)

Substitui valores como `AO01`, `AO02` pelos textos definidos no `.sps`:

```bash
dat2csv dados.dat --sps sintaxe.sps --apply-labels
```

```
Arquivo convertido com sucesso!
  Entrada:  dados.dat
  Saída:    dados.csv
  Linhas:   1280
  Colunas:  147
  Metadados .sps: sintaxe.sps
```

### Suprimir cabeçalho (`--no-header`)

```bash
dat2csv dados.dat --sps sintaxe.sps --no-header
```

### Remover colunas 100% vazias (`--clean`)

```bash
dat2csv dados.dat --clean
```

```
Arquivo convertido com sucesso!
  Entrada:  dados.dat
  Saída:    dados.csv
  Linhas:   1280
  Colunas:  58
  Colunas removidas (--clean): 89
```

### Inspecionar sem converter (`--inspect`)

```bash
dat2csv dados.dat --inspect
```

```
📄 Arquivo:  dados.dat
📏 Tamanho:  2.4 MB
🔤 Encoding: utf-8-sig
📊 Linhas:   1.280
📐 Colunas máximas: 147

⚠️  Atenção: 23 linhas possuem menos colunas que o máximo.
   Serão preenchidas com vazio na conversão.

📋 Amostra (5 primeiras linhas):
  [1] 1,,1,pt,1616738727,AO01,…
  [2] 2,,0,pt,1733525872
  [3] 3,,2,pt,1445270123,AO02,…
```

### Simular limpeza antes de converter (`--inspect --clean`)

```bash
dat2csv dados.dat --inspect --clean
```

```
🔧 Com --clean: 89 colunas seriam removidas (100% vazias).
```

### Verificar integridade com hash SHA256 (`--hash`)

```bash
dat2csv dados.dat resultado.csv --hash
```

```
🔒 Hash SHA256 do original: a1b2c3d4e5f6...
📦 Backup criado: resultado_backup_20260117_143022.csv (arquivo anterior preservado)
Arquivo convertido com sucesso!
```

### Desabilitar backup automático (`--no-backup`)

```bash
dat2csv dados.dat resultado.csv --no-backup
```

### Encoding personalizado

```bash
dat2csv dados.dat --encoding latin-1
```

---

## Uso — Python

```python
from dat2csv import convert

# Conversão simples
result = convert("dados.dat", "resultado.csv")
print(result)
# {'rows': 1280, 'columns': 147, 'backup': None}

# Com metadados SPSS (cabeçalho + substituição de labels)
result = convert(
    "dados.dat", "resultado.csv",
    sps_path="sintaxe.sps",
    apply_labels=True,
)
print(result)
# {'rows': 1280, 'columns': 147, 'backup': None}

# Com limpeza de colunas vazias
result = convert("dados.dat", "resultado.csv", clean=True)
print(result)
# {'rows': 1280, 'columns': 58, 'backup': PosixPath('resultado_backup_...csv'), 'removed_cols': 89}
```

```python
from dat2csv.utils import inspecionar_arquivo, calcular_hash
from dat2csv.sps import parse_sps

# Inspecionar sem gerar arquivo
info = inspecionar_arquivo("dados.dat", aplicar_clean=True)
print(f"Linhas: {info['rows']}, Colunas: {info['max_cols']}")
print(f"Colunas vazias: {len(info['empty_cols'])}")

# Calcular hash
digest = calcular_hash("dados.dat")
print(f"SHA256: {digest}")

# Ler metadados do .sps diretamente
meta = parse_sps("sintaxe.sps")
print(meta["variable_labels"])   # {'V1': 'id', 'V2': 'Género:', ...}
print(meta["value_labels"]["V6"])  # {'AO01': 'Portuguesa', 'AO02': 'Brasileira', ...}
```

---

## Formato suportado

Arquivos `.dat` em que:

- campos são separados por **vírgula**
- strings são delimitadas por **aspas simples** — ex.: `'valor com, vírgula'`
- colunas vazias no final de cada linha são ignoradas automaticamente
- encoding padrão: `utf-8-sig` (com suporte a BOM)

Exemplo de linha válida:

```
1,,2,'pt','1616738727','AO01','AO01',,
```

---

## Segurança e Integridade dos Dados

| Recurso | Comportamento |
|---|---|
| **Backup automático** | Se o arquivo de saída já existir, é renomeado para `<nome>_backup_YYYYMMDD_HHMMSS.csv` antes de qualquer escrita |
| **Hash SHA256** | Flag `--hash` calcula e exibe o hash do arquivo de entrada; útil para auditoria e comparação de versões |
| **Somente leitura da entrada** | Os arquivos `.dat` e `.sps` originais nunca são modificados |
| **Falha segura no backup** | Erro ao criar backup gera aviso no stderr, mas a conversão prossegue normalmente |
| **Falha segura no .sps** | `.sps` ausente ou ilegível gera aviso no stderr; conversão continua sem metadados |

---

## Referência de flags

| Flag | Descrição |
|---|---|
| `--sps ARQUIVO.sps` | Arquivo de sintaxe SPSS com nomes e rótulos das variáveis |
| `--apply-labels` | Substitui códigos pelos rótulos de valor definidos no `.sps` (requer `--sps`) |
| `--no-header` | Suprime a linha de cabeçalho mesmo quando `--sps` é fornecido |
| `--inspect` | Analisa o arquivo sem gerar CSV |
| `--clean` | Remove colunas 100% vazias; com `--inspect`, simula a remoção |
| `--hash` | Exibe o hash SHA256 do arquivo de entrada |
| `--no-backup` | Desabilita o backup automático do arquivo de saída |
| `--encoding ENC` | Define o encoding do arquivo de entrada (padrão: `utf-8-sig`) |

---

## Como contribuir

1. Faça um fork do repositório
2. Crie uma branch: `git checkout -b minha-feature`
3. Instale as dependências de desenvolvimento: `pip install -e ".[dev]"`
4. Rode os testes: `pytest -v`
5. Abra um Pull Request

---

## Licença

[MIT](LICENSE) © [SEU NOME]
