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

## Bereitstellung auf Raspberry Pi OS (oder anderen ARM-basierten Systemen)

Die `Dockerfile` im Hauptverzeichnis des Projekts ist so angepasst, dass sie auch Docker-Images für ARM-Architekturen, wie sie auf dem Raspberry Pi verwendet werden (z.B. `arm64/v8` oder `arm/v7`), erstellen kann.

### Voraussetzungen

*   Docker auf dem Raspberry Pi installiert und konfiguriert.
*   Eine externe Datenbank (MySQL/MariaDB oder PostgreSQL), die vom Raspberry Pi aus erreichbar ist, oder eine lokal auf dem Pi installierte Datenbank.

### Bau des Docker-Images auf Raspberry Pi

1.  **Klonen Sie das Repository** auf Ihre Raspberry Pi:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Bauen Sie das Docker-Image:**
    Führen Sie im Hauptverzeichnis des Projekts (wo sich die `Dockerfile` befindet) folgenden Befehl aus:
    ```bash
    docker build -t solana-steuer-tool-rpi .
    ```
    Dieser Prozess kann auf einem Raspberry Pi einige Zeit in Anspruch nehmen, da möglicherweise einige Python-Pakete und Rust-Abhängigkeiten (für `solders`) kompiliert werden müssen.

    Wenn Sie von einem anderen Rechner (z.B. x86_64) für eine Raspberry Pi bauen möchten (Cross-Compilation), können Sie `buildx` verwenden:
    ```bash
    # Sicherstellen, dass buildx eingerichtet ist (oft standardmäßig bei neueren Docker-Versionen)
    # docker buildx create --use

    # Beispiel für arm64 (z.B. Raspberry Pi 3/4/5 im 64-Bit-Modus)
    docker buildx build --platform linux/arm64/v8 -t yourusername/solana-steuer-tool-rpi --load .
    # Oder für armv7 (z.B. Raspberry Pi 2/3 im 32-Bit-Modus)
    # docker buildx build --platform linux/arm/v7 -t yourusername/solana-steuer-tool-rpi --load .

    # Wenn Sie das Image direkt in eine Registry pushen wollen (z.B. Docker Hub):
    # docker buildx build --platform linux/arm64/v8 -t yourusername/solana-steuer-tool-rpi --push .
    ```
    Das `--load` Argument lädt das gebaute Image in die lokale Docker-Instanz. Das `--push` Argument lädt es in eine Registry hoch.

### Ausführen des Containers

Nachdem das Image erfolgreich gebaut wurde (entweder direkt auf dem Pi oder per Pull von einer Registry), können Sie den Container starten. Passen Sie die Umgebungsvariablen an Ihre Datenbankkonfiguration und andere Einstellungen an:

```bash
docker run -d \
  -p 8000:8000 \
  --name solana-steuer-tool-app \
  -e DJANGO_SECRET_KEY='IhrSehrGeheimerSchluesselHier' \
  -e DJANGO_DEBUG='False' \
  -e DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,IHRE_PI_IP_ADRESSE' \
  -e DB_ENGINE='django.db.backends.mysql' \ # oder 'django.db.backends.postgresql'
  -e DB_NAME='IhreDatenbank' \
  -e DB_USER='IhrDbBenutzer' \
  -e DB_PASSWORD='IhrDbPasswort' \
  -e DB_HOST='IP_IHRES_DB_SERVERS' \ # z.B. die IP des Pi, falls DB lokal läuft, oder externe IP
  -e DB_PORT='3306' \ # oder '5432' für PostgreSQL
  solana-steuer-tool-rpi # Oder der Name Ihres Images, z.B. yourusername/solana-steuer-tool-rpi
```

**Hinweise zu Umgebungsvariablen für Raspberry Pi:**
*   `DJANGO_ALLOWED_HOSTS`: Fügen Sie die IP-Adresse Ihrer Raspberry Pi hinzu, damit Sie von anderen Geräten im Netzwerk darauf zugreifen können.
*   `DB_HOST`: Wenn die Datenbank auf derselben Raspberry Pi läuft (nicht im Docker-Container, sondern als Dienst auf dem Host-System), können Sie versuchen, die Docker-Host-IP (oft `172.17.0.1` auf Linux, wenn das Standard-Bridge-Netzwerk verwendet wird) oder die LAN-IP der Raspberry Pi zu verwenden. Wenn die Datenbank in einem anderen Docker-Container läuft, verwenden Sie den Namen dieses Containers als Host, vorausgesetzt, beide sind im selben Docker-Netzwerk.

### Wichtige Anpassungen in der Dockerfile für ARM

Die `Dockerfile` enthält spezifische Anpassungen, um die Kompatibilität mit ARM-Architekturen zu verbessern:
*   **Systemabhängigkeiten:** Installation von `default-libmysqlclient-dev` (für MySQL/MariaDB), `libpq-dev` (für PostgreSQL-Fallback-Kompilierung), `brotli`, `ca-certificates`, `gnupg` und `pkg-config`.
*   **Rust-Toolchain:** Installation von `rustc` und `cargo` über `rustup.rs`. Dies ist entscheidend für die Kompilierung der `solders`-Bibliothek (eine Abhängigkeit von `solana-py`) und potenziell anderer Pakete mit Rust-Code, falls keine passenden vorkompilierten Wheels für die ARM-Architektur verfügbar sind.
*   Das Basis-Image `python:3.10-slim-bullseye` ist multi-arch und unterstützt gängige ARM-Versionen.

Diese Anpassungen stellen sicher, dass die notwendigen Werkzeuge und Bibliotheken während des Docker-Build-Prozesses auf einer ARM-Plattform vorhanden sind.
