
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
            
            # DEBUG: Screenshot iniziale per vedere cosa vede il browser
            print("Salvataggio screenshot di debug -> debug_entry.png")
            page.screenshot(path="debug_entry.png")
            print(f"Titolo pagina: {page.title()}")
            
            # Banner Cookie
            # Banner Cookie
            print("Gestione Banner Cookie (Tentativo robusto)...")
            try:
                # Elenco possibili selettori per il bottone "Accetta"
                cookie_selectors = [
                    "button.iubenda-cs-accept-btn",  # ID specifico Iubenda
                    "button.iubenda-cs-btn-primary", # Altra classe comune
                    "text=Accetta",                  # Testo italiano
                    "text=Accept",                   # Testo inglese
                    "text=Consent",                  # Testo inglese alt
                ]
                
                banner_dismissed = False
                
                for selector in cookie_selectors:
                    if page.is_visible(selector):
                        print(f"Banner rilevato con selettore: '{selector}'. Clicco (force=True, timeout=3s)...")
                        try:
                            # Timeout ridotto per non bloccare tutto se il selettore è 'fake' o non cliccabile
                            page.click(selector, force=True, timeout=3000)
                            time.sleep(2.5) # Attesa animazione
                            
                            if not page.is_visible("text=Questo sito utilizza cookies"):
                                print("Banner sparito con successo (Testo non più visibile).")
                                banner_dismissed = True
                                break
                            else:
                                print(f"Il banner sembra ancora lì (Testo visibile). Provo il prossimo...")
                        except Exception as click_err:
                            print(f"Errore click su {selector}: {click_err}")
                
                if not banner_dismissed:
                    print("ATTENZIONE: Il banner cookie potrebbe essere ancora attivo.")
                
            except Exception as e:
                print(f"Errore generico gestione cookie: {e}")

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
            try:
                # Usa domcontentloaded invece di load per evitare blocchi su script terzi
                # Aumenta timeout a 40s per ambienti lenti (LXC)
                with page.expect_navigation(timeout=40000, wait_until="domcontentloaded"):
                    page.keyboard.press("Enter")
            except Exception as nav_e:
                print(f"Nota: la navigazione ha impiegato troppo tempo ({nav_e}).")
                print("Provo a cliccare il bottone 'Accedi' esplicitamente come fallback...")
                try:
                    page.click("button[type='submit']")
                except:
                   pass

            # Verifica Login
            current_url = page.url
            print(f"Navigazione completata (o terminata). URL corrente: {current_url}")
            
            # DEBUG: V vediamo dove siamo finiti
            print("Salvataggio screenshot post-login (debug_after_login.png)...")
            page.screenshot(path="debug_after_login.png")
            print("Screenshot salvato.")

            # Se siamo ancora su welcome.html, il login è fallito
            if "welcome.html" in current_url and "controlpanel" not in current_url:
                # Nota: A volte redirige su controlpanel.register.it/ senza welcome
                print("Login fallito: Rimasto sulla pagina di benvenuto.")
                print("Controlla 'debug_after_login.png' per vedere se ci sono errori o captcha.")
                return False
            else:
                print("Login riuscito (URL diverso da welcome.html).")
                return True
                
        except Exception as e:
            print(f"Si è verificato un errore critico durante il login: {e}")
            return False

    def update_ip(self, new_ip):
        if not self.page:
            print("Sessione non avviata. Effettuo login...")
            if not self.login():
                return False
        
        page = self.page
        try:
            # Gestione potenziale popup 2FA/Promo
            print("Attendo 3s per caricamento eventuali popup...")
            time.sleep(3)
            page.screenshot(path="debug_before_popup.png")
            
            print("Controllo eventuali popup (2FA/Promo)...")
            try:
                # Elenco possibili selettori per chiudere il popup
                popup_selectors = [
                    "text=Non ora",                # Testo semplice (spesso funziona)
                    "a:has-text('Non ora')",       # Link esplicito
                    "button:has-text('Non ora')",  # Bottone specifico
                    "div.modal-footer button.btn-secondary", # Bottone secondario footer modal
                    "button.close",                # X in alto a destra standard
                    "div[aria-label='Close']"      # X accessibile
                ]
                
                popup_found = False
                for sel in popup_selectors:
                    if page.is_visible(sel):
                        print(f"Popup rilevato ({sel}). Chiudo (force=True)...")
                        try:
                            page.click(sel, force=True)
                            popup_found = True
                            time.sleep(2) # Attesa chiusura animazione
                            if not page.is_visible(sel):
                                print("Popup chiuso con successo.")
                                break
                            else:
                                print("Popup ancora visibile, provo prossimo selettore...")
                        except:
                            pass
                
                if not popup_found:
                    print("Nessun popup bloccante rilevato al momento del controllo.")
                
                page.screenshot(path="debug_after_popup.png")
                    
            except Exception as e:
                print(f"Errore controllo popup (non bloccante): {e}")

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
