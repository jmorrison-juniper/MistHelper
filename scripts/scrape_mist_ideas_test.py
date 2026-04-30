"""
Test script to verify HTML structure of Mist Ideas forum before full scraping run.
"""

import requests
from bs4 import BeautifulSoup

# Session cookies extracted from authenticated VS Code browser session
COOKIES = {
    '_rf': '0',
    '_gcl_au': '1.1.133409514.1775770705',
    '_uservoice_tz': 'America/Chicago',
    '_gid': 'GA1.2.428903107.1775770707',
    'uvts': 'cdb57a9a-9283-4735-591d-d12aecd24055',
    'csrftoken': 'OPYOZ99nrHqwQXgBq4CJtttTvfAB73bK',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://ideas.mist.com',
}

BASE_URL = 'https://ideas.mist.com'

session = requests.Session()
session.cookies.update(COOKIES)
session.headers.update(HEADERS)


def test_list_page():
    """Test scraping the list page."""
    url = f'{BASE_URL}/forums/912934-product-features?filter=hot&page=1'
    print(f"Fetching list page: {url}")
    response = session.get(url, timeout=30)
    print(f"Status: {response.status_code}")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all idea links
    idea_links = []
    seen = set()
    for anchor in soup.select('a[href*="/suggestions/"]'):
        href = anchor.get('href', '')
        if '#comments' not in href and href not in seen:
            seen.add(href)
            idea_links.append(BASE_URL + href if href.startswith('/') else href)

    print(f"Found {len(idea_links)} idea links on page 1")
    for link in idea_links[:5]:
        print(f"  - {link}")

    # Check pagination
    next_link = soup.select_one('a[rel="next"]')
    last_page = None
    for anchor in soup.select('a[href*="page="]'):
        try:
            page_num = int(anchor.get('href', '').split('page=')[-1])
            if last_page is None or page_num > last_page:
                last_page = page_num
        except ValueError:
            pass
    print(f"Last page number found: {last_page}")
    print(f"Next page link: {next_link}")

    return idea_links


def test_idea_page(url):
    """Test scraping an individual idea page."""
    print(f"\nFetching idea page: {url}")
    response = session.get(url, timeout=30)
    print(f"Status: {response.status_code}")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Title
    title_el = soup.select_one('h1.uvIdeaTitle, .uvIdeaTitle')
    title = title_el.get_text(strip=True) if title_el else ''
    print(f"Title: {title}")

    # Description
    desc_el = soup.select_one('.uvIdeaDescription .typeset, .uvIdeaDescription')
    description = desc_el.get_text(strip=True) if desc_el else ''
    print(f"Description: {description[:100]}...")

    # Votes
    votes_el = soup.select_one('.uvIdeaVoteCount strong')
    votes = votes_el.get_text(strip=True) if votes_el else ''
    print(f"Votes: {votes}")

    # Status
    status_el = soup.select_one('.uvStatus-name, .uvIdeaStatus, [class*="status-name"], .uvStatus')
    status = status_el.get_text(strip=True) if status_el else ''
    print(f"Status: '{status}'")

    # Look for status in any span/div with "status" class
    all_status = [el.get_text(strip=True) for el in soup.select('[class*="status"]')]
    print(f"All status elements: {all_status[:5]}")

    # Category
    cat_el = soup.select_one('a[href*="/category/"]')
    category = cat_el.get_text(strip=True) if cat_el else ''
    print(f"Category: {category}")

    # Comments - check if they're in the initial HTML
    comment_els = soup.select('.uvComment, .uvComments-comment, [class*="uvComment"]')
    print(f"Comment elements found: {len(comment_els)}")

    # Print first comment HTML if any
    if comment_els:
        print(f"First comment HTML snippet: {str(comment_els[0])[:300]}")

    # Submitter/creator
    submitter_el = soup.select_one('.uvComments-comment-creatorName, .uvIdeaSubmitter, [class*="submitter"]')
    submitter = submitter_el.get_text(strip=True) if submitter_el else ''
    print(f"Submitter: {submitter}")

    # Date
    date_el = soup.select_one('time, [datetime]')
    date = date_el.get('datetime') or date_el.get_text(strip=True) if date_el else ''
    print(f"Date: {date}")

    # Print full HTML around comments area to understand structure
    comments_section = soup.select_one('.uvIdeaComments, #comments, [class*="comments"]')
    if comments_section:
        print("\nComments section HTML (first 1000 chars):")
        print(str(comments_section)[:1000])
    else:
        print("No comments section found in HTML")

    return {
        'title': title,
        'description': description,
        'votes': votes,
        'status': status,
        'category': category,
        'comment_count': len(comment_els),
    }


if __name__ == '__main__':
    print("=== Testing List Page ===")
    links = test_list_page()

    if links:
        print("\n=== Testing Individual Idea Page ===")
        # Test with the dark mode idea (known to have 10 comments)
        test_idea_page('https://ideas.mist.com/forums/912934-product-features/suggestions/49785359-add-dark-mode-to-mist-gui')
