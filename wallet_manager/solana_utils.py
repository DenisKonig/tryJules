import os
from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.rpc.core import RPCException
from typing import List, Dict, Any, Optional

# Konfiguration des RPC-Endpunkts.
# Du kannst einen öffentlichen Endpunkt verwenden oder einen eigenen/privaten.
# Für dieses Beispiel verwenden wir einen öffentlichen Endpunkt von Solana.
# Es ist ratsam, für eine Produktionsanwendung einen zuverlässigeren, ggf. kostenpflichtigen RPC-Knoten zu verwenden.
DEFAULT_RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
# Alternativ für Testzwecke:
# DEFAULT_RPC_ENDPOINT = "https://api.devnet.solana.com"
# DEFAULT_RPC_ENDPOINT = "https://api.testnet.solana.com"

class SolanaAPI:
    """
    Eine Klasse zur Interaktion mit der Solana Blockchain.
    """
    def __init__(self, rpc_endpoint: Optional[str] = None):
        """
        Initialisiert den Solana Client.

        :param rpc_endpoint: Der RPC-Endpunkt, zu dem eine Verbindung hergestellt werden soll.
                             Verwendet DEFAULT_RPC_ENDPOINT, wenn keiner angegeben ist.
        """
        self.rpc_endpoint = rpc_endpoint or os.getenv("SOLANA_RPC_ENDPOINT", DEFAULT_RPC_ENDPOINT)
        try:
            self.client = Client(self.rpc_endpoint, timeout=30) # Timeout auf 30 Sekunden erhöht
        except Exception as e:
            print(f"Fehler beim Initialisieren des Solana Clients: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """
        Überprüft, ob die Verbindung zum RPC-Endpunkt erfolgreich ist.
        """
        if not self.client:
            return False
        try:
            self.client.get_health()
            return True
        except RPCException as e:
            print(f"Verbindungsfehler zum RPC-Endpunkt {self.rpc_endpoint}: {e}")
            return False
        except Exception as e: # Allgemeinere Fehlerbehandlung
            print(f"Ein unerwarteter Fehler ist bei der Gesundheitsprüfung aufgetreten: {e}")
            return False

    def get_transaction_signatures(self, address_str: str, limit: int = 10, before_signature: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ruft die Signaturen der Transaktionen für eine bestimmte Adresse ab.

        :param address_str: Die Solana-Adresse als String.
        :param limit: Die maximale Anzahl der abzurufenden Signaturen.
        :param before_signature: Ruft Transaktionen vor dieser Signatur ab (für Paginierung).
        :return: Eine Liste von Transaktionssignaturen-Objekten oder eine leere Liste bei Fehlern.
        """
        if not self.client or not self.is_connected():
            print("Client nicht verbunden.")
            return []

        try:
            address_pubkey = PublicKey(address_str)
            params = {"limit": limit}
            if before_signature:
                params["before"] = before_signature

            # Hinweis: Die Solana API gibt die neuesten Transaktionen zuerst zurück.
            response = self.client.get_signatures_for_address(address_pubkey, **params)

            if response and response.get("result"):
                return response["result"]
            elif response and response.get("error"):
                print(f"Fehler beim Abrufen der Signaturen für Adresse {address_str}: {response['error']['message']}")
                return []
            else:
                print(f"Unerwartete Antwort beim Abrufen der Signaturen für {address_str}: {response}")
                return []
        except ValueError as e:
            print(f"Ungültige Adresse {address_str}: {e}")
            return []
        except RPCException as e:
            print(f"RPC Fehler beim Abrufen der Signaturen für Adresse {address_str}: {e}")
            return []
        except Exception as e:
            print(f"Allgemeiner Fehler beim Abrufen der Signaturen für {address_str}: {e}")
            return []

    def get_transaction_details(self, signature: str) -> Optional[Dict[str, Any]]:
        """
        Ruft die Details einer einzelnen Transaktion anhand ihrer Signatur ab.

        :param signature: Die Transaktionssignatur.
        :return: Ein Dictionary mit den Transaktionsdetails oder None bei Fehlern.
        """
        if not self.client or not self.is_connected():
            print("Client nicht verbunden.")
            return None

        try:
            # `max_supported_transaction_version` wird benötigt, um sicherzustellen, dass wir auch Versioned Transactions parsen können.
            # `commitment` kann 'processed', 'confirmed', oder 'finalized' sein. 'confirmed' ist ein guter Kompromiss.
            response = self.client.get_transaction(signature, encoding="jsonParsed", max_supported_transaction_version=0, commitment="confirmed")

            if response and response.get("result"):
                return response["result"]
            elif response and response.get("error"):
                print(f"Fehler beim Abrufen der Transaktionsdetails für Signatur {signature}: {response['error']['message']}")
                return None
            else:
                # Manchmal ist das Ergebnis None, auch wenn kein expliziter Fehler vorliegt, z.B. wenn die Tx noch nicht finalisiert ist
                # oder der RPC-Knoten sie nicht hat.
                if response and response.get("result") is None and not response.get("error"):
                    print(f"Transaktionsdetails für Signatur {signature} sind None, aber kein Fehler wurde gemeldet. Möglicherweise noch nicht finalisiert oder nicht auf diesem Knoten verfügbar.")
                else:
                    print(f"Unerwartete Antwort beim Abrufen der Transaktionsdetails für {signature}: {response}")
                return None
        except RPCException as e:
            print(f"RPC Fehler beim Abrufen der Transaktionsdetails für Signatur {signature}: {e}")
            return None
        except Exception as e:
            print(f"Allgemeiner Fehler beim Abrufen der Transaktionsdetails für {signature}: {e}")
            return None

    def get_transactions_for_address(self, address_str: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Ruft eine Liste von Transaktionsdetails für eine gegebene Adresse ab.

        :param address_str: Die Solana-Adresse als String.
        :param limit: Die maximale Anzahl der abzurufenden Transaktionen.
        :return: Eine Liste von Transaktionsdetail-Objekten.
        """
        signatures_result = self.get_transaction_signatures(address_str, limit=limit)
        transactions = []
        if not signatures_result:
            return transactions

        for sig_info in signatures_result:
            signature = sig_info.get("signature")
            if signature:
                print(f"Rufe Details für Signatur ab: {signature}")
                details = self.get_transaction_details(signature)
                if details:
                    transactions.append(details)
                else:
                    print(f"Konnte Details für Signatur {signature} nicht abrufen.")
            else:
                print(f"Keine Signatur im Signatur-Info-Objekt gefunden: {sig_info}")

        return transactions

# Beispielhafte Verwendung (kann für Tests auskommentiert werden):
# if __name__ == "__main__":
#     # Ersetze dies mit einer echten Solana-Adresse, für die du Transaktionen sehen möchtest
#     # Z.B. eine bekannte Adresse oder eine deiner Test-Wallet-Adressen
#     # Vorsicht mit Adressen, die sehr viele Transaktionen haben, da dies lange dauern kann.
#     # Beispiel: Die Adresse des Serum DEX v3 Programms (viele Transaktionen)
#     # test_address = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
#     # Eine Adresse mit weniger Transaktionen ist besser für ein schnelles Beispiel:
#     test_address = "Vote111111111111111111111111111111111111111" # Solana Vote Account Program
#
#     print(f"Initialisiere SolanaAPI mit Endpunkt: {DEFAULT_RPC_ENDPOINT}")
#     sol_api = SolanaAPI()
#
#     if sol_api.is_connected():
#         print(f"Erfolgreich mit {sol_api.rpc_endpoint} verbunden.")
#
#         print(f"\nAbrufen der letzten 5 Transaktionssignaturen für Adresse: {test_address}")
#         signatures = sol_api.get_transaction_signatures(test_address, limit=5)
#         if signatures:
#             for sig in signatures:
#                 print(f"  Signatur: {sig['signature']}, Slot: {sig['slot']}, Blockzeit: {sig.get('blockTime')}")
#         else:
#             print("Keine Signaturen gefunden oder Fehler.")
#
#         print(f"\nAbrufen der Details für die letzten 2 Transaktionen für Adresse: {test_address}")
#         # ACHTUNG: get_transactions_for_address kann viele RPC-Aufrufe verursachen (einen pro Signatur).
#         # Für eine echte Anwendung sollte dies sorgfältig gehandhabt werden (Paginierung, Caching, Rate Limiting).
#         transactions = sol_api.get_transactions_for_address(test_address, limit=2)
#         if transactions:
#             for i, tx in enumerate(transactions):
#                 print(f"\n--- Transaktion {i+1} ---")
#                 print(f"  Signatur: {tx['transaction']['signatures'][0]}")
#                 print(f"  Slot: {tx['slot']}")
#                 print(f"  Blockzeit: {tx.get('blockTime')} (Timestamp: {tx.get('blockTime')})")
#                 print(f"  Fee: {tx['meta']['fee']} Lamports")
#                 print(f"  Status: {'Erfolg' if tx['meta']['err'] is None else 'Fehler'}")
#                 # Die Struktur von `tx` kann sehr komplex sein. Hier nur ein paar Beispiele.
#                 # print(f"  Log-Nachrichten: {tx['meta'].get('logMessages')}")
#                 # print(f"  Instruktionen: {tx['transaction']['message']['instructions']}")
#         else:
#             print("Keine Transaktionsdetails gefunden oder Fehler.")
#     else:
#         print(f"Verbindung zu {sol_api.rpc_endpoint} fehlgeschlagen.")

# Wichtige Hinweise für die Weiterentwicklung:
# 1. Fehlerbehandlung: Die aktuelle Fehlerbehandlung ist rudimentär. Sie sollte verbessert werden,
#    um spezifischere Fehler zu erkennen und ggf. Wiederholungsversuche (Retries) mit Backoff zu implementieren.
# 2. Rate Limiting: Öffentliche RPC-Endpunkte haben oft strenge Rate Limits. Bei häufigen Abfragen
#    muss dies berücksichtigt werden (z.B. durch Pausen zwischen den Aufrufen oder einen besseren RPC-Provider).
# 3. Paginierung: Für Adressen mit vielen Transaktionen ist die Implementierung von Paginierung
#    (unter Verwendung des `before_signature`-Parameters) unerlässlich.
# 4. Datenextraktion: Die Transaktionsdetails (`tx`) sind sehr komplex. Es wird eine separate Logik benötigt,
#    um die relevanten Informationen (Sender, Empfänger, Betrag, Token-Typ etc.) für verschiedene
#    Transaktionstypen (SOL-Transfer, SPL-Token-Transfer, Swaps, Staking etc.) zu extrahieren.
#    Dies wird ein Kernbestandteil der Transaktionserkennung und -kategorisierung sein.
# 5. Asynchrone Verarbeitung: Für eine Webanwendung sollten diese Abfragen (besonders `get_transactions_for_address`)
#    asynchron im Hintergrund ausgeführt werden, um die Benutzeroberfläche nicht zu blockieren. Django unterstützt
#    asynchrone Views und Celery für Hintergrundaufgaben.
# 6. RPC Provider: Die Wahl des RPC Providers (aktuell api.mainnet-beta.solana.com) ist kritisch.
#    Für eine Produktionsanwendung sollte ein zuverlässigerer Service (z.B. Triton, QuickNode, Alchemy)
#    in Betracht gezogen werden, die oft auch bessere Performance und Features bieten.
#    Die URL kann über eine Umgebungsvariable `SOLANA_RPC_ENDPOINT` konfiguriert werden.
# 7. `max_supported_transaction_version=0`: Dies stellt sicher, dass wir auch "Versioned Transactions" (eingeführt mit TransactionV0)
#    korrekt parsen können, wenn wir `jsonParsed` als Encoding verwenden.
# 8. Commitment Level: `get_transaction` verwendet `commitment="confirmed"`. Je nach Anforderung
#    (Geschwindigkeit vs. Finalität) kann dies angepasst werden ('processed', 'confirmed', 'finalized').
#    'finalized' ist am sichersten, aber langsamer.
# 9. Timeout: Ein Timeout von 30 Sekunden wurde für den Client hinzugefügt, da manche RPC-Aufrufe länger dauern können.
#    Dies sollte ggf. weiter angepasst werden.
print("solana_utils.py wurde erstellt und grundlegende Funktionen implementiert.")
