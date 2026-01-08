import os

from dotenv import load_dotenv


def get_public_ip() -> str: #definisco che la funzione ritornerà una variabile di tipo stringa
    """
    Recupera l'indirizzo IP pubblico della macchina effettuando una richiesta a un servizio esterno.
    Returns:
        str: L'indirizzo IP pubblico come stringa.
    """ # si chiama docstring ed è una buona pratica inserirla per spiegare cosa fa la funzione
    import requests
    url = 'http://ifconfig.me'
    response = requests.get(url)
    ip_address = response.text
    return ip_address


def get_ip_from_dns(domain: str) -> str:
    """
    Recupera l'indirizzo IP associato a un dominio utilizzando Google DNS-over-HTTPS.
    Questo evita problemi di caching del resolver locale.
    Args:
        domain (str): Il dominio da risolvere.
    Returns:
        str: L'indirizzo IP o None se non trovato.
    """
    import requests
    try:
        # Interroga Google DNS via HTTPS per evitare la cache locale
        url = "https://dns.google/resolve"
        params = {"name": domain, "type": "A"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Controlla se esiste una risposta
        if 'Answer' in data:
            for answer in data['Answer']:
                if answer['type'] == 1: # Tipo A
                    return answer['data']
        
        print(f"Nessun record A trovato per {domain}")
        return None
        
    except Exception as e:
        print(f"Errore durante la risoluzione DNS (Google DoH): {e}")
        # Fallback su socket locale se internet/Google fallisce
        try:
             import socket
             return socket.gethostbyname(domain)
        except:
             return None


def main():
    # recupero EMAIL, PASSWORD e DOMINIO da file di configurazione .env
    load_dotenv()
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    DOMAIN = os.getenv('DOMAIN') or os.getenv('DOMINIO')
    HEADLESS = os.getenv('HEADLESS')

    if not all([EMAIL, PASSWORD, DOMAIN]):
        print("Errore: Variabili d'ambiente mancanti. Controlla il tuo file .env.")
        print("Assicurati di aver impostato EMAIL, PASSWORD e DOMAIN (o DOMINIO).")
        return

    public_ip = get_public_ip()  # Recupero l'indirizzo IP pubblico
    print(f"L'indirizzo pubblico attuale è: {public_ip}")
    old_public_ip = get_ip_from_dns(DOMAIN)  # Recupero l'indirizzo IP attualmente associato al DNS
    if old_public_ip is None:
        print(f"Impossibile risolvere il dominio: {DOMAIN}")
        return # Termino l'esecuzione della funzione main se non riesco a risolvere il dominio
    print(f"L'indirizzo IP attualmente associato a {DOMAIN} è: {old_public_ip}")
    if public_ip == old_public_ip:
        print("L'indirizzo IP non è cambiato. Nessun aggiornamento necessario.")
    else:
        print("L'indirizzo IP è cambiato. Procedo con l'aggiornamento del DNS.")
        from register_automation_playwright import update_dns
        
        # Convert HEADLESS to boolean
        headless_bool = HEADLESS is not None and HEADLESS.lower() in ('true', '1', 'yes')
        
        update_dns(EMAIL, PASSWORD, DOMAIN, headless=headless_bool)
        print("Tentativo di aggiornamento completato.")


if __name__ == "__main__":
    main()
