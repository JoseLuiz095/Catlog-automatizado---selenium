import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ======== CONFIGURAR APENAS AQUI ========
TXT_FILE = "caminho.txt"
PRINTER_URL = "http://10.5.7.53/sws/index.html"   # endereço da impressora
# =======================================

def load_data(txt):
    with open(txt, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]

    host   = lines[0]   # IP do servidor
    port   = lines[1]   # Porta ex: 445
    user   = lines[2]   # Usuário
    passwd = lines[3]   # Senha
    mappings = []

    for line in lines[4:]:
        if ":" in line:
            name, path = line.split(":", 1)
            mappings.append({"name": name, "path": path})

    return host, port, user, passwd, mappings

def add_destination(driver, name, host, port, user, passwd, remote_path):
    print(f"➡ Adicionando: {name}")

    # abrir janela
    driver.find_element(By.XPATH, "//button[contains(text(),'Adicionar')]").click()
    time.sleep(4)

    # preencher nome
    driver.find_element(By.XPATH, "//label[contains(.,'Nome')]/following::input[1]").send_keys(name)

    # marcar FTP
    ftp_checkbox = driver.find_element(By.XPATH, "//label[contains(.,'Adicionar FTP')]/preceding::input[1]")
    if not ftp_checkbox.is_selected():
        ftp_checkbox.click()

    # preencher servidor
    driver.find_element(By.XPATH, "//label[contains(.,'Endereço de servidor FTP')]/following::input[1]").send_keys(host)

    # preencher porta
    port_input = driver.find_element(By.XPATH, "//label[contains(.,'Porta de servidor FTP')]/following::input[1]")
    port_input.clear()
    port_input.send_keys(port)

    # preencher ID de logon
    driver.find_element(By.XPATH, "//label[contains(.,'ID de logon')]/following::input[1]").send_keys(user)

    # preencher senha
    driver.find_element(By.XPATH, "//label[contains(.,'Senha:')]/following::input[1]").send_keys(passwd)

    # confirmar senha
    driver.find_element(By.XPATH, "//label[contains(.,'Confirmar senha')]/following::input[1]").send_keys(passwd)

    # preencher caminho
    driver.find_element(By.XPATH, "//label[contains(.,'Cami')]/following::input[1]").send_keys(remote_path)

    # aplicar
    driver.find_element(By.XPATH, "//button[contains(text(),'Aplicar')]").click()
    time.sleep(1)


def main():
    host, port, user, passwd, mappings = load_data(TXT_FILE)

    print("✔ Arquivo TXT carregado com sucesso.")
    print(f"Servidor: {host}  Porta: {port}  Usuário: {user}")
    print(f"Total de destinos: {len(mappings)}\n")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(PRINTER_URL)
    time.sleep(2)

    # abre catálogo de endereços
    driver.find_element(By.XPATH, "//a[contains(.,'Catalog')]").click()
    time.sleep(1)

    # clica na opção "Indivíduo"
    driver.find_element(By.XPATH, "//span[contains(.,'Indivíduo') or contains(.,'Individual')]").click()
    time.sleep(1)

    for m in mappings:
        add_destination(driver, m["name"], host, port, user, passwd, m["path"])

    print("\n✅ FINALIZADO com sucesso!")
    input("Pressione ENTER para fechar... ")
    driver.quit()

if __name__ == "__main__":
    main()
