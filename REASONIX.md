# Reasonix — dat2csv

> Arquitetura completa, decisões de design e API Python: ver `CLAUDE.md`.
> Aqui estão apenas as regras operacionais, comandos e restrições para o agente.

---

## Ambiente Docker
 
Este projeto roda dentro de um container Docker (`reasonix-python`).
Python e ferramentas estão instalados **globalmente** — sem venv.
 
### Comandos que funcionam (spawn direto)
 
```
pytest -v
pytest --cov=dat2csv --cov-report=term-missing
python -m dat2csv dados.dat
python -c "from dat2csv.gui import main; print('OK')"
pip show dat2csv
coverage report
```
 
### ⚠️ Limitações do run_command neste ambiente
 
O `run_command` usa `spawn` direto, **sem shell intermediário**.
Isso significa que NÃO funcionam:
 
- Pipes: `pytest -v | tail -20`  → use `pytest -v` e leia a saída completa
- Redirects: `pytest 2>/dev/null` → não use, rode sem redirect
- Operadores: `cmd1 && cmd2`     → rode cada comando separado
- Builtins: `command -v python`  → use `which python` ou `python --version`
- Caminhos relativos com `./`:   `./venv/bin/pytest` → use `pytest` direto
### venv do host
 
O diretório `venv/` na raiz do projeto **não deve ser usado** dentro do container.
Está lá apenas para desenvolvimento local no host.
O container tem Python e pytest instalados globalmente em `/usr/local/bin/`.


## Convenções de código

| Regra | Valor |
|---|---|
| **Linguagem** | Python >= 3.10 |
| **Estilo** | `snake_case` para funções, variáveis, módulos; `PascalCase` para classes |
| **Dependências externas** | Nenhuma obrigatória; `openpyxl` opcional para `--excel` |
| **Formatação** | Nenhum linter configurado. Linhas até ~100 chars, imports: stdlib → local. |
| **Tipagem** | Type hints em todas as funções públicas. `# type: ignore` só com justificativa. |
| **Testes** | `pytest` + `coverage`. Cobertura 100% em `converter.py`, `utils.py`, `sps.py`. Execute `pytest` para verificar o estado atual. |

---

## Comandos úteis

### Seguros — Reasonix pode rodar sem confirmação

```bash
pytest -v
pytest --cov=dat2csv --cov-report=term-missing
python -m dat2csv dados.dat --preview 3
python -m dat2csv dados.dat --inspect
python -m dat2csv dados.dat --inspect --clean
dat2csv dados.dat --sps meta.sps --apply-labels --preview 2
```

### Requerem confirmação do usuário

```bash
pip install -e ".[dev]"                    # altera o ambiente Python
git push, git commit --amend, git rebase   # alterações no repositório
python -m build                            # gera distribuição
twine upload dist/*                        # publica no PyPI
```

---

## Regras específicas para IA

- **Parser `.sps` é fail-soft:** `parse_sps()` sempre retorna dict (possivelmente vazio). Nunca lança exceção — avisa em stderr e segue. **Não adicionar validação que quebre esse contrato.**
- **Nunca modificar arquivos de entrada (`.dat`, `.sps`):** são apenas lidos. Toda saída vai para um novo `.csv`.
- **`csv.reader` com `quotechar="'"`** — os `.dat` usam aspas simples para campos com vírgula interna. **Não trocar para `csv.DictReader` nem para `split(',')`.**
- **`_parse_dat()` é compartilhada:** `converter.convert()` e `utils.inspecionar_arquivo()` usam a mesma função. Qualquer mudança no parse deve manter os dois consumidores funcionando.
- **Hash em blocos de 64 KB** (`calcular_hash`) — não carregar o arquivo inteiro na memória.
- **Backup por move, não por cópia:** `criar_backup()` usa `shutil.move`. O original deixa de existir no caminho original.
- **Early return:** prefira `if not x: return` no topo de funções em vez de aninhar.
- **Evitar `Any`:** use `dict` com tipo concreto ou `TypedDict`. Se inevitável, documente.
- **Novas flags da CLI** devem ser adicionadas em 4 lugares: `argparse`, `--help`, tabela de flags no `README.md`, e `CLAUDE.md`. Sempre com testes em `tests/`.
- **Compatibilidade Windows:** usar `Path` em vez de strings, `encoding` explícito, `newline=""` em `open()` para CSV.
- **Toda função pública** deve ter docstring (Args/Returns).
- **`*.csv` está no `.gitignore`** — arquivos gerados nunca entram no repositório.

### ⚠️ Coisas que o modelo quase sempre erra neste projeto

1. **Trocar `csv.reader` por `split(',')`** — as aspas simples tornam `split` incorreto. Sempre use `csv.reader(f, quotechar="'")`.
2. **Usar `csv.DictReader`** — o `.dat` não tem cabeçalho interno. Os nomes vêm do `.sps` (ou são `V1`, `V2`, …). `DictReader` produziria chaves erradas.
3. **Modificar `tests/fixtures/`** — esses arquivos são a verdade dos testes. Qualquer alteração quebra a suíte.
4. **Adicionar validação que lança exceção no `parse_sps()`** — o contrato é fail-soft. Avisa e retorna dict vazio, nunca aborta.
5. **Escrever no diretório errado** — a saída sempre vai para o mesmo diretório do `.dat` de entrada, a menos que `output` seja um caminho absoluto.

---

## Tipos de mudança que exigem `/plan`

- Migrações de parser (mudar `csv.reader` para outra estratégia)
- Adicionar dependência externa obrigatória (openpyxl é opcional)
- Mudar a assinatura de `convert()` (quebra API pública)
- Qualquer alteração em `tests/fixtures/`
- Refatoração que cruze mais de 2 módulos

---

## Restrições e limites

| O quê | Regra |
|---|---|
| `tests/fixtures/` | **Nunca modificar.** São a verdade dos testes. |
| `data_dat/` | Gitignorado. Dados reais de pesquisa — não editar, não ler sem necessidade. |
| `test2/` | Gitignorado. Dados de teste local — não editar. |
| `venv/`, `.venv/` | Ambiente virtual — não mexer. |
| `*.egg-info/`, `dist/`, `build/` | Artefatos de build — não modificar. |
| `.coverage`, `.pytest_cache/` | Cache de testes — ignorar. |
| `package-lock.json`, `node_modules/` | Não existem no projeto — não criar. |
| Variáveis de ambiente | Nenhuma obrigatória. Toda configuração é via CLI. |
| Ferramentas externas | Nenhuma obrigatória. Tudo roda com Python puro. |
| Encoding padrão | `utf-8-sig` (com suporte a BOM). `--encoding` permite sobrescrever. |

---

## Glossário

| Termo | Significado |
|---|---|
| `.dat` | Arquivo de dados da pesquisa (separado por vírgula, aspas simples) |
| `.sps` | Sintaxe SPSS do LimeSurvey (contém nomes e rótulos de variáveis) |
| `V1`, `V2`, …, `VN` | Nomes internos das colunas no `.dat` (1-indexed) |
| **VARIABLE LABELS** | Bloco do `.sps` que mapeia `V1` → nome legível (`"id"`) |
| **VALUE LABELS** | Bloco do `.sps` que mapeia códigos (`"AO01"`) → rótulos (`"Portuguesa"`) |
| **apply-labels** | Substituir códigos pelos rótulos no CSV final |
| **clean** | Remover colunas 100% vazias do CSV |
| **fail-soft** | Em caso de erro, avisar em stderr e continuar com fallback (nunca abortar) |
```