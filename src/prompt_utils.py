"""Prompt utilities (selection helpers) - lightweight scaffold.

This provides a minimal select_site_with_logging and select_site_id_from_csv
implementation suitable for tests and incremental improvements.
"""
from typing import Callable, Optional, List, Dict
from src.utils.input_utils import InputUtils
from src.cache.site_cache import SiteCache
from src.utils.prompt_logging import get_prompt_logger, log_prompt_event


def select_site_with_logging(sites_source: Callable[[], List[Dict]], cache: SiteCache, page_size: int = 50, interactive: bool = True, logger=None) -> Optional[str]:
    logger = logger or get_prompt_logger()
    key = "all_sites"
    sites = cache.get(key, fetcher=sites_source)
    if not sites:
        logger.warn("No sites available")
        return None
    age = cache.age_seconds(key)
    header = f"Sites (cached {int(age)}s ago)" if age is not None else "Sites"
    logger.info(header)
    # show first page
    for idx, s in enumerate(sites[:page_size], start=1):
        print(f"{idx}. {s.get('name','<no-name>')} ({s.get('id')})")
    prompt = "Enter site index or name (or 'r' refresh, 'c' cancel): "
    ans = InputUtils.safe_input(prompt, interactive=interactive)
    if not ans:
        return None
    if ans.lower() == 'c':
        log_prompt_event(logger, 'user_action', {'action': 'cancel'})
        return None
    if ans.lower() == 'r':
        cache.force_refresh(key)
        sites = cache.get(key, force_refresh=True, fetcher=sites_source)
    # numeric index
    if ans.isdigit():
        i = int(ans) - 1
        if 0 <= i < len(sites):
            return sites[i]['id']
    # substring match
    matches = [s for s in sites if ans.lower() in s.get('name','').lower()]
    if len(matches) == 1:
        return matches[0]['id']
    if len(matches) > 1:
        for j, s in enumerate(matches[:10], start=1):
            print(f"{j}. {s.get('name')} ({s.get('id')})")
        choice = InputUtils.safe_input('Select index: ', interactive=interactive)
        if choice and choice.isdigit():
            k = int(choice) - 1
            if 0 <= k < len(matches):
                return matches[k]['id']
    return None


def select_site_id_from_csv(csv_path: str, name_hint: Optional[str] = None, interactive: bool = True, logger=None) -> Optional[str]:
    """Lightweight placeholder: read CSV and prompt user (not implemented here).

    Replace with the project's CSV loading utility in production.
    """
    logger = logger or get_prompt_logger()
    logger.info(f"select_site_id_from_csv called for {csv_path}")
    # For scaffolding purposes return None
    return None
