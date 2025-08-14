import re
import pandas as pd
import sys # Importa o módulo sys para ler argumentos da linha de comando

def extrair_contatos(texto):
    """
    Extrai contatos de um texto que pode conter múltiplos formatos.
    """
    contatos = []

    # Padrão para a lista tipo 1: ✅ Nome +55... foi adicionado... ✅
    padrao_1 = re.compile(r"✅\s*(.*?)\s*(\+\d+)\s*foi adicionado com sucesso\s*✅")
    matches_1 = padrao_1.findall(texto)
    
    for nome, numero in matches_1:
        nome_limpo = nome.replace('*', '').strip()
        contatos.append({'Número': numero, 'Nome': nome_limpo})

    # Padrão para a lista tipo 2: Name: ... Number (1): ...
    padrao_2 = re.compile(r"Name:\s*(.*?)\s*Number \(1\):\s*(.*)")
    matches_2 = padrao_2.findall(texto)
    
    for nome, numero_bruto in matches_2:
        numero_limpo = '+' + ''.join(filter(str.isdigit, numero_bruto))
        contatos.append({'Número': numero_limpo, 'Nome': nome.strip()})
        
    return contatos

def processar_e_salvar(texto_completo):
    """
    Processa o texto completo para extrair contatos e salvar em Excel.
    """
    if not texto_completo.strip():
        print("Nenhum texto para processar.")
        return

    contatos_extraidos = extrair_contatos(texto_completo)

    if not contatos_extraidos:
        print("Nenhum contato válido foi encontrado nos formatos esperados.")
        return

    df = pd.DataFrame(contatos_extraidos)
    df.drop_duplicates(subset=['Número'], keep='first', inplace=True)
    df = df[['Número', 'Nome']]
    nome_arquivo = 'contatos.xlsx'

    try:
        df.to_excel(nome_arquivo, index=False)
        print("\n----------------------------------------------------")
        print(f"✅ Sucesso! O arquivo '{nome_arquivo}' foi criado com {len(df)} contatos únicos.")
        print("----------------------------------------------------")
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo: {e}")

def main():
    """
    Função principal que decide se lê de um arquivo ou do input interativo.
    """
    # Verifica se um nome de arquivo foi passado como argumento
    if len(sys.argv) > 1:
        nome_arquivo_input = sys.argv[1]
        try:
            with open(nome_arquivo_input, 'r', encoding='utf-8') as f:
                texto_completo = f.read()
            print(f"Lendo contatos do arquivo: {nome_arquivo_input}")
            processar_e_salvar(texto_completo)
        except FileNotFoundError:
            print(f"Erro: O arquivo '{nome_arquivo_input}' não foi encontrado.")
        except Exception as e:
            print(f"Ocorreu um erro ao ler o arquivo: {e}")
    else:
        # Modo interativo se nenhum arquivo for passado
        print("Nenhum arquivo especificado. Entrando no modo interativo.")
        print("Cole o texto com os contatos abaixo (use clique direito para colar).")
        print("Quando terminar, pressione Enter em uma linha vazia para processar.")
        
        linhas = []
        while True:
            try:
                linha = input()
                if not linha:
                    break
                linhas.append(linha)
            except EOFError:
                break
                
        texto_completo = "\n".join(linhas)
        processar_e_salvar(texto_completo)

if __name__ == "__main__":
    main()