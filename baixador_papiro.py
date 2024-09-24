# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import sys
import csv
import codecs
import os

# FunÃ§Ã£o para realizar o login
def login(driver, usuario, password):
    driver.get("http://192.168.0.10/papiro/pages/login.xhtml")
    driver.find_element(By.ID, "itLogin").send_keys(usuario)
    driver.find_element(By.ID, "itSenha").send_keys(password)
    driver.find_element(By.XPATH, "//button[@id='buttonLogin']").click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#toolBarFrm\\3Aj_idt17_button > .ui-button-text")))

# FunÃ§Ã£o para pesquisar um ID
def buscar_id(driver, idt_buscada):
    xpath_expression = "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{}')]".format(idt_buscada.lower())
    
    driver.find_element(By.CSS_SELECTOR, "#toolBarFrm\\3Aj_idt17_button > .ui-button-text").click()
    driver.find_element(By.XPATH, "//a[span[text()='Pesquisar']]").click()
    driver.find_element(By.ID, "formularioDeConsulta:numero").send_keys(idt_buscada)
    button = driver.find_element(By.CSS_SELECTOR, "#formularioDeConsulta\\3A Consultar > .ui-button-text")
    driver.execute_script("arguments[0].click();", button)

    try:
        elemento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_expression))
        )
        elemento.click()
    except Exception as e:
        print("Elemento nÃ£o encontrado: {}. Erro: {}".format(idt_buscada, e))

# FunÃ§Ã£o para baixar o arquivo
def baixar_arquivo(driver, download_url, idt_buscada, nome):
    cookies = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

    response = requests.get(download_url, cookies=cookies_dict)

    if response.status_code == 200:
        # Salva o arquivo no formato idt-nome.pdf
        filename = "{}-{}.pdf".format(idt_buscada, nome)
        with open(filename, "wb") as f:
            f.write(response.content)
        print("Arquivo baixado com sucesso: {}".format(filename))
    else:
        print("Falha ao baixar o arquivo. Status code:", response.status_code)

# FunÃ§Ã£o principal para executar o fluxo
def iniciar_driver():
    driver = webdriver.Firefox()
    # driver = webdriver.Firefox(executable_path='/home/jean/workspace/papiro_dcipas/geckodriver')
    driver.set_window_size(550, 691)
    return driver

def realizar_login(driver, usuario, password):
    # Função de login genérica
    login(driver, usuario, password)

def buscar_documento(driver, idt_buscada):
    buscar_id(driver, idt_buscada)

def listar_unidades(driver):
    # Passo 6: Listar Unidades de Arquivamento
    driver.find_element(By.CSS_SELECTOR, "#formularioDeListagem\\3Aj_idt63 > .ui-button-text").click()

def selecionar_licenca_especial(driver, idt_buscada):
    # Passo 7: Clicar em 'LICENÇA ESPECIAL'
    time.sleep(1)
    try:
        driver.find_element(By.XPATH, "//td[text()='LICENÇA ESPECIAL']").click()
        driver.find_element(By.XPATH, "//span[text()='Listar Documentos']").click()
    except Exception as e:
        print("LICENÇA ESPECIAL não localizada.", idt_buscada)
        return False
    return True

def rolar_para_baixo(driver):
    # Passo 8: Rolar para baixo
    time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def visualizar_documento(driver):
    # Passo 9: Clicar para visualizar o documento
    time.sleep(1)
    button = driver.find_element(By.ID, "formularioDeListagem:tabela:0:j_idt151")
    driver.execute_script("arguments[0].click();", button)

    # Aguarda até que a nova janela esteja aberta
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)

def mudar_para_nova_janela(driver):
    # Muda para a nova janela
    original_window = driver.current_window_handle
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break

def baixar_documentos(driver, idt_nome_tuplas):
    original_window = driver.current_window_handle
    for idt_buscada, nome in idt_nome_tuplas:
        buscar_documento(driver, idt_buscada)
        listar_unidades(driver)
        
        if not selecionar_licenca_especial(driver, idt_buscada):
            driver.switch_to.window(original_window)
            continue

        rolar_para_baixo(driver)
        visualizar_documento(driver)
        mudar_para_nova_janela(driver)

        download_url = "http://10.166.67.30/papiro/javax.faces.resource/dynamiccontent.properties.xhtml?ln=primefaces&pfdrid=sh1wqWH16DYvfAvc9CkA%2FMUTmRat1wJ%2BpMbWed7WKU0%3D&pfdrt=sc&pfdrid_c=false&uid=1b860ffc-f936-4e4f-a480-ee10fe6c8ccf"
        baixar_arquivo(driver, download_url, idt_buscada, nome)

        driver.close()
        driver.switch_to.window(original_window)

def baixar(usuario, password, idt_nome_tuplas):
    driver = iniciar_driver()
    realizar_login(driver, usuario, password)
    baixar_documentos(driver, idt_nome_tuplas)
    driver.quit()

def ler_csv_para_tuplas(caminho_csv):
    with open(caminho_csv, 'rb') as csvfile:  # Abrir em modo binário
        leitor = csv.reader(csvfile, delimiter=',')
        lista_tuplas = [tuple(linha) for linha in leitor]
    return lista_tuplas

def listar_pdfs_e_verificar_ids(pasta, lista_tuplas):
    # Extrair as IDs dos arquivos PDF
    arquivos_pdf = [f for f in os.listdir(pasta) if f.endswith('.pdf')]
    ids_baixadas = {arquivo.split('-')[0] for arquivo in arquivos_pdf}

    # Verificar IDs baixadas
    ids_csv = {linha[0] for linha in lista_tuplas}  # Supondo que a ID está na primeira posição da tupla
    ids_nao_baixadas = ids_csv - ids_baixadas

    # Exibir e salvar IDs que não foram baixadas
    if ids_nao_baixadas:
        print("As seguintes IDs não foram baixadas:")
        with open('nao_baixadas.txt', 'w') as f:
            for id_nao_baixada in ids_nao_baixadas:
                print(id_nao_baixada)
                f.write(id_nao_baixada + '\n')
        print("IDs não baixadas foram salvas em nao_baixadas.txt.")
    else:
        print("Todas as IDs foram baixadas.")


def main():
    usuario = "dcm"
    password = "Dp1"
    pasta_pdf = os.getcwd() 

    if len(sys.argv) != 2:
        print("""
        Uso: python meu_codigo.py arquivo.csv

        Resumo do Uso:
        Este script automatiza o download de documentos PDF de um sistema web utilizando a biblioteca Selenium.
        O fluxo de operação inclui:
        - Realizar login no sistema
        - Buscar documentos por ID
        - Baixar arquivos PDF correspondentes

        Após o download, o script verifica quais IDs do CSV foram baixadas e informa se houve IDs que não foram baixadas.

        Formato do CSV:
        O arquivo CSV deve seguir o seguinte formato:
        - Cada linha deve conter uma ID e um nome, separados por vírgula.
        - O arquivo deve estar codificado em UTF-8.

        Exemplo de conteúdo do arquivo CSV:
        194000034,MARLOS SOBRENOME SILVA
        367000035,AUGUSTO SOBRENOME DA COSTA
        194000033,WELLINGTON SOBRENOME DOS SANTOS

        Mini Manual de Uso:
        Para executar o script, passe o caminho do arquivo CSV como argumento:
        python meu_codigo.py caminho/para/seu/arquivo.csv

        Condições para Uso:
        - Instalação do Selenium: certifique-se de que a biblioteca Selenium está instalada.
        - Driver do Navegador: tenha o driver do navegador (ex: geckodriver) instalado e disponível.
        - Acesso ao Sistema: tenha acesso à URL do sistema e forneça credenciais corretas.
        """)
        sys.exit(1)

    caminho_csv = sys.argv[1]
    lista_tuplas = ler_csv_para_tuplas(caminho_csv)
    baixar(usuario, password, lista_tuplas)
    listar_pdfs_e_verificar_ids(pasta_pdf, lista_tuplas)


if __name__ == "__main__":
    main()


