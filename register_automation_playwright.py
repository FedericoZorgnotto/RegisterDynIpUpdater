
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
        self.browser = self.playwright.firefox.launch(
            headless=self.headless,
            args=["--no-sandbox"]
        )
        
        # Crea un contesto con User-Agent realistico per evitare blocchi anti-bot
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            extra_http_headers={
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.register.it/"
            }
        )
        
        # Rimuove il flag webdriver per mitigare i controlli anti-bot in headless
        self.context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
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
            # self._safe_screenshot("debug_entry.png") # Rimosso per ottimizzazione
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
            print("Inserimento credenziali (simulazione umana)...")
            
            # Movimento casuale del mouse iniziale
            page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            time.sleep(random.uniform(0.3, 0.7))
            
            print("Inserimento username...")
            page.click("input.userName")
            time.sleep(random.uniform(0.1, 0.4))
            page.locator("input.userName").press_sequentially(self.email, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.5, 1.0))
            
            # Altro movimento mouse
            page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            
            print("Inserimento password...")
            page.click("input.password")
            time.sleep(random.uniform(0.1, 0.4))
            page.locator("input.password").press_sequentially(self.password, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.5, 1.0))

            print("Invio modulo di login...")
            try:
                # Usa un click esplicito invece del tasto Invio per evitare problemi JS/bot detection
                button = page.locator("button[type='submit']").first
                
                # Simulazione movimento mouse verso il bottone
                try:
                    box = button.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=10)
                        time.sleep(random.uniform(0.2, 0.5))
                except Exception:
                    pass
                
                try:
                    button.click(timeout=5000)
                except Exception:
                    # Alternativa se il bottone non è cliccabile
                    page.evaluate("document.querySelector('button[type=\"submit\"]').click()")
                
                # Attende che la navigazione si completi dopo il submit
                page.wait_for_load_state("domcontentloaded", timeout=40000)
                # Piccola pausa per dare modo alle animazioni/redirect JS finali di concludersi
                time.sleep(3)
            except Exception as nav_e:
                print(f"Errore navigazione login o caricamento lento ({nav_e}). Procedo ai check manuali...")

            # Verifica Login
            print("Verifica stato login...")
            # Screenshot rimosso dal main path per evitare hang su dashboard pesanti

            # Controllo Elementi Dashboard
            if page.is_visible("text=Esci") or page.is_visible(".user-info") or page.is_visible("#main-menu"):
                print("Login effettuato con successo! (Elementi dashboard rilevati)")
                return True
            
            # Controllo Form Login (fallimento sicuro)
            if page.is_visible("input[name='userName']"):
                 print("Login fallito: Form di login ancora visibile.")
                 self._safe_screenshot("debug_login_fail_form.png")
                 return False

            # Check URL (fallback)
            current_url = page.url
            if "welcome.html" in current_url:
                print("Login fallito: Ancora su welcome.html")
                self._safe_screenshot("debug_login_fail_welcome.png")
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
            # self._safe_screenshot("debug_before_popup.png")
            
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
            
            # self._safe_screenshot("debug_after_popup.png")

            # Salto la navigazione al dominio cliccando sul testo perché timeout, 
            # vado direttamente alla pagina dei DNS avanzati passando il dominio come parametro se possibile,
            # oppure semplicemente navigando all'URL e sperando che il dominio sia pre-selezionato 
            # (se ce n'è solo uno nel pannello di solito register.it lo pre-seleziona)
            
            print("Navigazione diretta DNS Avanzata per bypassare selezione GUI...")
            page.goto(f'https://controlpanel.register.it/domains/dnsAdvanced.html?domain={self.domain}')
            page.wait_for_selector("textarea.recordValue", timeout=15000)
            
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
