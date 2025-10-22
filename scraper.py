import requests
from lxml import html, etree
import sys
import os # Do wczytania klucza API ze zmiennej środowiskowej

# Wczytaj klucz API ScrapingBee - najlepiej ze zmiennej środowiskowej
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY')
# Lub jeśli MUSISZ go wpisać na chwilę (NIE RÓB TEGO W KODZIE NA GITHUBIE!):
# SCRAPINGBEE_API_KEY = "TWOJ_KLUCZ_API_TUTAJ"

if not SCRAPINGBEE_API_KEY:
    print("Błąd: Nie znaleziono klucza API ScrapingBee w zmiennej środowiskowej SCRAPINGBEE_API_KEY.", file=sys.stderr)
    sys.exit(1) # Zakończ skrypt, jeśli nie ma klucza

def scrape_stooq_profile_with_scrapingbee(ticker):
    """
    Scrapuje opis profilu spółki ze strony Stooq używając ScrapingBee.

    Args:
        ticker (str): Symbol giełdowy spółki (np. 'wod').

    Returns:
        str: Opis spółki lub None, jeśli nie znaleziono.
    """
    target_url = f"https://stooq.pl/q/p/?s={ticker}"

    try:
        print(f"Pobieranie strony przez ScrapingBee: {target_url}...")
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': SCRAPINGBEE_API_KEY,
                'url': target_url,
                # 'render_js': 'false' # Domyślnie false, włącz (true) jeśli strona wymaga JS
                # 'premium_proxy': 'true' # Użyj, jeśli potrzebujesz proxy rezydencjalnych (może być droższe)
            },
            timeout=60 # ScrapingBee może potrzebować więcej czasu
        )
        response.raise_for_status()
        # ScrapingBee zazwyczaj zwraca poprawnie zdekodowany tekst
        # response.encoding = response.apparent_encoding # Raczej niepotrzebne

        print(f"Status code (ScrapingBee): {response.status_code}")
        print(f"Pierwsze 500 znaków odpowiedzi (ScrapingBee):\n{response.text[:500]}\n--- Koniec pierwszych 500 znaków ---")

        if not response.text or response.text.isspace():
             print(f"Błąd: Otrzymano pustą odpowiedź z ScrapingBee dla {target_url}", file=sys.stderr)
             return None

        try:
            # Używamy response.text, bo ScrapingBee zwraca zdekodowany HTML
            tree = html.fromstring(response.text)
        except (etree.ParserError, ValueError) as parse_error:
            print(f"Błąd parsowania HTML (ScrapingBee): {parse_error}", file=sys.stderr)
            return None

        xpath_expr = "//table[.//b[text()='Profil']]/following-sibling::text()[normalize-space()]"
        description_nodes = tree.xpath(xpath_expr)

        if description_nodes:
            description = " ".join(node.strip() for node in description_nodes).strip()
            if "Źródło:" in description:
                description = description.split("Źródło:")[0].strip()
            return description
        else:
            print(f"Nie znaleziono opisu dla tickera: {ticker} przy użyciu XPath (ScrapingBee).", file=sys.stderr)
            # Możesz dodać tu kod debugujący HTML jak wcześniej, jeśli potrzebujesz
            return None

    except requests.exceptions.RequestException as e:
        # Sprawdź, czy ScrapingBee nie zwrócił konkretnego błędu w odpowiedzi
        error_detail = response.json().get('error', str(e)) if response and response.headers.get('Content-Type') == 'application/json' else str(e)
        print(f"Błąd połączenia przez ScrapingBee dla {target_url}: {error_detail}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd (ScrapingBee): {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None

# --- Uruchomienie scrapera ---
if __name__ == "__main__":
    ticker_symbol = "wod"
    # Używamy nowej funkcji
    profile_description = scrape_stooq_profile_with_scrapingbee(ticker_symbol)

    if profile_description:
        print(f"\nOpis profilu dla {ticker_symbol.upper()} (przez ScrapingBee):\n")
        print(profile_description)
    else:
        print(f"\nNie udało się pobrać opisu profilu dla {ticker_symbol.upper()} (przez ScrapingBee).")
