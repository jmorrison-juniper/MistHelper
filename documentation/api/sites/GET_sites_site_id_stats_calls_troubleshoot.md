# listSiteTroubleshootCalls

> listSiteTroubleshootCalls

## HTTP

`GET /api/v1/sites/{site_id}/stats/calls/troubleshoot`

## Description

Summary of calls troubleshoot by site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| ap | string | No |  |  | AP MAC |
| meeting_id | string | No |  |  | meeting_id |
| mac | string | No |  |  | Device identifier |
| app | string | No |  |  | Third party app name |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "mac": {
      "type": "string",
      "examples": [
        "983a78ea4a44"
      ]
    },
    "meeting_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "b784d744-9a7c-4fad-9af0-f78858a319b1"
      ]
    },
    "results": {
      "type": "array",
      "items": {
        "title": "call_troubleshoot_summary",
        "type": "object",
        "properties": {
          "ap_num_clients": {
            "type": "number",
            "examples": [
              -0.08802365511655807
            ]
          },
          "ap_rtt": {
            "type": "number",
            "examples": [
              0.09924473613500595
            ]
          },
          "audio_in": {
            "title": "call_troubleshoot_summary_data",
            "type": "object",
            "properties": {
              "ap_num_clients": {
                "type": "number",
                "examples": [
                  -0.6565111
                ]
              },
              "ap_rtt": {
                "type": "number",
                "examples": [
                  0.16559607
                ]
              },
              "client_cpu": {
                "type": "number",
                "examples": [
                  3.7028809
                ]
              },
              "client_n_streams": {
                "type": "number",
                "examples": [
                  0.15803306
                ]
              },
              "client_radio_band": {
                "type": "number",
                "examples": [
                  0.5576923
                ]
              },
              "client_rssi": {
                "type": "number",
                "examples": [
                  -1.0839354
                ]
              },
              "client_rx_bytes": {
                "type": "number",
                "examples": [
                  2.2622051
                ]
              },
              "client_rx_rates": {
                "type": "number",
                "examples": [
                  0.26726437
                ]
              },
              "client_tx_bytes": {
                "type": "number",
                "examples": [
                  6.6164713
                ]
              },
              "client_tx_rates": {
                "type": "number",
                "examples": [
                  0.62357205
                ]
              },
              "client_tx_retries": {
                "type": "number",
                "examples": [
                  1.702031
                ]
              },
              "client_vpn_distance": {
                "type": "number",
                "examples": [
                  1.6474955
                ]
              },
              "client_wifi_version": {
                "type": "number",
                "examples": [
                  0.18267937
                ]
              },
              "expected": {
                "type": "number",
                "examples": [
                  30.941595
                ]
              },
              "radio_bandwidth": {
                "type": "number",
                "examples": [
                  -0.06538621
                ]
              },
              "radio_channel": {
                "type": "number",
                "examples": [
                  -0.73391086
                ]
              },
              "radio_tx_power": {
                "type": "number",
                "examples": [
                  0.10027129
                ]
              },
              "radio_util": {
                "type": "number",
                "examples": [
                  12.770318
                ]
              },
              "radio_util_interference": {
                "type": "number",
                "examples": [
                  -3.079999
                ]
              },
              "site_num_clients": {
                "type": "number",
                "examples": [
                  0.017364305
                ]
              },
              "site_wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  3.0566701889e-07
                ]
              },
              "site_wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  5.566701889e-08
                ]
              },
              "site_wan_download_mbps": {
                "type": "number",
                "examples": [
                  8.0566701889e-07
                ]
              },
              "site_wan_jitter": {
                "type": "number",
                "examples": [
                  0.7875519659784105
                ]
              },
              "site_wan_rtt": {
                "type": "number",
                "examples": [
                  15.094849904378256
                ]
              },
              "site_wan_upload_mbps": {
                "type": "number",
                "examples": [
                  2.0566701889e-07
                ]
              },
              "wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_jitter": {
                "type": "number",
                "examples": [
                  5.9680853
                ]
              },
              "wan_max_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_max_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_rtt": {
                "type": "number",
                "examples": [
                  46.77899
                ]
              }
            }
          },
          "audio_out": {
            "title": "call_troubleshoot_summary_data",
            "type": "object",
            "properties": {
              "ap_num_clients": {
                "type": "number",
                "examples": [
                  -0.6565111
                ]
              },
              "ap_rtt": {
                "type": "number",
                "examples": [
                  0.16559607
                ]
              },
              "client_cpu": {
                "type": "number",
                "examples": [
                  3.7028809
                ]
              },
              "client_n_streams": {
                "type": "number",
                "examples": [
                  0.15803306
                ]
              },
              "client_radio_band": {
                "type": "number",
                "examples": [
                  0.5576923
                ]
              },
              "client_rssi": {
                "type": "number",
                "examples": [
                  -1.0839354
                ]
              },
              "client_rx_bytes": {
                "type": "number",
                "examples": [
                  2.2622051
                ]
              },
              "client_rx_rates": {
                "type": "number",
                "examples": [
                  0.26726437
                ]
              },
              "client_tx_bytes": {
                "type": "number",
                "examples": [
                  6.6164713
                ]
              },
              "client_tx_rates": {
                "type": "number",
                "examples": [
                  0.62357205
                ]
              },
              "client_tx_retries": {
                "type": "number",
                "examples": [
                  1.702031
                ]
              },
              "client_vpn_distance": {
                "type": "number",
                "examples": [
                  1.6474955
                ]
              },
              "client_wifi_version": {
                "type": "number",
                "examples": [
                  0.18267937
                ]
              },
              "expected": {
                "type": "number",
                "examples": [
                  30.941595
                ]
              },
              "radio_bandwidth": {
                "type": "number",
                "examples": [
                  -0.06538621
                ]
              },
              "radio_channel": {
                "type": "number",
                "examples": [
                  -0.73391086
                ]
              },
              "radio_tx_power": {
                "type": "number",
                "examples": [
                  0.10027129
                ]
              },
              "radio_util": {
                "type": "number",
                "examples": [
                  12.770318
                ]
              },
              "radio_util_interference": {
                "type": "number",
                "examples": [
                  -3.079999
                ]
              },
              "site_num_clients": {
                "type": "number",
                "examples": [
                  0.017364305
                ]
              },
              "site_wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  3.0566701889e-07
                ]
              },
              "site_wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  5.566701889e-08
                ]
              },
              "site_wan_download_mbps": {
                "type": "number",
                "examples": [
                  8.0566701889e-07
                ]
              },
              "site_wan_jitter": {
                "type": "number",
                "examples": [
                  0.7875519659784105
                ]
              },
              "site_wan_rtt": {
                "type": "number",
                "examples": [
                  15.094849904378256
                ]
              },
              "site_wan_upload_mbps": {
                "type": "number",
                "examples": [
                  2.0566701889e-07
                ]
              },
              "wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_jitter": {
                "type": "number",
                "examples": [
                  5.9680853
                ]
              },
              "wan_max_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_max_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_rtt": {
                "type": "number",
                "examples": [
                  46.77899
                ]
              }
            }
          },
          "client_cpu": {
            "type": "number",
            "examples": [
              0.00834270566701889
            ]
          },
          "client_n_streams": {
            "type": "number",
            "examples": [
              0.00734270566701889
            ]
          },
          "client_radio_band": {
            "type": "number",
            "examples": [
              0.5841414928436279
            ]
          },
          "client_rssi": {
            "type": "number",
            "examples": [
              0.7594696879386902
            ]
          },
          "client_rx_bytes": {
            "type": "number",
            "examples": [
              2.365511655807e-05
            ]
          },
          "client_rx_rates": {
            "type": "number",
            "examples": [
              0.02441493794322014
            ]
          },
          "client_rx_retries": {
            "type": "number",
            "examples": [
              -0.14325742423534393
            ]
          },
          "client_tx_bytes": {
            "type": "number",
            "examples": [
              0.00102365511655807
            ]
          },
          "client_tx_rates": {
            "type": "number",
            "examples": [
              0.22236637771129608
            ]
          },
          "client_tx_retries": {
            "type": "number",
            "examples": [
              0.3308201730251312
            ]
          },
          "client_vpn_distance": {
            "type": "number",
            "examples": [
              -0.0001660545531194657
            ]
          },
          "client_wifi_version": {
            "type": "number",
            "examples": [
              7.0566701889e-07
            ]
          },
          "expected": {
            "type": "number",
            "examples": [
              -2.8630001056670187
            ]
          },
          "radio_ap_change": {
            "type": "number",
            "examples": [
              0.01850946433842182
            ]
          },
          "radio_bandwidth": {
            "type": "number",
            "examples": [
              -0.021175479516386986
            ]
          },
          "radio_channel": {
            "type": "number",
            "examples": [
              0.11686426401138306
            ]
          },
          "radio_rx_failed": {
            "type": "number",
            "examples": [
              1.1782013177871704
            ]
          },
          "radio_tx_power": {
            "type": "number",
            "examples": [
              0.121039018034935
            ]
          },
          "radio_util": {
            "type": "number",
            "examples": [
              0.2452986091375351
            ]
          },
          "radio_util_interference": {
            "type": "number",
            "examples": [
              3.4367904663085938
            ]
          },
          "site_num_clients": {
            "type": "number",
            "examples": [
              0.055026158690452576
            ]
          },
          "site_wan_avg_download_mbps": {
            "type": "number",
            "examples": [
              3.0566701889e-07
            ]
          },
          "site_wan_avg_upload_mbps": {
            "type": "number",
            "examples": [
              5.566701889e-08
            ]
          },
          "site_wan_download_mbps": {
            "type": "number",
            "examples": [
              8.0566701889e-07
            ]
          },
          "site_wan_jitter": {
            "type": "number",
            "examples": [
              0.7875519659784105
            ]
          },
          "site_wan_rtt": {
            "type": "number",
            "examples": [
              15.094849904378256
            ]
          },
          "site_wan_upload_mbps": {
            "type": "number",
            "examples": [
              2.0566701889e-07
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "video_in": {
            "title": "call_troubleshoot_summary_data",
            "type": "object",
            "properties": {
              "ap_num_clients": {
                "type": "number",
                "examples": [
                  -0.6565111
                ]
              },
              "ap_rtt": {
                "type": "number",
                "examples": [
                  0.16559607
                ]
              },
              "client_cpu": {
                "type": "number",
                "examples": [
                  3.7028809
                ]
              },
              "client_n_streams": {
                "type": "number",
                "examples": [
                  0.15803306
                ]
              },
              "client_radio_band": {
                "type": "number",
                "examples": [
                  0.5576923
                ]
              },
              "client_rssi": {
                "type": "number",
                "examples": [
                  -1.0839354
                ]
              },
              "client_rx_bytes": {
                "type": "number",
                "examples": [
                  2.2622051
                ]
              },
              "client_rx_rates": {
                "type": "number",
                "examples": [
                  0.26726437
                ]
              },
              "client_tx_bytes": {
                "type": "number",
                "examples": [
                  6.6164713
                ]
              },
              "client_tx_rates": {
                "type": "number",
                "examples": [
                  0.62357205
                ]
              },
              "client_tx_retries": {
                "type": "number",
                "examples": [
                  1.702031
                ]
              },
              "client_vpn_distance": {
                "type": "number",
                "examples": [
                  1.6474955
                ]
              },
              "client_wifi_version": {
                "type": "number",
                "examples": [
                  0.18267937
                ]
              },
              "expected": {
                "type": "number",
                "examples": [
                  30.941595
                ]
              },
              "radio_bandwidth": {
                "type": "number",
                "examples": [
                  -0.06538621
                ]
              },
              "radio_channel": {
                "type": "number",
                "examples": [
                  -0.73391086
                ]
              },
              "radio_tx_power": {
                "type": "number",
                "examples": [
                  0.10027129
                ]
              },
              "radio_util": {
                "type": "number",
                "examples": [
                  12.770318
                ]
              },
              "radio_util_interference": {
                "type": "number",
                "examples": [
                  -3.079999
                ]
              },
              "site_num_clients": {
                "type": "number",
                "examples": [
                  0.017364305
                ]
              },
              "site_wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  3.0566701889e-07
                ]
              },
              "site_wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  5.566701889e-08
                ]
              },
              "site_wan_download_mbps": {
                "type": "number",
                "examples": [
                  8.0566701889e-07
                ]
              },
              "site_wan_jitter": {
                "type": "number",
                "examples": [
                  0.7875519659784105
                ]
              },
              "site_wan_rtt": {
                "type": "number",
                "examples": [
                  15.094849904378256
                ]
              },
              "site_wan_upload_mbps": {
                "type": "number",
                "examples": [
                  2.0566701889e-07
                ]
              },
              "wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_jitter": {
                "type": "number",
                "examples": [
                  5.9680853
                ]
              },
              "wan_max_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_max_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_rtt": {
                "type": "number",
                "examples": [
                  46.77899
                ]
              }
            }
          },
          "video_out": {
            "title": "call_troubleshoot_summary_data",
            "type": "object",
            "properties": {
              "ap_num_clients": {
                "type": "number",
                "examples": [
                  -0.6565111
                ]
              },
              "ap_rtt": {
                "type": "number",
                "examples": [
                  0.16559607
                ]
              },
              "client_cpu": {
                "type": "number",
                "examples": [
                  3.7028809
                ]
              },
              "client_n_streams": {
                "type": "number",
                "examples": [
                  0.15803306
                ]
              },
              "client_radio_band": {
                "type": "number",
                "examples": [
                  0.5576923
                ]
              },
              "client_rssi": {
                "type": "number",
                "examples": [
                  -1.0839354
                ]
              },
              "client_rx_bytes": {
                "type": "number",
                "examples": [
                  2.2622051
                ]
              },
              "client_rx_rates": {
                "type": "number",
                "examples": [
                  0.26726437
                ]
              },
              "client_tx_bytes": {
                "type": "number",
                "examples": [
                  6.6164713
                ]
              },
              "client_tx_rates": {
                "type": "number",
                "examples": [
                  0.62357205
                ]
              },
              "client_tx_retries": {
                "type": "number",
                "examples": [
                  1.702031
                ]
              },
              "client_vpn_distance": {
                "type": "number",
                "examples": [
                  1.6474955
                ]
              },
              "client_wifi_version": {
                "type": "number",
                "examples": [
                  0.18267937
                ]
              },
              "expected": {
                "type": "number",
                "examples": [
                  30.941595
                ]
              },
              "radio_bandwidth": {
                "type": "number",
                "examples": [
                  -0.06538621
                ]
              },
              "radio_channel": {
                "type": "number",
                "examples": [
                  -0.73391086
                ]
              },
              "radio_tx_power": {
                "type": "number",
                "examples": [
                  0.10027129
                ]
              },
              "radio_util": {
                "type": "number",
                "examples": [
                  12.770318
                ]
              },
              "radio_util_interference": {
                "type": "number",
                "examples": [
                  -3.079999
                ]
              },
              "site_num_clients": {
                "type": "number",
                "examples": [
                  0.017364305
                ]
              },
              "site_wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  3.0566701889e-07
                ]
              },
              "site_wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  5.566701889e-08
                ]
              },
              "site_wan_download_mbps": {
                "type": "number",
                "examples": [
                  8.0566701889e-07
                ]
              },
              "site_wan_jitter": {
                "type": "number",
                "examples": [
                  0.7875519659784105
                ]
              },
              "site_wan_rtt": {
                "type": "number",
                "examples": [
                  15.094849904378256
                ]
              },
              "site_wan_upload_mbps": {
                "type": "number",
                "examples": [
                  2.0566701889e-07
                ]
              },
              "wan_avg_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_avg_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_jitter": {
                "type": "number",
                "examples": [
                  5.9680853
                ]
              },
              "wan_max_download_mbps": {
                "type": "number",
                "examples": [
                  1.4803165
                ]
              },
              "wan_max_upload_mbps": {
                "type": "number",
                "examples": [
                  -0.038184267
                ]
              },
              "wan_rtt": {
                "type": "number",
                "examples": [
                  46.77899
                ]
              }
            }
          }
        }
      },
      "description": ""
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Syntax |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.stats_-_calls.listSiteTroubleshootCalls()`

## Usage Context

Provides troubleshooting data for calls at a site, including roaming events and RF conditions during the call.

## Gotchas

- Troubleshooting data is retained for a limited window (typically 7 days).

## Related Endpoints

- [GET_sites_site_id_stats_calls_client_client_mac_troubleshoot.md](GET_sites_site_id_stats_calls_client_client_mac_troubleshoot.md) — Per-client troubleshoot
- [GET_sites_site_id_stats_calls_search.md](GET_sites_site_id_stats_calls_search.md) — Search calls

## MistHelper Notes

Not currently used by MistHelper directly.
