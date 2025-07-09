# Phase 1: Build-Phase (falls Multi-Stage-Builds für komplexere Szenarien benötigt werden, hier aber erstmal einfach)
FROM python:3.10-slim-bullseye AS base

# Umgebungsvariablen setzen
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PIP_DEFAULT_TIMEOUT 100

# Systemabhängigkeiten installieren
# - gcc und libmariadb-dev (oder default-libmysqlclient-dev) für mysqlclient
# - brotli für whitenoise[brotli]
# - curl und andere Werkzeuge können für Healthchecks oder Debugging nützlich sein
# - libpq-dev für psycopg2 (falls Kompilierung aus Quellen nötig wird, z.B. für armv7l)
# - rustc und cargo für Pakete mit Rust-Abhängigkeiten (z.B. solders, brotli Python-Paket)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \ # Bevorzugt für breitere Kompatibilität
    libpq-dev \ # Für psycopg2 Fallback-Kompilierung
    brotli \ # Stellt libbrotli bereit, whitenoise[brotli] könnte dies verwenden oder sein eigenes kompilieren
    curl \
    # Rust-Toolchain für solders und ggf. andere Pakete
    ca-certificates \ # Erforderlich für den Rust-Installations-Skript-Download
    gnupg \ # Erforderlich für das Rust-Installations-Skript
    # Ende Rust-Toolchain Vorbereitung
    # Aufräumen, um Image-Größe zu reduzieren (wird später separat gemacht nach Rust-Installation)
    && rm -rf /var/lib/apt/lists/*

# Rust installieren (wird für solders und ggf. brotli benötigt, falls keine Wheels passen)
# Die Installation von Rust bläht das Image auf. Wenn möglich, in einem Multi-Stage-Build nur für die Build-Phase verwenden.
# Für dieses Beispiel wird es direkt installiert.
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain stable -y \
    && apt-get update && apt-get install -y --no-install-recommends pkg-config \ # pkg-config wird oft von Rust-Builds benötigt
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* # Aufräumen nach Rust und pkg-config

# Arbeitsverzeichnis erstellen und setzen
WORKDIR /app

# Python-Abhängigkeiten installieren
# Zuerst nur requirements.txt kopieren, um den Docker-Cache zu nutzen,
# wenn sich nur der Code, aber nicht die Abhängigkeiten ändern.
# Wir installieren Abhängigkeiten NACHDEM Rust eingerichtet ist.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Django-Projektverzeichnis erstellen (falls es Unterordner gibt, die nicht im Root liegen)
# In unserem Fall ist das Projekt im Root des Repos, daher ist dieser Schritt nicht zwingend nötig,
# aber gut für die Struktur, falls sich das ändert.
# RUN mkdir /app/solana_steuer_tool
# WORKDIR /app/solana_steuer_tool # Wenn das Projekt in einem Unterordner wäre

# Den gesamten Anwendungscode kopieren
COPY . .

# Statische Dateien sammeln
# DEBUG muss hier explizit auf einen Wert gesetzt werden, der nicht 'True' ist,
# oder die collectstatic-Prüfung für DEBUG umgangen werden,
# da collectstatic bei DEBUG=True ggf. nicht alle Dateien sammelt oder anders agiert.
# Wir haben DEBUG in settings.py so konfiguriert, dass es standardmäßig False ist, es sei denn, DJANGO_DEBUG=True ist gesetzt.
# Daher sollte es hier standardmäßig korrekt funktionieren.
RUN python manage.py collectstatic --noinput --clear

# Port freigeben, den Gunicorn verwenden wird
EXPOSE 8000

# Gunicorn als Entrypoint verwenden, um die Anwendung zu starten
# Die Anzahl der Worker sollte idealerweise über Umgebungsvariablen oder eine Konfigurationsdatei gesteuert werden.
# Für dieses Beispiel setzen wir sie fest.
# Die Umgebungsvariablen für Django (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB-Settings)
# müssen beim Starten des Containers gesetzt werden (z.B. über docker run -e VAR=value ... oder docker-compose.yml).
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8000", "solana_steuer_tool.wsgi:application"]

# Hinweise zum Bauen und Ausführen:
# 1. Dockerfile und .dockerignore im Root-Verzeichnis des Projekts.
# 2. Bauen: docker build -t solana-steuer-tool .
# 3. Ausführen (Beispiel, Umgebungsvariablen anpassen!):
#    docker run -p 8000:8000 \
#    -e DJANGO_SECRET_KEY='supergeheim' \
#    -e DJANGO_DEBUG='False' \
#    -e DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1' \
#    -e DB_NAME='meine_db' \
#    -e DB_USER='mein_user' \
#    -e DB_PASSWORD='mein_passwort' \
#    -e DB_HOST='host.docker.internal' \ # Für Verbindung zu DB auf dem Docker-Host (mac/windows) oder IP des DB-Servers
#    -e DB_PORT='3306' \
#    solana-steuer-tool
#
# Für die Datenbankverbindung vom Container zu einem Host-Dienst oder einem anderen Container
# müssen DB_HOST und ggf. Netzwerk-Einstellungen angepasst werden.
# 'host.docker.internal' ist eine spezielle DNS für Docker Desktop (Mac/Windows).
# In Linux-Umgebungen ist es oft die IP der Bridge-Schnittstelle (z.B. 172.17.0.1) oder der Name des DB-Containers im selben Docker-Netzwerk.
