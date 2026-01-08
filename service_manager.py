
import os
import sys
import argparse
import subprocess
import getpass

SERVICE_NAME = "register-ip-updater"
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}.service"
TIMER_FILE = f"/etc/systemd/system/{SERVICE_NAME}.timer"

def is_root():
    return os.geteuid() == 0

def get_paths():
    """Returns the absolute paths for the current directory, python executable and main script."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "main.py")
    
    # Check for virtual environment
    venv_python = os.path.join(current_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        python_path = venv_python
    else:
        # Fallback to current executable if no venv found
        python_path = sys.executable
        
    return current_dir, python_path, script_path

def create_service_file(current_dir, python_path, script_path, user):
    content = f"""[Unit]
Description=Register.it Dynamic IP Updater Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User={user}
WorkingDirectory={current_dir}
ExecStart={python_path} {script_path}
# Environment variables are loaded from .env in WorkingDirectory by the script itself
# If needed, you can add specific Environment= variables here

[Install]
WantedBy=multi-user.target
"""
    return content

def create_timer_file(interval):
    content = f"""[Unit]
Description=Run Register.it Updater every {interval}

[Timer]
OnBootSec=5min
OnUnitActiveSec={interval}
Unit={SERVICE_NAME}.service

[Install]
WantedBy=timers.target
"""
    return content

def install_service(interval):
    if not is_root():
        print("Errore: L'installazione richiede privilegi di root (sudo).")
        sys.exit(1)

    print(f"Installazione servizio '{SERVICE_NAME}'...")
    
    # Get details
    current_dir, python_path, script_path = get_paths()
    # We want to run as the user who invoked sudo, not root (unless using root)
    target_user = os.environ.get('SUDO_USER', getpass.getuser())
    
    print(f"Directory di lavoro: {current_dir}")
    print(f"Eseguibile Python: {python_path}")
    print(f"Utente esecuzione: {target_user}")
    print(f"Intervallo: {interval}")

    # Write Service File
    with open(SERVICE_FILE, "w") as f:
        f.write(create_service_file(current_dir, python_path, script_path, target_user))
    print(f"Creato: {SERVICE_FILE}")

    # Write Timer File
    with open(TIMER_FILE, "w") as f:
        f.write(create_timer_file(interval))
    print(f"Creato: {TIMER_FILE}")

    # Reload and Enable
    try:
        print("Ricaricamento daemon systemd...")
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        
        print("Abilitazione e avvio timer...")
        subprocess.run(["systemctl", "enable", f"{SERVICE_NAME}.timer"], check=True)
        subprocess.run(["systemctl", "start", f"{SERVICE_NAME}.timer"], check=True)
        
        # Don't start the service immediately, let the timer do it (or triggered by boot)
        # But we can verify status
        print("Installazione completata con successo! \u2705")
        print(f"Il servizio partirà tra 5 minuti e poi ogni {interval}.")
        print(f"Controlla stato con: systemctl status {SERVICE_NAME}.timer")
        
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la configurazione systemd: {e}")

def uninstall_service():
    if not is_root():
        print("Errore: La disinstallazione richiede privilegi di root (sudo).")
        sys.exit(1)

    print(f"Disinstallazione servizio '{SERVICE_NAME}'...")

    try:
        # Stop and Disable
        subprocess.run(["systemctl", "stop", f"{SERVICE_NAME}.timer"], stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "disable", f"{SERVICE_NAME}.timer"], stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "stop", f"{SERVICE_NAME}.service"], stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "disable", f"{SERVICE_NAME}.service"], stderr=subprocess.DEVNULL)
        
        # Remove Files
        if os.path.exists(TIMER_FILE):
            os.remove(TIMER_FILE)
            print(f"Rimosso: {TIMER_FILE}")
        
        if os.path.exists(SERVICE_FILE):
            os.remove(SERVICE_FILE)
            print(f"Rimosso: {SERVICE_FILE}")
            
        # Reload
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("Disinstallazione completata. \u2705")

    except Exception as e:
        print(f"Errore durante la disinstallazione: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gestore Servizio Linux per Register IP Updater")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Install command
    install_parser = subparsers.add_parser("install", help="Installa e attiva il servizio systemd")
    install_parser.add_argument("--interval", default="1h", help="Intervallo di esecuzione (es. 30min, 1h, 2h). Default: 1h")

    # Uninstall command
    subparsers.add_parser("uninstall", help="Disinstalla e rimuove il servizio")

    args = parser.parse_args()

    # Check OS
    if os.name == 'nt':
        print("ATTENZIONE: Questo script è progettato per sistemi Linux con systemd.")
        print("Esecuzione su Windows non supportata per l'installazione dei servizi.")
        # We allow dry-run or exit. Since user asked for code, generating it is fine.
        # But running it will fail imports like 'getpass' sudo user check or paths.
        sys.exit(1)

    if args.command == "install":
        install_service(args.interval)
    elif args.command == "uninstall":
        uninstall_service()

if __name__ == "__main__":
    main()
