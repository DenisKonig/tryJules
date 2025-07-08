# Deployment Anleitung (Basis)

Diese Anleitung beschreibt die grundlegenden Schritte, um diese Django-Anwendung in einer Produktionsumgebung mit Gunicorn zu starten.

## Voraussetzungen

*   Linux-Server
*   Python 3.8+ und Pip
*   MySQL oder MariaDB Datenbankserver
*   Systemabhängigkeiten für `mysqlclient` (z.B. `libmysqlclient-dev` oder `mariadb-connector-c-devel` und `gcc`)
*   Git (um den Code zu klonen)

## Setup

1.  **Code klonen:**
    ```bash
    git clone <repository_url>
    cd <projekt_verzeichnis>
    ```

2.  **Python Virtual Environment erstellen und aktivieren (empfohlen):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```
    *Hinweis: Stellen Sie sicher, dass die Systemabhängigkeiten für `mysqlclient` installiert sind, bevor Sie diesen Schritt ausführen.*

4.  **Datenbank einrichten:**
    *   Erstellen Sie eine MySQL/MariaDB-Datenbank und einen Benutzer für die Anwendung.
    *   Konfigurieren Sie die Datenbankverbindung in den Umgebungsvariablen oder direkt in `solana_steuer_tool/settings.py` (nicht empfohlen für Produktion).
        *   `DB_NAME`
        *   `DB_USER`
        *   `DB_PASSWORD`
        *   `DB_HOST`
        *   `DB_PORT`
    *   Django wird versuchen, diese Variablen zu verwenden, wenn sie in `settings.py` entsprechend konfiguriert sind (aktuell sind dort Platzhalter). Für eine robustere Lösung sollten Sie `django-environ` oder ähnliche Pakete verwenden, um Umgebungsvariablen einfach in `settings.py` zu laden.

5.  **Django-spezifische Konfigurationen für Produktion:**
    *   **SECRET_KEY:** Setzen Sie eine starke, zufällige `DJANGO_SECRET_KEY` als Umgebungsvariable.
        ```bash
        export DJANGO_SECRET_KEY='IhrSehrGeheimerSchluesselHier'
        ```
    *   **DEBUG:** Stellen Sie sicher, dass `DJANGO_DEBUG` auf `False` gesetzt ist (oder nicht gesetzt ist, da der Standard `False` ist).
        ```bash
        export DJANGO_DEBUG='False'
        ```
    *   **ALLOWED_HOSTS:** Setzen Sie `DJANGO_ALLOWED_HOSTS` auf die Domain(s), unter denen Ihre Anwendung erreichbar sein wird.
        ```bash
        export DJANGO_ALLOWED_HOSTS='ihredomain.com,www.ihredomain.com,localhost'
        ```
        (Passen Sie `localhost` an, falls Gunicorn lokal läuft und von einem Reverse Proxy bedient wird).

6.  **Datenbankmigrationen durchführen:**
    ```bash
    python manage.py migrate
    ```

7.  **Statische Dateien sammeln:**
    ```bash
    python manage.py collectstatic --noinput
    ```
    Dies sammelt alle statischen Dateien in das Verzeichnis, das in `STATIC_ROOT` in `settings.py` definiert ist (standardmäßig `staticfiles`).

## Anwendung mit Gunicorn starten

Gunicorn ist ein WSGI HTTP Server für UNIX.

1.  **Gunicorn direkt starten (Beispiel):**
    ```bash
    gunicorn --workers 3 --bind 0.0.0.0:8000 solana_steuer_tool.wsgi:application
    ```
    *   `--workers 3`: Anzahl der Worker-Prozesse. Eine gute Faustregel ist `2 * <Anzahl_CPU_Kerne> + 1`.
    *   `--bind 0.0.0.0:8000`: Bindet Gunicorn an alle Netzwerkinterfaces auf Port 8000.
    *   `solana_steuer_tool.wsgi:application`: Der Pfad zum WSGI-Anwendungsobjekt.

2.  **Empfohlen: Gunicorn mit einem Prozessmanager (z.B. systemd, Supervisor) betreiben:**
    Dies stellt sicher, dass Gunicorn bei Fehlern neu gestartet wird und beim Systemstart automatisch startet.

    **Beispiel für eine systemd Service Unit (`/etc/systemd/system/solana_steuer_tool.service`):**
    ```ini
    [Unit]
    Description=gunicorn daemon for solana_steuer_tool
    After=network.target

    [Service]
    User=<ihr_benutzer> # Der Benutzer, unter dem Gunicorn laufen soll
    Group=<ihre_gruppe> # Die Gruppe, unter dem Gunicorn laufen soll
    WorkingDirectory=/pfad/zu/ihrem/projekt_verzeichnis
    Environment="PATH=/pfad/zu/ihrem/projekt_verzeichnis/venv/bin"
    Environment="DJANGO_SECRET_KEY=IhrSehrGeheimerSchluesselHier"
    Environment="DJANGO_DEBUG=False"
    Environment="DJANGO_ALLOWED_HOSTS=ihredomain.com,www.ihredomain.com"
    # Fügen Sie hier weitere Umgebungsvariablen für die Datenbank etc. hinzu
    # Environment="DB_NAME=solana_steuer_db"
    # ...
    ExecStart=/pfad/zu/ihrem/projekt_verzeichnis/venv/bin/gunicorn \
        --workers 3 \
        --bind unix:/run/solana_steuer_tool.sock \
        solana_steuer_tool.wsgi:application

    [Install]
    WantedBy=multi-user.target
    ```
    *   Ersetzen Sie `<ihr_benutzer>`, `<ihre_gruppe>` und die Pfade entsprechend.
    *   Das Binden an einen Unix-Socket (`unix:/run/solana_steuer_tool.sock`) ist üblich, wenn ein Reverse Proxy wie Nginx davor geschaltet wird.
    *   Nach Erstellen/Ändern der Service-Datei:
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl start solana_steuer_tool
        sudo systemctl enable solana_steuer_tool # Zum automatischen Start beim Booten
        sudo systemctl status solana_steuer_tool # Status prüfen
        ```

## Reverse Proxy (Nginx - empfohlen)

Es wird dringend empfohlen, einen Reverse Proxy wie Nginx vor Gunicorn zu schalten. Nginx kann:
*   Statische Dateien effizienter ausliefern (obwohl Whitenoise das auch gut kann).
*   HTTPS/SSL-Terminierung übernehmen.
*   Anfragen puffern.
*   Als Load Balancer dienen, falls mehrere Instanzen laufen.

Ein Beispiel für eine Nginx-Konfiguration folgt, wenn benötigt.

---

Diese Anleitung ist eine Basis. Für eine robuste Produktionsumgebung sind weitere Überlegungen notwendig (Logging, Monitoring, Sicherheitshärtung, Backup-Strategien etc.).
```
