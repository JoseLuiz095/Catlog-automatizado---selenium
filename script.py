# salva como add_scan_paths_syncthru.py
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

INPUT_FILE = "caminho das impressoras do adm.txt"
PRINTER_WEBUI = "http://10.5.7.53/sws/index.html"  # IP detectado no seu arquivo. Ajuste se necessário.

def parse_input_file(path):
    """Extrai blocos simples do arquivo. Retorna lista de dicionários com tipo e campos."""
    with open(path, encoding='utf-8') as f:
        text = f.read()

    # Normaliza newlines
    blocks = re.split(r'\n\s*\n', text.strip())
    entries = []
    for b in blocks:
        lines = [ln.strip() for ln in b.splitlines() if ln.strip()]
        # se bloco pequeno pulamos
        if len(lines) < 2:
            continue
        # detecta IP do dispositivo (primeiro bloco possivelmente)
        if lines[0].startswith("ip:") or re.match(r'^\d+\.\d+\.\d+\.\d+$', lines[0]):
            # por enquanto guardamos a ip principal separadamente
            entries.append({"type": "meta", "lines": lines})
            continue

        # detecta se é FTP por palavra
        entry = {"type": None, "fields": {}}
        if any("Ftp" in l or "FTP" in l for l in lines):
            entry["type"] = "ftp"
        else:
            entry["type"] = "smb_or_ftp"

        # busca host, porta, user e pass e mapeamentos
        for l in lines:
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', l):
                entry["fields"]["host"] = l
            elif re.match(r'^\d{2,5}$', l):
                entry["fields"]["port"] = l
            elif ":" in l and "\\" in l:
                # exemplo: Gabriella:PASHELL_DIRETORIA\Direcao\scanner
                name, path = l.split(":", 1)
                if "mappings" not in entry["fields"]:
                    entry["fields"]["mappings"] = []
                entry["fields"]["mappings"].append({"name": name.strip(), "path": path.strip()})
            elif re.match(r'^[A-Za-z0-9\._-]+$', l) and "scanner" in l.lower() is False:
                # pode ser username do host (heurística)
                if "user" not in entry["fields"]:
                    entry["fields"]["user"] = l
                else:
                    # se já tiver, talvez seja outra info
                    pass
            elif re.match(r'^[A-Za-z0-9\*_!@#\$%\^&\(\)\-]+$', l):
                # heurística para senha curta
                if "password" not in entry["fields"]:
                    entry["fields"]["password"] = l
        entries.append(entry)
    return entries

def find_and_click_by_text(driver, tag, text):
    """Procura um elemento <tag> contendo o texto e clica."""
    try:
        el = driver.find_element(By.XPATH, f"//{tag}[contains(text(), '{text}')]")
        el.click()
        return True
    except Exception:
        return False

def safe_find(driver, xpath):
    try:
        return driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return None

def add_entry_via_ui(driver, mapping, common_fields):
    """
    Tenta abrir modal de 'Adicionar' e preencher o cadastro de destino
    mapping: {"name": "...", "path": "..."}
    common_fields: host, port, user, password
    """
    name = mapping["name"]
    path = mapping["path"]
    host = common_fields.get("host")
    port = common_fields.get("port", "")
    user = common_fields.get("user", "")
    password = common_fields.get("password", "")

    # Tenta clicar em botão "Adicionar" (pt-br)
    if not find_and_click_by_text(driver, "button", "Adicionar"):
        # tenta por input/button com value
        try:
            btns = driver.find_elements(By.XPATH, "//input[@value='Adicionar' or @value='Add']")
            if btns:
                btns[0].click()
            else:
                print("Botão 'Adicionar' não encontrado automaticamente. Interrompendo essa entrada.")
                return False
        except Exception as e:
            print("Erro ao tentar clicar em 'Adicionar':", e)
            return False

    time.sleep(1.2)  # aguarda modal abrir

    # Preenche Nome
    # procura label "Nome" e seu input
    el = safe_find(driver, "//label[contains(normalize-space(.),'Nome')]/following::input[1]")
    if el:
        el.clear()
        el.send_keys(name)
    else:
        # fallback: procura input com maxlength ou name 'name'
        el2 = safe_find(driver, "//input[@name='name' or contains(@id,'name')]")
        if el2:
            el2.clear()
            el2.send_keys(name)

    # Marca adicionar SMB/FTP conforme disponível:
    # Primeiro tentamos marcar "Adicionar SMB" checkbox (texto)
    chk = safe_find(driver, "//label[contains(., 'Adicionar SMB')]/preceding::input[1]")
    if chk and chk.get_attribute("type") == "checkbox":
        try:
            if not chk.is_selected():
                chk.click()
        except Exception:
            pass

    # Preenche endereço de servidor SMB / FTP
    server_input = safe_find(driver, "//label[contains(., 'Endereço de servidor SMB')]/following::input[1]")
    if not server_input:
        server_input = safe_find(driver, "//label[contains(., 'Endereço') and contains(.,'servidor')]/following::input[1]")
    if server_input:
        server_input.clear()
        server_input.send_keys(host or "")

    port_input = safe_find(driver, "//label[contains(., 'Porta do servidor SMB')]/following::input[1]")
    if port_input:
        port_input.clear()
        port_input.send_keys(port or "")

    # ID de logon / nome de usuário
    id_input = safe_find(driver, "//label[contains(., 'ID de logon') or contains(., 'Nome de usuário')]/following::input[1]")
    if id_input:
        id_input.clear()
        id_input.send_keys(user or "")

    # Senha
    pw_input = safe_find(driver, "//label[contains(., 'Senha')]/following::input[1]")
    if pw_input:
        pw_input.clear()
        pw_input.send_keys(password or "")

    # Campo de pasta/remote path: tenta localizar 'Endereço' ou 'Pasta' ou 'Diretório'
    remote_input = safe_find(driver, "//label[contains(translate(., 'P', 'p'), 'pasta') or contains(., 'Diretório') or contains(., 'Endereço')]/following::input[1]")
    if remote_input:
        remote_input.clear()
        remote_input.send_keys(path)

    # Aplica / salvar
    # tenta botão Aplicar ou Save
    if not find_and_click_by_text(driver, "button", "Aplicar"):
        try:
            btns = driver.find_elements(By.XPATH, "//input[@value='Aplicar' or @value='Save' or @value='OK']")
            if btns:
                btns[0].click()
            else:
                print("Botão 'Aplicar' não encontrado; tente checar o modal manualmente.")
                return False
        except Exception as e:
            print("Erro ao tentar salvar:", e)
            return False

    time.sleep(1.0)
    print(f"Entrada '{name}' enviada para o dispositivo (host={host})")
    return True

def main():
    entries = parse_input_file(INPUT_FILE)
    # extrai meta ip se presente
    printer_ip = PRINTER_WEBUI
    for e in entries:
        if e.get("type") == "meta":
            # procura ip: linha
            for ln in e["lines"]:
                if ln.lower().startswith("ip:"):
                    ip = ln.split(":",1)[1].strip()
                    printer_ip = f"http://{ip}/sws/index.html"
                    print("Usando IP do arquivo:", printer_ip)

    # Simplificação: pega blocos que têm mappings
    jobs = []
    for e in entries:
        if e.get("type") in ("ftp", "smb_or_ftp"):
            f = e.get("fields", {})
            if "mappings" in f:
                for m in f["mappings"]:
                    jobs.append((f, m))

    if not jobs:
        print("Nenhuma entrada válida encontrada no arquivo.")
        return

    # Inicializa navegador
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless=new")  # retire o comentário se quiser headless
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(printer_ip)
    time.sleep(2)

    # Se a UI pedir login, aqui você pode inserir o username/password:
    # Exemplo (ajuste seletores conforme a tela):
    try:
        user_field = driver.find_element(By.ID, "username")
        pw_field = driver.find_element(By.ID, "password")
        # se você tiver credenciais admin para o SyncThru, coloque aqui:
        # user_field.send_keys("admin")
        # pw_field.send_keys("password")
        # driver.find_element(By.XPATH, "//button[contains(., 'Login')]").click()
        # time.sleep(1.5)
        print("Campos de login detectados. Se necessário, o script pode preencher credenciais (ajuste manualmente).")
    except Exception:
        pass

    # abre a página de catálogo/endereços se houver link texto
    # tenta encontrar 'Catalogo de enderecos' link pelo texto
    try:
        link = driver.find_element(By.XPATH, "//a[contains(., 'Catalog') or contains(., 'Catalogo') or contains(., 'Catalogo de endere') or contains(., 'Catalogo de endereços')]")
        try:
            link.click()
            time.sleep(1.0)
        except Exception:
            pass
    except Exception:
        pass

    # Processa jobs
    for common_fields, mapping in jobs:
        try:
            add_entry_via_ui(driver, mapping, common_fields)
            # dar um tempo entre inclusões
            time.sleep(1.0)
        except Exception as ex:
            print("Erro ao processar", mapping, ex)

    print("Finalizado. Feche o navegador manualmente ou o script irá encerrar.")
    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    main()
