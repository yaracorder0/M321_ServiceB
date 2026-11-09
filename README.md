# Service B

Hello-World-Service in Python (nur Standardbibliothek, keine Dependencies).

## Starten

```bash
python app.py
```

Läuft auf `http://localhost:5000` (Port via `PORT` änderbar).

| Endpoint  | Antwort                                        |
|-----------|------------------------------------------------|
| `/`       | `{"message":"Hello World from Service B"}`     |
| `/health` | `{"status":"UP","service":"service-b"}`        |
