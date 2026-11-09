# Service B

Hello-World-Service in Python (nur Standardbibliothek, keine Dependencies).
**Rolle: Daten-Provider** – stellt unter `/api/items` Daten bereit, die Service A abruft.

## Starten

```bash
python app.py
```

Läuft auf `http://localhost:5000` (Port via `PORT` änderbar).

| Endpoint  | Antwort                                        |
|-----------|------------------------------------------------|
| `/`       | `{"message":"Hello World from Service B"}`     |
| `/health` | `{"status":"UP","service":"service-b"}`        |
| `/api/items` | Liste von Items (`id`, `name`, `price`) als JSON |
