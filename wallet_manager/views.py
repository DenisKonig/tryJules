from django.shortcuts import render
from django.http import Http404
from .solana_utils import SolanaAPI
from .models import Wallet # Importieren wir, auch wenn wir es in dieser View noch nicht direkt zum Speichern nutzen
import datetime

def wallet_transactions_view(request, address: str):
    """
    Zeigt die letzten Transaktionen für eine gegebene Solana-Wallet-Adresse an.
    """
    sol_api = SolanaAPI()

    # Überprüfen, ob die Adresse gültig ist (rudimentäre Prüfung, Solana-Adressen sind typischerweise 32-44 Zeichen lang)
    # Eine korrekte Validierung würde die Base58-Dekodierung und Längenprüfung beinhalten.
    if not (32 <= len(address) <= 44 and address.isalnum()): # Einfache Prüfung
        # In einer echten Anwendung wäre hier eine robustere Adressvalidierung nötig
        # oder man verlässt sich darauf, dass die SolanaAPI Fehler wirft.
        # raise Http404("Ungültige Solana-Adresse.")
        # Fürs Erste versuchen wir es einfach, die API kümmert sich um Fehler bei ungültigen Adressen.
        pass

    if not sol_api.is_connected():
        # Hier könnten wir eine Fehlerseite oder eine Nachricht rendern
        # Fürs Erste eine einfache Ausgabe im Kontext.
        context = {
            'address': address,
            'error_message': f"Verbindung zum Solana RPC-Endpunkt ({sol_api.rpc_endpoint}) fehlgeschlagen.",
            'transactions': []
        }
        return render(request, 'wallet_manager/transaction_list.html', context, status=503)

    # Rufe die letzten N Transaktionen ab (z.B. 10)
    # In einer echten Anwendung sollte die Anzahl konfigurierbar sein oder Paginierung implementiert werden.
    raw_transactions = sol_api.get_transactions_for_address(address, limit=10)

    # Aufbereitung der Transaktionsdaten für das Template
    # Die Struktur von `raw_transactions` (Details von get_transaction) ist komplex.
    # Wir extrahieren hier nur einige Schlüsselelemente.

    display_transactions = []
    if raw_transactions:
        for tx_detail in raw_transactions:
            if tx_detail: # Sicherstellen, dass tx_detail nicht None ist
                signature = tx_detail.get("transaction", {}).get("signatures", [None])[0]
                block_time_unix = tx_detail.get("blockTime")
                block_time_readable = datetime.datetime.fromtimestamp(block_time_unix).strftime('%Y-%m-%d %H:%M:%S UTC') if block_time_unix else "N/A"
                slot = tx_detail.get("slot", "N/A")
                fee = tx_detail.get("meta", {}).get("fee", "N/A")

                # Einfache Fehlerprüfung aus den Metadaten
                err = tx_detail.get("meta", {}).get("err")
                status = "Fehlgeschlagen" if err else "Erfolgreich"

                # Versuch, eine einfache Beschreibung zu generieren
                # Dies ist sehr rudimentär und müsste für verschiedene Transaktionstypen erweitert werden.
                description = "Transaktion"
                instructions = tx_detail.get("transaction", {}).get("message", {}).get("instructions", [])
                if instructions:
                    first_instruction_type = instructions[0].get("parsed", {}).get("type", "Unbekannt")
                    # Beispiel: 'transfer', 'createAccount', 'vote', etc.
                    # Dies kann für eine erste Beschreibung verwendet werden.
                    description = f"Typ: {first_instruction_type}"

                    # Spezifischer für Transfers (SOL oder SPL Token)
                    if first_instruction_type == "transfer" or first_instruction_type == "transferChecked":
                        info = instructions[0].get("parsed", {}).get("info", {})
                        source = info.get("source")
                        destination = info.get("destination")
                        amount_lamports = info.get("lamports")
                        amount_tokens = info.get("tokenAmount", {}).get("uiAmountString") # Für SPL Tokens

                        if amount_tokens: # SPL Token Transfer
                            description = f"Token Transfer: {amount_tokens} von {source[:5]}... zu {destination[:5]}..."
                        elif amount_lamports: # SOL Transfer
                            description = f"SOL Transfer: {amount_lamports / 1e9:.6f} SOL von {source[:5]}... zu {destination[:5]}..."


                display_transactions.append({
                    'signature': signature,
                    'block_time_unix': block_time_unix,
                    'block_time_readable': block_time_readable,
                    'slot': slot,
                    'fee_lamports': fee,
                    'status': status,
                    'description': description, # Fürs Erste eine sehr einfache Beschreibung
                    'raw': tx_detail # Für Debugging im Template, falls nötig
                })
            else:
                # Fall, dass ein Element in raw_transactions None ist (sollte nicht oft vorkommen, aber sicher ist sicher)
                display_transactions.append({
                    'signature': 'N/A - Fehler beim Abruf',
                    'block_time_readable': 'N/A',
                    'slot': 'N/A',
                    'fee_lamports': 'N/A',
                    'status': 'Fehler',
                    'description': 'Konnte Transaktionsdetails nicht laden',
                    'raw': None
                })


    context = {
        'address': address,
        'transactions': display_transactions,
        'rpc_endpoint': sol_api.rpc_endpoint,
        'error_message': None # Wird gesetzt, falls die Verbindung fehlschlägt (siehe oben)
    }

    # Hier würden wir normalerweise die Transaktionen auch in der Datenbank speichern/aktualisieren.
    # z.B. Wallet.objects.get_or_create(address=address)
    # Dann für jede tx_detail: Transaction.objects.update_or_create(signature=..., defaults={...})
    # Das heben wir uns für eine spätere Iteration auf, um diesen Schritt fokussiert zu halten.

    return render(request, 'wallet_manager/transaction_list.html', context)
