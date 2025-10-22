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


        xpath_expr = "//table[.//b[text()='Profil']]/following-sibling::text()[normalize-space()]"
        description_nodes = tree.xpath(xpath_expr)

        if description_nodes:
            description = " ".join(node.strip() for node in description_nodes).strip()
            if "Źródło:" in description:
                description = description.split("Źródło:")[0].strip()
            return description
        else:
            print(f"Nie znaleziono opisu dla tickera: {ticker} przy użyciu XPath (ScrapingBee).", file=sys.stderr)

            # --- 👇👇👇 DODANY KOD DEBUGUJĄCY 👇👇👇 ---
            print("\n--- DEBUG: Sprawdzanie struktury HTML wokół nagłówka 'Profil' ---", file=sys.stderr)
            try:
                # Spróbuj znaleźć tabelę "Profil"
                profile_table = tree.xpath("//table[.//b[text()='Profil']]")
                if profile_table:
                    parent_element = profile_table[0].getparent() # Pobierz rodzica tabeli (prawdopodobnie <td>)
                    if parent_element is not None:
                        # Wydrukuj kod HTML rodzica, żeby zobaczyć co jest obok tabeli
                        print("HTML rodzica tabeli 'Profil':", file=sys.stderr)
                        print(etree.tostring(parent_element, pretty_print=True, encoding='unicode'), file=sys.stderr)
                    else:
                        print("Nie można znaleźć elementu nadrzędnego dla tabeli 'Profil'.", file=sys.stderr)
                else:
                    print("Nie znaleziono nawet tabeli zawierającej nagłówek 'Profil'.", file=sys.stderr)
            except Exception as debug_e:
                print(f"Błąd podczas debugowania HTML: {debug_e}", file=sys.stderr)
            print("--- Koniec DEBUG --- \n", file=sys.stderr)
            # --- 👆👆👆 KONIEC DODANEGO KODU 👆👆👆 ---
            return None

# ... (reszta funkcji i bloku if __name__ == "__main__" bez zmian) ...

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
