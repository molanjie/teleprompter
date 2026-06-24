# Teleprompter

A web-based teleprompter application with remote control support.

## Features

- Browser-based teleprompter with adjustable speed
- Remote control via smartphone (QR code pairing)
- Real-time WebSocket synchronization
- Room-based multi-device control
- Adjustable font size, scroll speed, and mirror mode

## Quick Start

Open `index.html` in a browser, or serve it via any HTTP server:

```bash
python -m http.server 8888
```

For remote control functionality, run the companion server (`serve.py`) that provides WebSocket relay.

## Remote Control

1. Start the server: `python serve.py`
2. Open `http://localhost:8888` on the teleprompter screen
3. Scan the QR code with your phone to connect as remote controller
4. Control playback, speed, font size from your phone

## License

MIT
