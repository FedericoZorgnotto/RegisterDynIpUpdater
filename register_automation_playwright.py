
import time
import random
from playwright.sync_api import sync_playwright

class RegisterDNSUpdater:
    
    def __init__(self, email, password, domain="example.com", headless=False):
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
            
            # DEBUG: Screenshot iniziale
            self._safe_screenshot("debug_entry.png")
            print(f"Titolo pagina: {page.title()}")
            
            # Banner Cookie
            print("Gestione Banner Cookie (Metodo JS robusto)...")
            try:
                # Elenco possibili selettori
                cookie_selectors = [
                    "button.iubenda-cs-accept-btn",
                    "button.iubenda-cs-btn-primary",
                    "text=Accetta",
                    "text=Accept"
                ]
                
                banner_dismissed = False
                
                for selector in cookie_selectors:
                    if page.is_visible(selector):
                        print(f"Banner rilevato: '{selector}'. Tentativo click JS...")
                        try:
                            # Usa il locator di Playwright per risolvere il selettore (supporta text=...)
                            # Poi usa evaluate per cliccare via JS sull'elemento trovato
                            page.locator(selector).first.evaluate("node => node.click()")
                            time.sleep(2.5)
                            
                            # Verifica se il testo del banner è sparito
                            if not page.is_visible("text=Questo sito utilizza cookies"):
                                print("Banner sparito con successo.")
                                banner_dismissed = True
                                break
                            else:
                                print(f"Banner ancora visibile dopo click su {selector}.")
                        except Exception as e:
                            print(f"Errore click JS su {selector}: {e}")

                if not banner_dismissed:
                    print("ATTENZIONE: Banner cookie potrebbe essere ancora presente.")

            except Exception as e:
                print(f"Errore gestione cookie: {e}")

            # Modulo di Login
            print("Inserimento credenziali...")
            print("Inserimento username...")
            page.fill("input.userName", self.email)
            time.sleep(random.uniform(0.5, 1.0))
            
            print("Inserimento password...")
            page.fill("input.password", self.password)
            time.sleep(random.uniform(0.5, 1.0))

            print("Invio modulo di login...")
            try:
                with page.expect_navigation(timeout=40000, wait_until="domcontentloaded"):
                    page.keyboard.press("Enter")
            except Exception as nav_e:
                print(f"Timeout navigazione login ({nav_e}). Provo click su bottone...")
                try:
                    page.evaluate("document.querySelector('button[type=\"submit\"]').click()")
                except:
                    pass

            # Verifica Login
            print("Verifica stato login...")
            self._safe_screenshot("debug_after_login.png")

            # Controllo Elementi Dashboard
            if page.is_visible("text=Esci") or page.is_visible(".user-info") or page.is_visible("#main-menu"):
                print("Login effettuato con successo! (Elementi dashboard rilevati)")
                return True
            
            # Controllo Form Login (fallimento sicuro)
            if page.is_visible("input[name='userName']"):
                 print("Login fallito: Form di login ancora visibile.")
                 return False

            # Check URL (fallback)
            current_url = page.url
            if "welcome.html" in current_url:
                print("Login fallito: Ancora su welcome.html")
                return False
                
            print(f"Login apparentemente riuscito (URL: {current_url}).")
            return True

        except Exception as e:
            print(f"Errore critico durante il login: {e}")
            return False

    def update_ip(self, new_ip):
        if not self.page:
            print("Sessione non avviata (o persa). Effettuo login...")
            if not self.login():
                return False
        
        page = self.page
        try:
            # Gestione potenziale popup 2FA
            print("Attendo 3s per popup 2FA/Promo...")
            time.sleep(3)
            self._safe_screenshot("debug_before_popup.png")
            
            print("Controllo e chiusura popup...")
            popup_selectors = [
                "text=Non ora",
                "button:has-text('Non ora')",
                "button.close",
                "div[aria-label='Close']"
            ]
            
            for sel in popup_selectors:
                if page.is_visible(sel):
                    print(f"Popup rilevato ({sel}). Chiudo via JS...")
                    try:
                        page.locator(sel).first.evaluate("node => node.click()")
                        time.sleep(2)
                        if not page.is_visible(sel):
                            print("Popup chiuso.")
                            break
                    except Exception as e:
                         print(f"Errore chiusura popup JS ({sel}): {e}")
            
            self._safe_screenshot("debug_after_popup.png")

            print(f"Selezione dominio '{self.domain}'...")
            try:
                # Navigazione Dominio
                with page.expect_navigation(timeout=10000):
                    # Prova JS click su link dominio per robustezza
                    found = page.evaluate(f"""() => {{
                        let el = document.querySelector("a[href*='domain={self.domain}']");
                        if(el) {{ el.click(); return true; }}
                        return false;
                    }}""")
                    if not found:
                         # Fallback testo
                         page.click(f"text={self.domain}")
                print("Dominio selezionato.")
            except Exception as e:
                 print(f"Errore selezione dominio: {e}")
                 # Fallback estremo: navigazione diretta? Rischioso per sessione.
                 return False

            print("Navigazione DNS Avanzata...")
            page.goto('https://controlpanel.register.it/domains/dnsAdvanced.html')
            page.wait_for_selector("textarea.recordValue", timeout=10000)
            
            rows = page.query_selector_all("tr")
            updated_count = 0
            
            print(f"Analisi {len(rows)} righe DNS...")
            for row in rows:
                name_input = row.query_selector("input.recordName")
                type_input = row.query_selector("select.recordType")
                value_input = row.query_selector("textarea.recordValue")
                
                if name_input and value_input and type_input:
                    name_val = name_input.input_value().strip()
                    record_type = type_input.input_value().strip()
                    current_val = value_input.input_value().strip()
                    
                    clean_name = name_val[:-1] if name_val.endswith('.') else name_val
                    targets = [self.domain, f"mail.{self.domain}"]
                    
                    if record_type == 'A' and clean_name in targets:
                        if current_val != new_ip:
                            print(f"AGGIORNO {name_val}: {current_val} -> {new_ip}")
                            value_input.fill(new_ip)
                            updated_count += 1
                        else:
                            print(f"Record {name_val} già aggiornato.")

            if updated_count > 0:
                print(f"Applico {updated_count} modifiche...")
                page.click("text=Applica")
                
                print("Conferma salvataggio...")
                try:
                    with page.expect_navigation(timeout=20000):
                        page.click("text=CONTINUA", timeout=5000)
                    print("Salvataggio confermato.")
                except Exception as e:
                    print(f"Errore conferma: {e}")
                return True
            else:
                print("Nessuna modifica necessaria.")
                return True

        except Exception as e:
            print(f"Errore processo update DNS: {e}")
            return False

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _safe_screenshot(self, filename):
        """Tenta di salvare uno screenshot senza bloccare lo script in caso di hang."""
        try:
            print(f"Salvataggio {filename}...")
            # Timeout implicito non esiste in sync API python per screenshot, 
            # ma speriamo che wrapping in try aiuti se è un errore gestibile.
            self.page.screenshot(path=filename) 
        except Exception as e:
            print(f"Screenshot fallito (ignorato): {e}")

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
