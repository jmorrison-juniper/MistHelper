"""Quick test: does ideas.mist.com do SSR?"""

import ssl
import urllib.request

url = "https://ideas.mist.com/forums/912934-product-features/suggestions/50598263-modify-port-configuration-button"
req = urllib.request.Request(
    url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
ctx = ssl.create_default_context()  # Verify the certificate and the host name. See issue #1914.
resp = urllib.request.urlopen(req, context=ctx, timeout=30)  # nosec B310 -- fixed https URL above.
html = resp.read().decode("utf-8")
print(f"HTML length: {len(html)}")

# Check for key class names
for cls in ["uvIdeaTitle", "uvIdeaDescription", "uvIdeaVoteCount", "uvStyle-status"]:
    found = cls in html
    print(f"{cls} in HTML: {found}")

# Check for JSON data in script tags
json_count = html.count("application/json")
print(f"application/json count: {json_count}")

# Check if it is a SPA shell or has real content
has_content = "Modify Port" in html or "modify port" in html.lower()
print(f"Contains 'Modify Port': {has_content}")

# Check for __NEXT_DATA__ or similar SSR payloads
for marker in ["__NEXT_DATA__", "__APP_DATA__", "window.__data", "preloadedState"]:
    print(f"{marker}: {marker in html}")

# Print first 3000 chars
print("\n=== FIRST 3000 CHARS ===")
print(html[:3000])
