from django.contrib import admin
from .models import Cryptocurrency, PriceData


@admin.register(Cryptocurrency)
class CryptocurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "slug", "created_at", "updated_at")
    search_fields = ("name", "slug", "symbol")
    list_filter = ("created_at",)


@admin.register(PriceData)
class PriceDataAdmin(admin.ModelAdmin):
    list_display = (
        "cryptocurrency",
        "price_usd",
        "market_cap",
        "volume_24h",
        "change_24h",
        "timestamp",
    )
    list_filter = ("cryptocurrency", "timestamp")
    date_hierarchy = "timestamp"
