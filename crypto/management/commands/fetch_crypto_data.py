import requests
from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency, PriceData


class Command(BaseCommand):
    help = "Fetches cryptocurrency data from CoinGecko API"

    def handle(self, *args, **kwargs):
        # CoinGecko API endpoint
        api_url = "https://api.coingecko.com/api/v3/simple/price"

        # Fetch all active cryptocurrencies
        cryptocurrencies = Cryptocurrency.objects.filter(is_active=True)

        try:
            # Prepare the list of cryptocurrency IDs for the API request
            ids = ",".join([crypto.name.lower() for crypto in cryptocurrencies])

            # Fetch data from CoinGecko
            response = requests.get(
                api_url,
                params={
                    "ids": ids,
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Update each cryptocurrency's data
            for crypto in cryptocurrencies:
                if crypto.name.lower() in data:
                    PriceData.objects.create(
                        cryptocurrency=crypto,
                        price_usd=data[crypto.name.lower()]["usd"],
                        market_cap=data[crypto.name.lower()]["usd_market_cap"],
                        volume_24h=data[crypto.name.lower()]["usd_24h_vol"],
                        change_24h=data[crypto.name.lower()]["usd_24h_change"],
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully updated {crypto.name} data")
                    )

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching data: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
