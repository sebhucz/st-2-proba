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
        print(f"Pobieranie strony przez ScrapingBee: {target_url}...")
        # Make the request to ScrapingBee API
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': SCRAPINGBEE_API_KEY,
                'url': target_url,
                # Optional parameters (uncomment if needed):
                # 'render_js': 'false', # Default is false. Set to 'true' if the page needs JavaScript rendering.
                # 'premium_proxy': 'true', # Use residential proxies if needed (higher cost).
                # 'block_resources': 'false' # Set to 'true' to block CSS/images for faster loading (if not needed).
            },
            timeout=60 # Increased timeout for potential proxy delays
        )
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        print(f"Status code (ScrapingBee): {response.status_code}")
        # Uncomment the line below for more detailed debugging if needed
        # print(f"Pierwsze 500 znaków odpowiedzi (ScrapingBee):\n{response.text[:500]}\n--- Koniec pierwszych 500 znaków ---")

        # Check if the response text is empty or only whitespace
        if not response.text or response.text.isspace():
             print(f"Błąd: Otrzymano pustą odpowiedź z ScrapingBee dla {target_url}", file=sys.stderr)
             return None

        # --- 👇 Poprawiony blok try/except dla parsowania 👇 ---
        try:
            # Parse the HTML content using lxml
            tree = html.fromstring(response.text)

            # Define the XPath expression to find the description
            xpath_expr = "//table[.//b[text()='Profil']]/following-sibling::div[1]/following-sibling::text()[normalize-space()]"
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
                print(f"Nie znaleziono opisu dla tickera: {ticker} przy użyciu XPath (ScrapingBee).", file=sys.stderr)

                # --- Optional HTML Debugging Code ---
                # Uncomment this section if you need to inspect the HTML structure when XPath fails
                print("\n--- DEBUG: Sprawdzanie struktury HTML wokół nagłówka 'Profil' ---", file=sys.stderr)
                try:
                     profile_table = tree.xpath("//table[.//b[text()='Profil']]")
                     if profile_table:
                         parent_element = profile_table[0].getparent()
                         if parent_element is not None:
                             print("HTML rodzica tabeli 'Profil':", file=sys.stderr)
                             print(etree.tostring(parent_element, pretty_print=True, encoding='unicode'), file=sys.stderr)
                         else:
                             print("Nie można znaleźć elementu nadrzędnego dla tabeli 'Profil'.", file=sys.stderr)
                     else:
                         print("Nie znaleziono nawet tabeli zawierającej nagłówek 'Profil'.", file=sys.stderr)
                 except Exception as debug_e:
                     print(f"Błąd podczas debugowania HTML: {debug_e}", file=sys.stderr)
                 print("--- Koniec DEBUG --- \n", file=sys.stderr)
                # --- End Optional Debugging Code ---

                return None # Return None as description was not found

        except (etree.ParserError, ValueError) as parse_error:
            # Handle errors during HTML parsing
            print(f"Błąd parsowania HTML (ScrapingBee): {parse_error}", file=sys.stderr)
            # Uncomment to print the full response text if parsing fails
            # print(f"Cała odpowiedź:\n{response.text}", file=sys.stderr)
            return None # Return None on parsing error
        # --- 👆 Koniec poprawionego bloku 👆 ---

    except requests.exceptions.RequestException as e:
        # Handle connection errors or bad HTTP statuses from ScrapingBee
        error_detail = str(e)
        try:
             # Try to get a more specific error message from ScrapingBee's JSON response
             # Check if 'response' exists before accessing it
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

    # This return should ideally not be reached due to returns inside the try block,
    # but kept as a safeguard.
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
