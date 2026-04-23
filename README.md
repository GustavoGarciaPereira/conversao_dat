# dat2csv

> Conversor seguro de arquivos `.dat` de pesquisas para CSV

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-117%20passed-brightgreen)

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

### Preview do CSV (`--preview`)

Exibe as primeiras linhas do CSV que seria gerado, sem criar arquivo. Útil para verificar rapidamente o resultado da conversão.

A saída é formatada como tabela alinhada (poucos campos) ou lista vertical (muitos campos). Datasets com mais de 20 colunas mudam automaticamente para o modo vertical. Use `--raw` para obter o CSV bruto.

```bash
dat2csv dados.dat --preview
```

```
+---+-------+-----+
| 1 | dois  | 3   |
+---+-------+-----+
| 4 | cinco | 6   |
| 7 | oito  | 9   |
+---+-------+-----+
```

```bash
dat2csv dados.dat --sps sintaxe.sps --apply-labels --preview 3
```

```
+----+-----------+-------------+
| id | pais      | genero      |
+----+-----------+-------------+
| 1  | Portugal  | Feminino    |
| 2  | Brasil    | Não binário |
| 3  | Espanha   | Masculino   |
+----+-----------+-------------+
```

```bash
dat2csv dados.dat --sps sintaxe.sps --apply-labels --preview 3 --raw
```

```
id,pais,genero
1,Portugal,Feminino
2,Brasil,Não binário
3,Espanha,Masculino
```

### Preview com datasets de muitas colunas (modo vertical automático)

Quando o CSV tiver mais de 20 colunas, o preview muda automaticamente para o modo vertical,
exibindo cada linha como uma lista `nome_coluna : valor`. Use `--cols N` para controlar
quantas colunas são exibidas por linha (padrão: 10).

```bash
dat2csv survey.dat --sps sintaxe.sps --apply-labels --preview 2
```

```
── Linha 1 ──────────────────────────────────────────────────────────────────────────────
  id            : 1
  submitdate    : 
  lastpage      : 1
  startlanguage : pt
  seed          : 1616738727
  Nacionalidade : Portuguesa
  genero        : Feminino
  idade         : 25
  pais          : Portugal
  escolaridade  : Superior
  (+ 165 colunas omitidas de 175)

── Linha 2 ──────────────────────────────────────────────────────────────────────────────
  id            : 2
  ...
  (+ 165 colunas omitidas de 175)
```

```bash
# Ver apenas 5 colunas por linha
dat2csv survey.dat --sps sintaxe.sps --apply-labels --preview 2 --cols 5
```

```
── Linha 1 ──────────────────────────────────────────────────────────────────────────────
  id            : 1
  submitdate    : 
  lastpage      : 1
  startlanguage : pt
  seed          : 1616738727
  (+ 170 colunas omitidas de 175)
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

## Interface gráfica

O dat2csv também pode ser usado através de uma interface gráfica desktop, construída com
**Tkinter** (biblioteca padrão do Python — sem dependências externas).

### Requisitos

- Python 3.10 ou superior
- Tkinter (geralmente já incluso na instalação padrão do Python;
  em distribuições Linux pode ser necessário instalar o pacote `python3-tk`)

### Como executar

```bash
python -m dat2csv.gui
```

Se o pacote foi instalado via `pip install -e .`, o comando `dat2csv-gui` também fica
disponível:

```bash
dat2csv-gui
```

### Funcionalidades

- **Seleção de arquivos** via diálogos nativos: entrada `.dat` (obrigatório),
  sintaxe `.sps` (opcional) e saída `.csv` (opcional; se não informado, usa `<input>.csv`)
- **Checkboxes** para ativar as opções `--apply-labels`, `--clean`, `--no-backup` e `--hash`
- **Botão Converter:** executa a conversão em uma thread separada — a interface não trava
  mesmo com arquivos grandes; o resumo (linhas, colunas, backup, hash) é exibido na área de log
- **Botão Preview:** exibe as primeiras N linhas do CSV que seria gerado (N configurável via
  spinner ao lado do botão), sem criar arquivo, formatadas como tabela (horizontal ou vertical
  conforme o número de colunas)
- **Log rolável:** toda a saída de diagnóstico aparece na janela; erros são reportados em
  caixas de diálogo

### Exemplo de uso

1. Execute `python -m dat2csv.gui`
2. Clique em "Procurar…" ao lado de "Arquivo .dat" e selecione o arquivo desejado
3. Opcional: selecione um arquivo `.sps` e marque "Aplicar rótulos do .sps"
4. Opcional: marque "Remover colunas vazias" e/ou "Exibir hash SHA256"
5. Ajuste o spinner "Linhas" e clique em **Preview** para visualizar o resultado antes de converter
6. Clique em **Converter** para gerar o CSV final

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

# Preview do CSV (sem criar arquivo)
from dat2csv.utils import preview_csv_preview
preview = preview_csv_preview("dados.dat", sps_path="sintaxe.sps", n=3)
print(preview)
# id,nome,genero
# 1,dois,3
# 4,cinco,6

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
| `--preview [N]` | Exibe as primeiras N linhas do CSV que seria gerado, sem criar arquivo (padrão: 5). Não pode ser usado com `--inspect`. |
| `--raw` | Com `--preview`, imprime o CSV bruto (sem formatação de tabela). |
| `--cols N` | Número máximo de colunas a exibir no preview (padrão: 10). No modo horizontal trunca a tabela; no modo vertical lista apenas as primeiras N colunas por linha. |
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
