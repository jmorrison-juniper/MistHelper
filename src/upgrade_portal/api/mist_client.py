"""Mist API client for listing sites and devices.

Queries Mist API and caches results for 5 minutes per FR-003.
"""

import json  # WHY: JSON serialization for cache
import time  # WHY: cache TTL calculations
from typing import Dict, List, Optional, Any  # WHY: type hints

import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class MistAPIClient:
    """Client for Mist API operations with caching."""

    # WHY: configurable cache duration
    SITES_CACHE_TTL = 300  # WHY: 5 minutes per FR-003
    DEVICES_CACHE_TTL = 300  # WHY: 5 minutes per FR-003

    def __init__(self, mist_api_client=None, redis_cache=None):
        """Initialize Mist API client.

        Args:
            mist_api_client: mistapi.api.* client instance for API calls.
            redis_cache: Redis client for caching (optional).

        WHY: dependency injection for API and cache layers.
        """
        # WHY: store dependencies
        self.mist_api = mist_api_client  # WHY: Mist API client
        self.redis = redis_cache  # WHY: Redis cache
        # WHY: log initialization
        logger.info("mist_api_client_initialized", cache_enabled=redis_cache is not None)  # WHY: startup event

    def list_sites(self, org_id: str) -> Optional[List[Dict[str, Any]]]:
        """List all sites for an organization.

        Args:
            org_id: Organization ID.

        Returns:
            List of site dicts with id, name, country_code, sorted by name.
            Returns None if query fails.

        WHY: get sites list for dropdown selector (T-003).
        """
        # WHY: log operation start
        logger.info("mist_list_sites_start", org_id=org_id)  # WHY: pre-query log
        try:
            # WHY: check cache first
            cache_key = f"sites:{org_id}"  # WHY: cache key format
            if self.redis:  # WHY: if cache enabled
                cached = self._get_cache(cache_key)  # WHY: retrieve from cache
                if cached:  # WHY: if cache hit
                    logger.debug("mist_sites_cache_hit", org_id=org_id)  # WHY: cache hit log
                    return cached  # WHY: return cached result
            # WHY: query Mist API
            if not self.mist_api:  # WHY: check API client
                logger.error("mist_api_client_unavailable")  # WHY: no API client
                return None  # WHY: fail
            # WHY: call Mist API listOrgSites
            try:
                # WHY: example API call structure (adjust based on actual mistapi library)
                sites = self.mist_api.listOrgSites(org_id)  # WHY: API call
            except Exception as e:
                # WHY: API call failed
                logger.error("mist_api_list_sites_failed", org_id=org_id, error=str(e))  # WHY: API error
                return None  # WHY: fail
            # WHY: normalize response
            sites_list = []  # WHY: normalized output
            for site in (sites or []):  # WHY: iterate sites
                # WHY: extract relevant fields
                site_dict = {  # WHY: normalized site dict
                    'id': site.get('id', ''),  # WHY: site ID
                    'name': site.get('name', ''),  # WHY: site name
                    'country_code': site.get('country_code', ''),  # WHY: country
                }  # WHY: site data
                sites_list.append(site_dict)  # WHY: add to list
            # WHY: sort by name
            sites_list.sort(key=lambda x: x['name'])  # WHY: alphabetical sort
            # WHY: cache result
            if self.redis:  # WHY: if cache enabled
                self._set_cache(cache_key, sites_list, self.SITES_CACHE_TTL)  # WHY: cache result
            # WHY: log success
            logger.info("mist_list_sites_success", org_id=org_id, count=len(sites_list))  # WHY: post-query log
            return sites_list  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("mist_list_sites_exception", org_id=org_id, error=str(e))  # WHY: exception log
            return None  # WHY: fail

    def list_site_devices(self, site_id: str, device_type: str = 'all') -> Optional[List[Dict[str, Any]]]:
        """List devices for a site.

        Args:
            site_id: Site ID.
            device_type: Device type filter ('all', 'ap', 'switch', 'gateway').

        Returns:
            List of device dicts with id, name, model, serial, firmware_version.
            Returns None if query fails.

        WHY: get devices list for multi-select (T-003).
        """
        # WHY: log operation start
        logger.info("mist_list_devices_start", site_id=site_id, type=device_type)  # WHY: pre-query log
        try:
            # WHY: check cache first
            cache_key = f"devices:{site_id}:{device_type}"  # WHY: cache key format
            if self.redis:  # WHY: if cache enabled
                cached = self._get_cache(cache_key)  # WHY: retrieve from cache
                if cached:  # WHY: if cache hit
                    logger.debug("mist_devices_cache_hit", site_id=site_id)  # WHY: cache hit log
                    return cached  # WHY: return cached result
            # WHY: query Mist API
            if not self.mist_api:  # WHY: check API client
                logger.error("mist_api_client_unavailable")  # WHY: no API client
                return None  # WHY: fail
            # WHY: call Mist API listSiteDevices
            try:
                # WHY: example API call structure (adjust based on actual mistapi library)
                devices = self.mist_api.listSiteDevices(site_id, type=device_type)  # WHY: API call
            except Exception as e:
                # WHY: API call failed
                logger.error("mist_api_list_devices_failed", site_id=site_id, error=str(e))  # WHY: API error
                return None  # WHY: fail
            # WHY: normalize response
            devices_list = []  # WHY: normalized output
            for device in (devices or []):  # WHY: iterate devices
                # WHY: extract relevant fields
                device_dict = {  # WHY: normalized device dict
                    'id': device.get('id', ''),  # WHY: device ID
                    'name': device.get('name', ''),  # WHY: device name
                    'model': device.get('model', ''),  # WHY: device model
                    'serial': device.get('serial', ''),  # WHY: device serial
                    'firmware_version': device.get('fw_version', ''),  # WHY: running firmware (not configured)
                    'mac': device.get('mac', ''),  # WHY: MAC address
                    'status': device.get('status', 'unknown'),  # WHY: connection status
                }  # WHY: device data
                devices_list.append(device_dict)  # WHY: add to list
            # WHY: cache result
            if self.redis:  # WHY: if cache enabled
                self._set_cache(cache_key, devices_list, self.DEVICES_CACHE_TTL)  # WHY: cache result
            # WHY: log success
            logger.info("mist_list_devices_success", site_id=site_id, count=len(devices_list))  # WHY: post-query log
            return devices_list  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("mist_list_devices_exception", site_id=site_id, error=str(e))  # WHY: exception log
            return None  # WHY: fail

    def _get_cache(self, key: str) -> Optional[List]:
        """Get value from Redis cache.

        Args:
            key: Cache key.

        Returns:
            Cached list or None if not found/expired.

        WHY: helper for cache retrieval with JSON deserialization.
        """
        # WHY: retrieve from Redis
        try:
            if not self.redis:  # WHY: check cache enabled
                return None  # WHY: no cache
            # WHY: get cache value
            value = self.redis.get(key)  # WHY: Redis GET
            if not value:  # WHY: if not found
                return None  # WHY: cache miss
            # WHY: deserialize JSON
            return json.loads(value)  # WHY: deserialize
        except Exception as e:
            # WHY: catch cache errors
            logger.warning("cache_get_failed", key=key, error=str(e))  # WHY: cache error
            return None  # WHY: fail

    def _set_cache(self, key: str, value: List, ttl: int) -> bool:
        """Set value in Redis cache.

        Args:
            key: Cache key.
            value: List value to cache.
            ttl: Time-to-live in seconds.

        Returns:
            True if successful, False otherwise.

        WHY: helper for cache storage with JSON serialization.
        """
        # WHY: store in Redis
        try:
            if not self.redis:  # WHY: check cache enabled
                return False  # WHY: no cache
            # WHY: serialize JSON and set with TTL
            value_json = json.dumps(value)  # WHY: serialize
            self.redis.setex(key, ttl, value_json)  # WHY: Redis SETEX
            return True  # WHY: success
        except Exception as e:
            # WHY: catch cache errors
            logger.warning("cache_set_failed", key=key, error=str(e))  # WHY: cache error
            return False  # WHY: fail
