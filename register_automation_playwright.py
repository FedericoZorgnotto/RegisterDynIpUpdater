
import time
import random
from playwright.sync_api import sync_playwright

class RegisterDNSUpdater:
    
    def __init__(self, email, password, domain="zorgnotto.it", headless=False):
        self.email = email
        self.password = password
        self.domain = domain
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_session(self):
        """Inizializza la sessione del browser."""
        self.playwright = sync_playwright().start()
        # Avvia il browser - utilizza FIREFOX
        self.browser = self.playwright.firefox.launch(headless=self.headless)
        
        # Crea un contesto
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        
        self.page = self.context.new_page()

    def login(self):
        if not self.page:
            self.start_session()
            
        page = self.page
        try:
            print("Navigazione alla pagina di login...")
            page.goto('https://controlpanel.register.it/welcome.html')
            
            # Banner Cookie
            try:
                # Attende brevemente il banner dei cookie
                cookie_btn = page.wait_for_selector("button.iubenda-cs-accept-btn", timeout=5000)
                if cookie_btn:
                    print("Banner cookie trovato. Clicco...")
                    cookie_btn.click()
                    time.sleep(1)
            except Exception:
                print("Banner cookie non trovato o timeout.")

            # Modulo di Login
            print("Inserimento credenziali...")
            
            # Username
            print("Inserimento username...")
            page.fill("input.userName", self.email)
            
            time.sleep(random.uniform(0.5, 1.0))
            
            # Password
            print("Inserimento password...")
            page.fill("input.password", self.password)
            
            time.sleep(random.uniform(0.5, 1.0))

            # INVIO: Preme INVIO invece di cliccare il pulsante
            print("Premo INVIO per accedere...")
            with page.expect_navigation(timeout=15000):
                page.keyboard.press("Enter")
            
            # Verifica Login
            current_url = page.url
            print(f"Navigazione completata. URL corrente: {current_url}")
            
            if "welcome.html" not in current_url:
                print("Login effettuato con successo!")
                return True
            else:
                print("Login fallito, sembra essere ancora sulla pagina di benvenuto.")
                return False
                
        except Exception as e:
            print(f"Si è verificato un errore: {e}")
            return False

    def update_ip(self, new_ip):
        if not self.page:
            print("Sessione non avviata. Effettuo login...")
            if not self.login():
                return False
        
        page = self.page
        try:
            # Gestione potenziale popup 2FA/Promo
            try:
                # Controllo breve se appare il popup
                print("Controllo eventuali popup...")
                # Selettore per 'Non ora'
                if page.is_visible("text=Non ora", timeout=3000):
                    print("Chiudo popup 2FA...")
                    page.click("text=Non ora")
                    time.sleep(1)
            except:
                pass

            print(f"Selezione dominio '{self.domain}'...")
            # Clicca sul link del dominio per impostare il contesto
            try:
                # Prova prima il selettore CSS (più robusto)
                with page.expect_navigation(timeout=10000):
                    page.click(f"a[href*='domain={self.domain}']")
                print("Dominio selezionato via HREF.")
            except Exception:
                 print(f"Selettore compatto fallito. Provo con match testuale per '{self.domain}'...")
                 try:
                     with page.expect_navigation(timeout=5000):
                        page.click(f"text={self.domain}")
                     print("Dominio selezionato via TESTO.")
                 except Exception:
                     print("Match testuale fallito. Provo selettore generico sidebar 'a._dom'...")
                     try:
                         with page.expect_navigation(timeout=5000):
                            page.click("a._dom") 
                         print("Dominio selezionato via selettore GENERICO.")
                     except Exception as e_final:
                         print("Tutti i tentativi di selezione dominio sono falliti.")
                         return False

            print("Navigazione alla Gestione DNS Avanzata...")
            page.goto('https://controlpanel.register.it/domains/dnsAdvanced.html')
            
            # Attende caricamento tabella
            page.wait_for_selector("textarea.recordValue", timeout=10000)
            
            # Trova tutte le righe
            rows = page.query_selector_all("tr")
            updated_count = 0
            
            print(f"Scansione di {len(rows)} righe per record DNS...")
            
            for row in rows:
                # Cerca selettori nome, tipo e valore
                name_input = row.query_selector("input.recordName")
                type_input = row.query_selector("select.recordType")
                value_input = row.query_selector("textarea.recordValue")
                
                if name_input and value_input and type_input:
                    name_val = name_input.input_value().strip()
                    record_type = type_input.input_value().strip()
                    current_val = value_input.input_value().strip()
                    
                    # Normalizza nome rimuovendo punto finale se presente
                    clean_name = name_val[:-1] if name_val.endswith('.') else name_val
                    
                    # Target specifici: Dominio radice e sottodominio 'mail'
                    targets = [self.domain, f"mail.{self.domain}"]
                    
                    print(f"Controllo record: Nome='{name_val}' Tipo='{record_type}' Valore='{current_val}'")

                    if record_type == 'A':
                        if clean_name in targets:
                            if current_val != new_ip:
                                print(f"MATCH TROVATO: Aggiorno {name_val} (A) da {current_val} a {new_ip}")
                                value_input.fill(new_ip)
                                updated_count += 1
                            else:
                                print(f"MATCH TROVATO: {name_val} ha già l'IP corretto. Salto.")
                        else:
                            print(f"Salto record A {name_val} (non è nei target).")
                    else:
                        print(f"Salto record non-A {name_val} (Tipo: {record_type}).")

            if updated_count > 0:
                print(f"Aggiornamenti effettuati: {updated_count}. Clicco 'Applica'...")
                # Clicca pulsante Applica.
                page.click("text=Applica")
                
                print("Attendo dialogo di conferma...")
                try:
                    # Attende il modale "Salvataggio modifiche" con pulsante "CONTINUA"
                    with page.expect_navigation(timeout=20000):
                        page.click("text=CONTINUA", timeout=5000)
                    print("Modifiche confermate (Cliccato CONTINUA).")
                except Exception as e:
                    print(f"Problema con dialogo di conferma: {e}")
                
                print("Processo aggiornamento DNS completato.")
                return True
            else:
                print("Nessun record necessitava aggiornamento.")
                return True

        except Exception as e:
            print(f"Errore durante aggiornamento DNS: {e}")
            return False

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

def update_dns(email, password, domain, headless=False):
    # Recupera l'IP pubblico qui per completezza
    import requests
    try:
        new_ip = requests.get('https://api.ipify.org').text
        print(f"IP Pubblico Rilevato: {new_ip}")
    except Exception as e:
        print(f"Impossibile ottenere IP pubblico: {e}")
        return

    updater = RegisterDNSUpdater(email, password, domain, headless)
    try:
        updater.update_ip(new_ip)
    finally:
        updater.close()
