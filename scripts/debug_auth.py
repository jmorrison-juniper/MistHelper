"""Debug response from requests to check auth."""

import requests
from bs4 import BeautifulSoup

COOKIES = {
    "uvts": "cdb57a9a-9283-4735-591d-d12aecd24055",
    "csrftoken": "OPYOZ99nrHqwQXgBq4CJtttTvfAB73bK",
    "_rf": "0",
    "_gcl_au": "1.1.133409514.1775770705",
    "_uservoice_tz": "America/Chicago",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
s = requests.Session()
s.cookies.update(COOKIES)
s.headers.update(HEADERS)
r = s.get("https://ideas.mist.com/forums/912934-product-features?filter=hot&page=1", timeout=20)
print("Status:", r.status_code)
soup = BeautifulSoup(r.content, "lxml")
titles = [h.get_text(strip=True) for h in soup.select("h1,h2")][:5]
print("H1/H2:", titles)
ideas_list = soup.select('[href*="/suggestions/"]')
print("Suggestion links:", len(ideas_list))
print("First 3:", [a.get("href") for a in ideas_list[:3]])
