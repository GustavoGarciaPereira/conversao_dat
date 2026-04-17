import csv

def limpar_dat_para_csv(arquivo_entrada, arquivo_saida):
    """
    Converte um arquivo .dat com campos separados por vírgula e aspas simples
    em um CSV limpo, removendo colunas vazias à direita.
    """
    linhas_processadas = []
    max_campos = 0

    # 1. PRIMEIRA PASSADA: Descobrir o número máximo de campos úteis
    with open(arquivo_entrada, 'r', encoding='utf-8-sig') as f:
        for linha_bruta in f:
            # Remove quebras de linha
            linha_bruta = linha_bruta.strip()
            if not linha_bruta:
                continue

            # Usa o leitor CSV do Python que entende aspas simples como delimitador de texto
            # Configuramos quotechar="'" para tratar 'pt' e 'AO01' corretamente
            leitor = csv.reader([linha_bruta], quotechar="'", skipinitialspace=True)
            try:
                campos = next(leitor)
            except StopIteration:
                continue

            # Remove campos vazios do final da lista
            while campos and campos[-1] == '':
                campos.pop()

            if campos:
                linhas_processadas.append(campos)
                if len(campos) > max_campos:
                    max_campos = len(campos)

    # 2. ESCREVER O ARQUIVO CSV FINAL
    with open(arquivo_saida, 'w', encoding='utf-8', newline='') as f_out:
        escritor = csv.writer(f_out)
        
        # Escreve cada linha com o número máximo de colunas (preenche com vazio se necessário)
        for linha in linhas_processadas:
            # Garante que todas as linhas tenham o mesmo número de colunas
            linha_completa = linha + [''] * (max_campos - len(linha))
            escritor.writerow(linha_completa)

    print(f"✅ Arquivo convertido com sucesso!")
    print(f"📁 Entrada: {arquivo_entrada}")
    print(f"📁 Saída:  {arquivo_saida}")
    print(f"📊 Total de {len(linhas_processadas)} linhas processadas.")
    print(f"📐 Número de colunas no CSV final: {max_campos}")

# === EXECUÇÃO ===
if __name__ == "__main__":
    # Altere os nomes dos arquivos conforme necessário
    arquivo_dat = "./data_dat/survey_512758_SPSS_data_file.dat"      # Substitua pelo nome do seu arquivo
    arquivo_csv = "sniffy_limpo.csv"
    
    limpar_dat_para_csv(arquivo_dat, arquivo_csv)