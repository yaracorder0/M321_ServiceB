# Service B – Item Provider API

REST-Service in Python (Standardbibliothek, ohne externe Dependencies) mit formalem **API Contract** (OpenAPI 3.0) und entkoppeltem **Interface-Design**.

**Rolle im Modul 321:** Daten-Provider – stellt über standardisierte Schnittstellen Daten für Consumer-Services (z. B. **Service A**) bereit.

---

## 📋 API Contract (Schnittstellenvertrag)

Der Schnittstellenvertrag ist als **OpenAPI 3.0.3** Spezifikation definiert und liegt im Repository:
- [openapi.json](file:///C:/VSC/school/M321_ServiceB/openapi.json) (maschinenlesbar)
- [openapi.yaml](file:///C:/VSC/school/M321_ServiceB/openapi.yaml) (menschenlesbar)

Zur Laufzeit wird der Vertrag direkt vom Service ausgeliefert:
- **Vertrag (JSON):** `http://localhost:5000/openapi.json`
- **Interaktive Dokumentation (Swagger UI):** `http://localhost:5000/docs`

---

## 🏛️ Architektur & Interfaces

Das Projekt folgt dem Prinzip der Schnittstellentrennung und Vertragstreue:

1. **`models.py`**:
   - `Item`: Dataclass mit strikter Typisierung (`id: int`, `name: str`, `price: float`).
2. **`service.py`**:
   - `ItemServiceInterface`: Abstraktes Interface (`abc.ABC`), das alle Datenoperationen (`get_all`, `get_by_id`, `create`, `update`, `delete`) vertraglich vorschreibt.
   - `InMemoryItemService`: Konkrete Implementierung des Interfaces.
3. **`contract.py`**:
   - Lädt die Spezifikation und validiert eingehende Payloads gegen das Schema `ItemInput` (Pflichtfelder `name` (String, min 1 Zeichen), `price` (Zahl > 0)).
4. **`app.py`**:
   - HTTP-Server (Standardbibliothek `http.server`), der Routen auf die Methoden des Interfaces abbildet und standardisierte Statuscodes & Fehlerantworten (`ErrorResponse`) zurückgibt.

---

## 🚀 Starten

```bash
python app.py
```

Läuft standardmässig auf `http://localhost:5000` (Port via Umgebungsvariable `PORT` konfigurierbar).

---

## 📡 Endpunkte-Übersicht

| Methode | Pfad | Beschreibung | Statuscodes |
|---------|------|--------------|-------------|
| `GET` | `/` | Willkommensnachricht | `200` |
| `GET` | `/health` | Health-Check für Service Discovery | `200` |
| `GET` | `/openapi.json` | OpenAPI 3.0 Spezifikation | `200` |
| `GET` | `/openapi.yaml` | OpenAPI 3.0 YAML | `200` |
| `GET` | `/docs` | Interaktive Swagger-UI Dokumentation | `200` |
| `GET` | `/api/items` | Alle Items abrufen (wird von Service A genutzt) | `200` |
| `GET` | `/api/items/{id}` | Einzelnes Item nach ID abrufen | `200`, `400`, `404` |
| `POST` | `/api/items` | Neues Item anlegen (Payload: `name`, `price`) | `201`, `400` |
| `PUT` | `/api/items/{id}` | Item aktualisieren (Payload: `name`, `price`) | `200`, `400`, `404` |
| `DELETE`| `/api/items/{id}` | Item löschen | `200`, `404` |

---

## 🧪 Tests ausführen

Das Projekt verfügt über automatische Unittests und End-to-End Vertragstests:

```bash
python -m unittest test_contract.py -v
```
