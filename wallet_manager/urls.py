from django.urls import path
from . import views

app_name = 'wallet_manager'

urlpatterns = [
    path('wallet/<str:address>/transactions/', views.wallet_transactions_view, name='wallet_transactions'),
    # Wir könnten hier später eine Übersichtsseite für alle Wallets hinzufügen
    # path('', views.dashboard_view, name='dashboard'),
]
