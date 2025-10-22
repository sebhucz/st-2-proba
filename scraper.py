# Import necessary libraries
import requests
from lxml import html, etree
import sys
import os
import traceback # To print full error details
import time # Do tworzenia unikalnych nazw plików

# --- Configuration ---
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY')
if not SCRAPINGBEE_API_KEY:
    print("Błąd: Nie znaleziono klucza API ScrapingBee...", file=sys.stderr)
    sys.exit(1)

# --- Scraping Function ---
def scrape_stooq_profile_with_scrapingbee(ticker):
    target_url = f"https://stooq.pl/q/p/?s={ticker}"
    description = None
    response = None

    try:
        print(f"Pobieranie strony przez ScrapingBee (JS, Premium Proxy, Wait): {target_url}...")
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': SCRAPINGBEE_API_KEY,
                'url': target_url,
                'render_js': 'true',
                # === 👇👇👇 Dodane/zmienione parametry 👇👇👇 ===
                'premium_proxy': 'true', # Użyj proxy rezydencjalnych
                'wait_for': "#f10 b:contains('Profil')", # Poczekaj na pojawienie się nagłówka 'Profil' (używając selektora CSS)
                'timeout': '15000', # Zwiększ ogólny timeout (w milisekundach)
                # === 👆👆👆 Koniec zmian 👆👆👆 ===
            },
            timeout=120 # Timeout dla samego połączenia requests (w sekundach)
        )
        response.raise_for_status()

        print(f"Status code (ScrapingBee): {response.status_code}")

        if not response.text or response.text.isspace() or "<html><head></head><body></body></html>" in response.text[:100]:
             print(f"Błąd: Otrzymano (potencjalnie) pustą odpowiedź z ScrapingBee dla {target_url}", file=sys.stderr)
             # Zapisz pustą odpowiedź do debugowania
             filename = f"error_empty_{ticker}_{int(time.time())}.html"
             with open(filename, "w", encoding="utf-8") as f:
                 f.write(response.text)
             print(f"Zapisano pustą odpowiedź do pliku: {filename}", file=sys.stderr)
             return None

        try:
            tree = html.fromstring(response.text)
            xpath_expr = "//b[normalize-space(text())='Profil']/ancestor::table[1]/following-sibling::div[1]/following-sibling::text()[normalize-space()]"
            description_nodes = tree.xpath(xpath_expr)

            if description_nodes:
                description = " ".join(node.strip() for node in description_nodes).strip()
                if "Źródło:" in description:
                    description = description.split("Źródło:")[0].strip()
                return description
            else:
                print(f"Nie znaleziono opisu dla tickera: {ticker} przy użyciu XPath (ScrapingBee, JS włączony).", file=sys.stderr)
                # --- 👇 Zapisz pełny HTML do pliku w razie błędu XPath 👇 ---
                print("Zapisywanie pełnego HTML do pliku w celu debugowania...", file=sys.stderr)
                filename = f"debug_html_{ticker}_{int(time.time())}.html"
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print(f"Pełny HTML zapisano do pliku: {filename}", file=sys.stderr)
                except Exception as save_e:
                    print(f"Nie udało się zapisać pliku HTML: {save_e}", file=sys.stderr)
                # --- 👆 Koniec zapisu do pliku 👆 ---
                return None

        except (etree.ParserError, ValueError) as parse_error:
            print(f"Błąd parsowania HTML (ScrapingBee): {parse_error}", file=sys.stderr)
            filename = f"error_parsing_{ticker}_{int(time.time())}.html"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"HTML powodujący błąd parsowania zapisano do: {filename}", file=sys.stderr)
            except Exception as save_e:
                print(f"Nie udało się zapisać pliku HTML przy błędzie parsowania: {save_e}", file=sys.stderr)
            return None

    # ... (reszta obsługi błędów requests i Exception bez zmian) ...
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        try:
             if response is not None and response.headers.get('Content-Type') == 'application/json':
                 error_detail = response.json().get('error', str(e))
        except ValueError:
             pass
        print(f"Błąd połączenia przez ScrapingBee dla {target_url}: {error_detail}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd (ScrapingBee): {e}", file=sys.stderr)
        traceback.print_exc()
        return None

    return description

# --- Script Execution ---
if __name__ == "__main__":
    ticker_symbol = "wod"
    print(f"Uruchamianie scrapera dla tickera: {ticker_symbol.upper()}")
    profile_description = scrape_stooq_profile_with_scrapingbee(ticker_symbol)
    if profile_description:
        print(f"\nOpis profilu dla {ticker_symbol.upper()} (przez ScrapingBee):\n")
        # Poprawka kodowania przy drukowaniu w niektórych terminalach
        try:
            print(profile_description)
        except UnicodeEncodeError:
            print(profile_description.encode('utf-8', 'ignore').decode('ascii', 'ignore'))
    else:
        print(f"\nNie udało się pobrać opisu profilu dla {ticker_symbol.upper()} (przez ScrapingBee).")
