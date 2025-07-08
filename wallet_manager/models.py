from django.db import models
from django.utils import timezone

class Wallet(models.Model):
    """
    Repräsentiert eine Solana-Wallet-Adresse, die vom Benutzer verfolgt wird.
    """
    address = models.CharField(max_length=44, unique=True, help_text="Solana Wallet Adresse (z.B. Base58-kodierter Public Key)")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Ein optionaler, benutzerdefinierter Name für das Wallet")
    added_at = models.DateTimeField(default=timezone.now, help_text="Zeitpunkt, zu dem das Wallet hinzugefügt wurde")

    def __str__(self):
        return f"{self.name or self.address}"

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ['-added_at']


class Transaction(models.Model):
    """
    Repräsentiert eine einzelne Transaktion auf der Solana-Blockchain,
    die einem verfolgten Wallet zugeordnet ist.
    """
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions", help_text="Das Wallet, zu dem diese Transaktion gehört")
    signature = models.CharField(max_length=88, unique=True, help_text="Eindeutige Transaktionssignatur (Base58-kodiert)") # Signaturen können bis zu 88 Zeichen lang sein (z.B. für Ed25519)
    block_time = models.BigIntegerField(help_text="Unix-Timestamp der Transaktion (Zeitpunkt, zu dem sie in einen Block aufgenommen wurde)") # Als BigInt für Unix Timestamp
    slot = models.BigIntegerField(help_text="Der Slot, in dem die Transaktion bestätigt wurde")
    fee = models.BigIntegerField(help_text="Transaktionsgebühr in Lamports")

    # Für den Anfang eine einfache Beschreibung. Später können wir hier ein JSONField für mehr Details verwenden.
    # raw_data = models.JSONField(default=dict, help_text="Rohe Transaktionsdaten oder relevante extrahierte Teile")
    description = models.TextField(blank=True, null=True, help_text="Eine kurze Beschreibung oder Notiz zur Transaktion")

    # Meta-Informationen zur Verarbeitung in unserem System
    imported_at = models.DateTimeField(default=timezone.now, help_text="Zeitpunkt, zu dem die Transaktion in die Datenbank importiert wurde")
    meta_data = models.JSONField(default=dict, null=True, blank=True, help_text="Zusätzliche Metadaten aus der RPC-Antwort (z.B. meta.preBalances, postBalances, etc.)")
    raw_transaction_data = models.JSONField(default=dict, null=True, blank=True, help_text="Die vollständige rohe Transaktion von get_transaction")


    def __str__(self):
        return f"Transaktion {self.signature[:10]}... für Wallet {self.wallet.address[:10]}..."

    class Meta:
        verbose_name = "Transaktion"
        verbose_name_plural = "Transaktionen"
        ordering = ['-block_time'] # Neueste Transaktionen zuerst
        indexes = [
            models.Index(fields=['wallet', '-block_time']),
            models.Index(fields=['signature']),
        ]
