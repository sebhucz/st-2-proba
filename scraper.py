import requests
from lxml import html, etree # Import etree for specific parsing errors
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5.3.736 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Pobieranie strony: {url}...") # Debug info
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        # --- DEBUG: Sprawdź zawartość odpowiedzi ---
        print(f"Status code: {response.status_code}")
        # print(f"Response headers: {response.headers}") # Opcjonalnie, do dalszej analizy
        print(f"Pierwsze 500 znaków odpowiedzi:\n{response.text[:500]}\n--- Koniec pierwszych 500 znaków ---")
        # ----------------------------------------

        # Sprawdź, czy odpowiedź nie jest pusta przed parsowaniem
        if not response.text or response.text.isspace():
             print(f"Błąd: Otrzymano pustą odpowiedź ze strony {url}", file=sys.stderr)
             return None

        # Parsowanie HTML za pomocą lxml
        try:
            tree = html.fromstring(response.content)
        except (etree.ParserError, ValueError) as parse_error: # Łapanie błędów parsowania
            print(f"Błąd parsowania HTML: {parse_error}", file=sys.stderr)
            # print(f"Cała odpowiedź:\n{response.text}") # Opcjonalnie, pokaż całą odpowiedź przy błędzie parsowania
            return None


        # Użycie XPath do znalezienia opisu
        xpath_expr = "//table[.//b[text()='Profil']]/following-sibling::text()[normalize-space()]"
        description_nodes = tree.xpath(xpath_expr)

        if description_nodes:
            description = " ".join(node.strip() for node in description_nodes).strip()
            if "Źródło:" in description:
                description = description.split("Źródło:")[0].strip()
            return description
        else:
            print(f"Nie znaleziono opisu dla tickera: {ticker} przy użyciu XPath.", file=sys.stderr)
            # --- DEBUG: Pokaż fragment HTML, jeśli XPath zawiedzie ---
            # Spróbuj znaleźć tabelę "Profil" i jej rodzica, aby zobaczyć kontekst
            profile_header = tree.xpath("//b[text()='Profil']")
            if profile_header:
                 parent_td = profile_header[0].xpath("./ancestor::td")
                 if parent_td:
                     print("Fragment HTML wokół nagłówka 'Profil':")
                     print(etree.tostring(parent_td[0], pretty_print=True, encoding='unicode'))
                 else:
                     print("Nie znaleziono rodzica <td> dla nagłówka 'Profil'.")
            else:
                 print("Nie znaleziono nawet nagłówka 'Profil' na stronie.")
            # ----------------------------------------------------
            return None

    except requests.exceptions.RequestException as e:
        print(f"Błąd połączenia ze stroną {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        # Usunięto ogólny handler, aby zobaczyć bardziej szczegółowe błędy
        print(f"Wystąpił nieoczekiwany błąd: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc() # Wydrukuj pełny traceback błędu
        return None

# --- Uruchomienie scrapera ---
if __name__ == "__main__":
    ticker_symbol = "wod"
    profile_description = scrape_stooq_profile(ticker_symbol)

    if profile_description:
        print(f"\nOpis profilu dla {ticker_symbol.upper()}:\n")
        print(profile_description)
    else:
        print(f"\nNie udało się pobrać opisu profilu dla {ticker_symbol.upper()}.")
