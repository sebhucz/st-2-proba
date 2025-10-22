# Import necessary libraries
import requests
from lxml import html, etree
import sys
import os
import traceback # To print full error details

# --- Configuration ---
# Read ScrapingBee API key from environment variable (recommended for security)
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY')

# Exit if the API key is not found
if not SCRAPINGBEE_API_KEY:
    print("Błąd: Nie znaleziono klucza API ScrapingBee w zmiennej środowiskowej SCRAPINGBEE_API_KEY.", file=sys.stderr)
    sys.exit(1) # Exit the script with an error code

# --- Scraping Function ---
def scrape_stooq_profile_with_scrapingbee(ticker):
    """
    Scrapes the company profile description from Stooq using ScrapingBee.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'wod').

    Returns:
        str: The company description or None if not found or an error occurs.
    """
    target_url = f"https://stooq.pl/q/p/?s={ticker}"
    description = None # Initialize description as None
    response = None # Initialize response to avoid potential UnboundLocalError

    try:
        print(f"Pobieranie strony przez ScrapingBee (z JS): {target_url}...")
        # Make the request to ScrapingBee API
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': SCRAPINGBEE_API_KEY,
                'url': target_url,
                # === Włącz renderowanie JavaScript ===
                'render_js': 'true', # Zmienione z 'false' lub odkomentowane
                # =====================================
                # 'premium_proxy': 'true', # Odkomentuj, jeśli samo render_js nie wystarczy
                # 'block_resources': 'false'
            },
            timeout=90 # Zwiększony timeout dla renderowania JS
        )
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        print(f"Status code (ScrapingBee): {response.status_code}")
        # Odkomentuj poniższą linię do dokładniejszego debugowania, jeśli potrzebne
        # print(f"Pierwsze 500 znaków odpowiedzi (ScrapingBee):\n{response.text[:500]}\n--- Koniec pierwszych 500 znaków ---")

        # Check if the response text is empty or only whitespace
        if not response.text or response.text.isspace():
             print(f"Błąd: Otrzymano pustą odpowiedź z ScrapingBee dla {target_url} (nawet z JS)", file=sys.stderr)
             return None

        try:
            # Parse the HTML content using lxml
            tree = html.fromstring(response.text)

            # Define the XPath expression (z poprzedniej poprawki)
            xpath_expr = "//b[normalize-space(text())='Profil']/ancestor::table[1]/following-sibling::div[1]/following-sibling::text()[normalize-space()]"

            description_nodes = tree.xpath(xpath_expr)

            if description_nodes:
                # Join the found text nodes and clean whitespace
                description = " ".join(node.strip() for node in description_nodes).strip()
                # Remove the "Źródło:" footer if present
                if "Źródło:" in description:
                    description = description.split("Źródło:")[0].strip()
                # Return the found description immediately
                return description
            else:
                # If XPath found nothing, but parsing succeeded
                print(f"Nie znaleziono opisu dla tickera: {ticker} przy użyciu XPath (ScrapingBee, JS włączony).", file=sys.stderr)

                # --- Optional HTML Debugging Code ---
                # Możesz odkomentować ten blok, jeśli nadal potrzebujesz sprawdzić strukturę HTML
                # print("\n--- DEBUG: Sprawdzanie struktury HTML wokół tekstu 'Profil' (JS włączony) ---", file=sys.stderr)
                # try:
                #     profil_elements = tree.xpath("//*[contains(normalize-space(.), 'Profil')]")
                #     if profil_elements:
                #         print(f"Znaleziono {len(profil_elements)} elementów zawierających 'Profil'.", file=sys.stderr)
                #         reference_element = profil_elements[0]
                #         parent_element = reference_element.getparent()
                #         if parent_element is not None:
                #             print("HTML rodzica pierwszego elementu zawierającego 'Profil':", file=sys.stderr)
                #             print(etree.tostring(parent_element, pretty_print=True, encoding='unicode'), file=sys.stderr)
                #             grandparent = parent_element.getparent()
                #             if grandparent is not None:
                #                 print("\nHTML 'dziadka':", file=sys.stderr)
                #                 print(etree.tostring(grandparent, pretty_print=True, encoding='unicode'), file=sys.stderr)
                #         else:
                #             print("Nie można znaleźć elementu nadrzędnego dla elementu zawierającego 'Profil'.", file=sys.stderr)
                #             print("HTML znalezionego elementu:", file=sys.stderr)
                #             print(etree.tostring(reference_element, pretty_print=True, encoding='unicode'), file=sys.stderr)
                #     else:
                #         print("Nie znaleziono ŻADNEGO elementu zawierającego tekst 'Profil'.", file=sys.stderr)
                #         print(f"Pierwsze 1000 znaków odpowiedzi:\n{response.text[:1000]}\n---", file=sys.stderr)
                # except Exception as debug_e:
                #     print(f"Błąd podczas debugowania HTML: {debug_e}", file=sys.stderr)
                # print("--- Koniec DEBUG --- \n", file=sys.stderr)
                # --- End Optional Debugging Code ---

                return None # Return None as description was not found

        except (etree.ParserError, ValueError) as parse_error:
            # Handle errors during HTML parsing
            print(f"Błąd parsowania HTML (ScrapingBee): {parse_error}", file=sys.stderr)
            # print(f"Cała odpowiedź:\n{response.text}", file=sys.stderr) # Optional
            return None # Return None on parsing error

    except requests.exceptions.RequestException as e:
        # Handle connection errors or bad HTTP statuses from ScrapingBee
        error_detail = str(e)
        try:
             # Try to get a more specific error message from ScrapingBee's JSON response
             if response is not None and response.headers.get('Content-Type') == 'application/json':
                 error_detail = response.json().get('error', str(e))
        except ValueError: # Ignore error if response is not valid JSON
             pass
        print(f"Błąd połączenia przez ScrapingBee dla {target_url}: {error_detail}", file=sys.stderr)
        return None
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Wystąpił nieoczekiwany błąd (ScrapingBee): {e}", file=sys.stderr)
        traceback.print_exc() # Print the full error traceback for debugging
        return None

    # Fallback return
    return description

# --- Script Execution ---
if __name__ == "__main__":
    ticker_symbol = "wod" # Define the ticker symbol to scrape
    print(f"Uruchamianie scrapera dla tickera: {ticker_symbol.upper()}")

    # Call the scraping function
    profile_description = scrape_stooq_profile_with_scrapingbee(ticker_symbol)

    # Print the result
    if profile_description:
        print(f"\nOpis profilu dla {ticker_symbol.upper()} (przez ScrapingBee):\n")
        print(profile_description)
    else:
        print(f"\nNie udało się pobrać opisu profilu dla {ticker_symbol.upper()} (przez ScrapingBee).")
