# RegisterDynIpUpdater

Questo tool automatizza l'aggiornamento dei record DNS su [Register.it](https://register.it).  
Agisce come un client DDNS: controlla il tuo IP pubblico attuale (usando Google DNS per evitare cache locali) e, se è cambiato, accede al pannello di controllo ed aggiorna i record A del tuo dominio.



## Requisiti

*   Python 3.8+
*   Un account Register.it
*   Ambiente Linux o Windows

## Installazione

1.  **Clona il repository:**
    ```bash
    git clone https://github.com/FedericoZorgnotto/RegisterDynIpUpdater.git
    cd RegisterDynIpUpdater
    ```

2.  **Crea un Virtual Environment (Raccomandato):**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Installa il browser per Playwright:**
    ```bash
    playwright install firefox
    ```

## Configurazione

Crea un file `.env` nella cartella principale (puoi copiare `.env.example`).  
Inserisci le tue credenziali:

```ini
EMAIL="tua_email@esempio.com"
PASSWORD="tua_password"
DOMINIO="tuodominio.it"
HEADLESS=True
```

*   `HEADLESS=True`: Il browser lavora in background (invisibile). Metti `False` se vuoi vedere cosa fa (utile per debug).
*   `DOMINIO`: Il dominio principale (es. `example.com`). Lo script aggiornerà sia il dominio radice che il sottodominio `mail`.

## Utilizzo

Per avviare il controllo manuale (o testare se funziona):

```bash
python main.py
```

Se l'IP è cambiato, vedrai i log del login e dell'aggiornamento. Se è uguale, lo script terminerà subito.

## Automazione

### Linux (Servizio Automatico)

Ho incluso uno script per installare facilmente il tool come servizio di sistema (systemd). Si avvierà al boot e girerà periodicamente.

1.  **Installa il servizio (es. ogni ora):**
    ```bash
    sudo python service_manager.py install --interval 1h
    ```

2.  **Controlla che giri:**
    ```bash
    systemctl status register-ip-updater.timer
    ```

3.  **Disinstalla:**
    ```bash
    sudo python service_manager.py uninstall
    ```

### Windows

Puoi usare l'**Utilità di pianificazione (Task Scheduler)** di Windows:
1.  Crea una nuova attività "Base".
2.  Azione: Avvio programma -> Seleziona `python.exe` (trova il percorso con `where python`).
3.  Argomenti: il percorso completo di `main.py` (es. `C:\Users\Nome\Desktop\RegisterDynIpUpdater\main.py`).
4.  Imposta la pianificazione (es. ogni ora).

---


