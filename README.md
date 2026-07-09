esp32-backend/

```├── app/
│   ├── main.py               # Rotas HTTP e WebSocket
│   ├── auth.py                # Login, JWT, hash de senha
│   ├── websocket_manager.py   # Conexões e estado em tempo real
│   └── config.py              # Configurações via .env

```├── static/
│   └── dashboard.html         # Dashboard (HTML puro + JS)
├── firmware/
│   └── esp32_client.ino       # Exemplo de firmware pro ESP32 DevKit1

```├── scripts/
│   └── generate_password_hash.py
├── requirements.txt
└── .env.example

  ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

   ```bash
   cp .env.example .env
   python scripts/generate_password_hash.py
   ```

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
- `WIFI_SSID` / `WIFI_PASSWORD`
- `SERVER_HOST` (IP da máquina rodando o backend na sua rede)
- `DEVICE_API_KEY` (mesma chave do `.env`)



Acesse `http://localhost:8000` no navegador e faça login com o usuário/senha
   configurados.
