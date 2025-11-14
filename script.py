import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys  # <-- ADICIONADO

# ======== CONFIGURAR APENAS AQUI ========
TXT_FILE = "caminho.txt"
PRINTER_URL = "http://10.5.7.53/sws/index.html"
# =======================================


def create_driver():
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver


# === BOTÃO "Catalog ender" ==========================
def click_catalog(driver):
    print("⏳ Procurando botão 'Catalog ender'...")

    try:
        btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((
                By.XPATH, "//button[contains(text(),'Catalog ender')]"
            ))
        )
        print("✔ Catalog encontrado! Clicando...")
        btn.click()
        time.sleep(2)
        return True

    except Exception as e:
        print("❌ Erro ao localizar botão Catalog ender:", e)
        return False


# === CARREGAR TXT ==================================
def load_data(txt):
    with open(txt, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]

    host = lines[0]
    port = lines[1]
    user = lines[2]
    passwd = lines[3]
    mappings = []

    for line in lines[4:]:
        if ":" in line:
            name, path = line.split(":", 1)
            mappings.append({"name": name, "path": path})

    return host, port, user, passwd, mappings


# === ADICIONAR DESTINO ================================
def add_destination(driver, name, host, port, user, passwd, remote_path):
    print(f"\n➡ Adicionando: {name}")
    time.sleep(2)

    # Botão ADICIONAR (texto fixo)
    add_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Adicionar')]"))
    )
    add_btn.click()
    time.sleep(4)

    # --- CAMPOS --------------------------------------

    # Nome
    driver.find_element(By.ID, "ABOOK_ICMD_INAME").send_keys(name)
    time.sleep(0.8)

    # Checkbox FTP
    ftp_box = driver.find_element(By.ID, "XXI_ABOOK_ICMD_FTP_FIELDSET-checkbox")
    driver.execute_script("arguments[0].click();", ftp_box)
    time.sleep(1)

    # Servidor FTP
    driver.find_element(By.ID, "ABOOK_ICMD_FTP_ADDR").send_keys(host)
    time.sleep(1)

    # Porta
    port_input = driver.find_element(By.ID, "ABOOK_ICMD_FTP_PORT")
    port_input.clear()
    port_input.send_keys(port)
    time.sleep(1)

    # ID (usuário)
    driver.find_element(By.ID, "ABOOK_ICMD_FTP_ID").send_keys(user)
    time.sleep(1)

    # Senha
    driver.find_element(By.ID, "ABOOK_ICMD_FTP_PASS").send_keys(passwd)
    time.sleep(1)

    # Confirmar senha
    driver.find_element(By.ID, "ABOOK_ICMD_FTP_PASS_CONFIRM").send_keys(passwd)
    time.sleep(1)

    # Caminho compartilhado
    caminho = driver.find_element(By.ID, "ABOOK_ICMD_FTP_SHAREDFOLDER")
    caminho.send_keys(remote_path)
    time.sleep(1)

    time.sleep(5)
    # Botão APLICAR
    aplicar_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Aplicar')]"))
    )
    aplicar_btn.click()

    time.sleep(2)


# === PRINCIPAL ==========================================
def main():
    host, port, user, passwd, mappings = load_data(TXT_FILE)

    print("✔ Arquivo TXT carregado.")
    print(f"Servidor FTP: {host}")
    print(f"Porta: {port} | Usuário: {user}")
    print(f"Total de destinos: {len(mappings)}\n")

    driver = create_driver()
    driver.get(PRINTER_URL)

    print("⏳ Esperando carregamento inicial...")
    time.sleep(10)

    # Abre o menu Catalog
    click_catalog(driver)
    time.sleep(2)

    # Abre submenu Individual
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Indiv')]"))
    ).click()
    time.sleep(2)

    # Adicionar todos destinos
    for m in mappings:
        add_destination(driver, m["name"], host, port, user, passwd, m["path"])

    print("\n✅ FINALIZADO!")
    input("Pressione ENTER para fechar...")
    driver.quit()


if __name__ == "__main__":
    main()
