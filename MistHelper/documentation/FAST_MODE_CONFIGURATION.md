# Fast Mode Configuration Guide

This document explains how to tune the `--fast` flag performance for Option 16 (Gateway Synthetic Tests) using environment variables in the `.env` file.

## Overview

All hardcoded values for the fast mode implementation have been moved to the `.env` file, allowing you to tune performance parameters without modifying code.

## Configuration Variables

### Core Retry Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_MODE_MAX_RETRIES` | `3` | Maximum number of retry attempts per device in fast mode |
| `FAST_MODE_RETRY_DELAY` | `0.5` | Base delay in seconds between retry attempts |
| `FAST_MODE_BACKOFF_MULTIPLIER` | `1.5` | Exponential backoff multiplier for retries |

**Example retry progression with defaults:** 0.5s → 0.75s → 1.125s

### Threading and Concurrency

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_MODE_DEVICES_PER_THREAD` | `10` | Number of devices to process per thread |
| `FAST_MODE_RETRY_THREADS` | `4` | Maximum number of threads for retrying failed devices |
| `FAST_MODE_FALLBACK_THREADS` | `8` | Fallback thread count if CPU count cannot be determined |

**Batch size calculation:** `max_threads * devices_per_thread`

### Connection Pool Management (NEW)

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | `8` | Maximum concurrent API connections to avoid pool saturation |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | `true` | Use connection-aware threading instead of CPU-based threading |

**Connection pool strategy:** When enabled, limits threads based on connection pool size rather than CPU count to prevent connection pool warnings.

### Mode-Specific Retry Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_MODE_RETRY_MAX_RETRIES` | `2` | Maximum retry attempts for devices that failed in the first batch |
| `FAST_MODE_SEQUENTIAL_MAX_RETRIES` | `1` | Maximum retry attempts in sequential (non-fast) mode |

## Performance Tuning Examples

### Zero Connection Pool Warnings (RECOMMENDED)
```properties
FAST_MODE_USE_CONNECTION_AWARE_THREADING=true
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
FAST_MODE_DEVICES_PER_THREAD=5
FAST_MODE_RETRY_THREADS=2
```

### Maximum Throughput (Aggressive)
```properties
FAST_MODE_USE_CONNECTION_AWARE_THREADING=false
FAST_MODE_MAX_RETRIES=2
FAST_MODE_RETRY_DELAY=0.25
FAST_MODE_BACKOFF_MULTIPLIER=1.2
FAST_MODE_DEVICES_PER_THREAD=15
FAST_MODE_RETRY_THREADS=6
```

### Conservative (Gentle on API)
```properties
FAST_MODE_USE_CONNECTION_AWARE_THREADING=true
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=6
FAST_MODE_MAX_RETRIES=5
FAST_MODE_RETRY_DELAY=1.0
FAST_MODE_BACKOFF_MULTIPLIER=2.0
FAST_MODE_DEVICES_PER_THREAD=3
FAST_MODE_RETRY_THREADS=2
```

### Current Optimized (Default)
```properties
FAST_MODE_USE_CONNECTION_AWARE_THREADING=true
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
FAST_MODE_MAX_RETRIES=3
FAST_MODE_RETRY_DELAY=0.5
FAST_MODE_BACKOFF_MULTIPLIER=1.5
FAST_MODE_DEVICES_PER_THREAD=5
FAST_MODE_RETRY_THREADS=4
```

## How to Apply Changes

1. Edit the `.env` file in the project root
2. Modify the desired variables
3. Save the file
4. Run MistHelper with the `--fast` flag

Changes take effect immediately on the next run - no code restart required.

## Performance Impact

- **Higher `DEVICES_PER_THREAD`**: More devices per batch, higher memory usage
- **Lower `RETRY_DELAY`**: Faster retries, higher API load
- **Higher `RETRY_THREADS`**: More concurrent retries, potential connection pool warnings
- **Higher `MAX_RETRIES`**: More resilient to network issues, slower on persistent failures

## Connection Pool Warnings

### NEW: Connection-Aware Threading

The latest version introduces smart connection pool management to eliminate warnings:

**How it works:**
- **Semaphore Control**: Uses a semaphore to limit concurrent API calls to the configured maximum
- **Connection-Aware Threading**: Limits worker threads based on connection pool size, not CPU count
- **Dynamic Throttling**: Automatically queues requests when connection limit is reached

**To eliminate connection pool warnings:**
```properties
FAST_MODE_USE_CONNECTION_AWARE_THREADING=true
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
```

### Traditional Tuning (if connection-aware mode is disabled)

If you see connection pool warnings, consider:
- Reducing `FAST_MODE_RETRY_THREADS`
- Increasing `FAST_MODE_RETRY_DELAY`
- Reducing `FAST_MODE_DEVICES_PER_THREAD`

These warnings are typically cosmetic and don't indicate data loss.
