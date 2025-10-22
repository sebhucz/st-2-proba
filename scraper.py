import requests
from lxml import html
import sys

def scrape_stooq_profile(ticker):
    """
    Scrapuje opis profilu spółki ze strony Stooq.

    Args:
        ticker (str): Symbol giełdowy spółki (np. 'wod').

    Returns:
        str: Opis spółki lub None, jeśli nie znaleziono.
    """
    url = f"https://stooq.pl/q/p/?s={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Sprawdza czy status HTTP jest OK (2xx)
        response.encoding = response.apparent_encoding # Poprawne dekodowanie polskich znaków

        # Parsowanie HTML za pomocą lxml
        tree = html.fromstring(response.content)

        # Użycie XPath do znalezienia opisu
        # Szukamy tabeli zawierającej <b>Profil</b>, a następnie bierzemy następny
        # węzeł tekstowy (rodzeństwo), który nie jest pusty.
        xpath_expr = "//table[.//b[text()='Profil']]/following-sibling::text()[normalize-space()]"
        description_nodes = tree.xpath(xpath_expr)

        if description_nodes:
            # Łączymy i czyścimy znaleziony tekst
            description = " ".join(node.strip() for node in description_nodes).strip()
            # Czasem łapie też stopkę "Źródło: Quant Research", usuwamy ją
            if "Źródło:" in description:
                description = description.split("Źródło:")[0].strip()
            return description
        else:
            print(f"Nie znaleziono opisu dla tickera: {ticker}", file=sys.stderr)
            return None

    except requests.exceptions.RequestException as e:
        print(f"Błąd połączenia ze stroną {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}", file=sys.stderr)
        return None

# --- Uruchomienie scrapera ---
if __name__ == "__main__":
    ticker_symbol = "wod"
    profile_description = scrape_stooq_profile(ticker_symbol)

    if profile_description:
        print(f"Opis profilu dla {ticker_symbol.upper()}:\n")
        print(profile_description)
    else:
        print(f"\nNie udało się pobrać opisu profilu dla {ticker_symbol.upper()}.")
