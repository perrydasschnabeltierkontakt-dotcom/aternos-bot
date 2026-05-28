# aternos-bot

Ein einfacher Discord-Bot, der deinen Aternos-Server per Slash-Befehl `/start` starten kann.

## Einrichtung

### Python-Variante für Katabump

1. Lade alle Dateien hoch: `bot.py`, `requirements.txt`, `config.example.json`, `.gitignore`, optional `.env.example`.
2. Erstelle eine `config.json` nach `config.example.json` und trage deine Werte ein.
3. Katabump installiert automatisch die Python-Abhängigkeiten aus `requirements.txt`.
4. Starte den Bot mit der Play/Start-Funktion von Katabump.

### Node.js-Variante (optional)

Wenn du lieber Node.js verwendest, kannst du die vorhandenen Dateien `package.json` und `bot.js` weiter nutzen. Katabump scheint aber nur Python über `requirements.txt` zu unterstützen, daher ist die Python-Variante hier empfohlen.

## Konfiguration

Du kannst `config.json` benutzen, wenn dein Hoster Umgebungsvariablen nicht direkt setzt. Der Bot liest zuerst `DISCORD_TOKEN`, `DISCORD_CLIENT_ID` usw. aus der Umgebung und dann aus `config.json`.

Beispiel `config.json`:
```json
{
  "DISCORD_TOKEN": "dein_discord_bot_token",
  "DISCORD_CLIENT_ID": "deine_discord_app_client_id",
  "DISCORD_GUILD_ID": "deine_server_id",
  "ATERNOS_LOGIN": "dein_aternos_email_oder_username",
  "ATERNOS_PASSWORD": "dein_aternos_passwort",
  "ATERNOS_SERVER_URL": "https://aternos.org/server"
}
```

## Bot starten

Für Katabump starte den Python-Bot so:

```bash
python bot.py
```

## Katabump Deployment

1. Lade die Dateien hoch: `bot.py`, `requirements.txt`, `config.example.json`, `.gitignore`, optional `.env.example`.
2. Erstelle in Katabump eine `config.json` aus `config.example.json` und trage deine Zugangsdaten ein.
3. Katabump installiert automatisch `requirements.txt`.
4. Verwende die Play/Start-Funktion von Katabump, um `python bot.py` auszuführen.

> Wichtig: `config.json` sollte nicht ins Repo hochgeladen werden. Katabump kann die Datei aber intern speichern, solange sie privat ist.

## Nutzung

Im Discord-Server einfach `/start` eingeben. Der Bot versucht dann, sich bei Aternos einzuloggen und den Server zu starten.

## Hinweise

- Der Bot verwendet `pyppeteer`, um die Aternos-Webseite zu automatisieren.
- Achte darauf, dass der Bot auf dem Rechner läuft, auf dem du ihn selbst hostest.
- Speichere Passwörter niemals in öffentlich zugänglichen Repositories.
