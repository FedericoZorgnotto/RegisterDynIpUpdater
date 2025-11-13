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


def get_ip_from_dns(domain: str) -> str: #definisco che la funzione accetterà un parametro di tipo stringa e ritornerà un valore di tipo stringa
    """
    Recupera l'indirizzo IP attualmente associato a un dominio DNS specifico.
     Args:
        domain (str): Il dominio di cui recuperare l'indirizzo IP.
    Returns:
        str: L'indirizzo IP associato al dominio come stringa.
    """
    import socket
    try: # "provo" a eseguire il codice, potrebbero esserci diversi errori che gestisco in questo modo
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        print(f"Impossibile risolvere il dominio: {domain}")
        return None


def main():
    # recupero EMAIL, PASSWORD e DOMINIO da file di configurazione .env
    load_dotenv()
    EMAIL = os.getenv('EMAIL')  # i nomi sono in maiuscolo perché sono costanti
    PASSWORD = os.getenv('PASSWORD')
    DOMAIN = os.getenv('DOMAIN')
    HEADLESS = os.getenv('HEADLESS')  # Opzione per eseguire il browser in modalità headless

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
        # Qui chiamerei la funzione che aggiorna il DNS, passando EMAIL, PASSWORD, DOMAIN e HEADLESS
        # update_dns(EMAIL, PASSWORD, DOMAIN, HEADLESS)
        print("Aggiornamento del DNS completato.")  # Messaggio di conferma fittizio


if __name__ == "__main__":
    main()
