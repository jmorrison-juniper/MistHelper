# updateOrgSettings

> updateOrgSettings

## HTTP

`PUT /api/v1/orgs/{org_id}/setting`

## Description

Update Org Settings

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "allow_mist": {
      "type": "boolean",
      "description": "whether to allow Mist to look at this org",
      "default": false
    },
    "ap_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for AP devices only. When configured it takes effect for AP devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0
    },
    "api_policy": {
      "title": "org_setting_api_policy",
      "type": "object",
      "properties": {
        "no_reveal": {
          "type": "boolean",
          "description": "By default, API hides password/secrets when the user doesn't have write access\n  * `true`: API will hide passwords/secrets for all users\n  * `false`: API will hide passwords/secrets for read-only users",
          "default": false
        }
      }
    },
    "auto_device_naming": {
      "title": "org_setting_auto_device_naming",
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "title": "org_setting_auto_device_naming_rule",
            "type": "object",
            "properties": {
              "expression": {
                "type": "string",
                "description": "\"[0:3]\"            // \"abcdef\" -> \"abc\"  \n      \"split(.)[1]\"      // \"a.b.c\" -> \"b\"  \n      \"split(-)[1][0:3]\" // \"a1234-b5678-c90\" -> \"b56\"'",
                "examples": [
                  "split(.)[1]"
                ]
              },
              "match_device": {
                "type": "string",
                "description": "enum: `ap`, `gateway`, `switch`"
              },
              "prefix": {
                "type": "string",
                "description": "Prefix to append to the device name"
              },
              "src": {
                "type": "string",
                "description": "enum: `lldp_port_desc`, `mac`"
              },
              "suffix": {
                "type": "string",
                "description": "Suffix to append to the device name"
              }
            }
          },
          "description": ""
        }
      }
    },
    "auto_deviceprofile_assignment": {
      "title": "org_setting_auto_deviceprofile_assignment",
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "title": "org_setting_auto_assignment_rule",
            "required": [
              "src"
            ],
            "type": "object",
            "properties": {
              "create_new_site_if_needed": {
                "type": "boolean",
                "description": "If `src`==`geoip`. By default, a claimed device only gets assigned if the site exists to auto-create the site, enable this",
                "default": false
              },
              "expression": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`, `src`==`lldp_system_name`,  `src`==`dns_suffix`  \n      \"[0:3]\"            // \"abcdef\" -> \"abc\"  \n      \"split(.)[1]\"      // \"a.b.c\" -> \"b\"  \n      \"split(-)[1][0:3]\" // \"a1234-b5678-c90\" -> \"b56\"'",
                "examples": [
                  "split(.)[1]"
                ]
              },
              "gatewaytemplate_id": {
                "type": "string",
                "description": "If `src`==`geoip` and `create_new_site_if_needed`==`true`. If a gateway template is desired for this newly created site"
              },
              "match_country": {
                "type": "string",
                "description": "If `src`==`geoip`"
              },
              "match_device_type": {
                "type": "string",
                "description": "enum: `ap`, `gateway`, `switch`"
              },
              "match_model": {
                "type": "string",
                "description": "Optional/additional filter"
              },
              "model": {
                "type": "string",
                "description": "If `src`==`model`"
              },
              "prefix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "XX-"
                ]
              },
              "src": {
                "type": "string",
                "description": "enum: `ext_ip`, `dns_suffix`, `geoip`, `lldp_port_desc`, `lldp_system_name`, `model`, `name`, `subnet`"
              },
              "subnet": {
                "type": "string",
                "description": "If `src`==`subnet` or `ext_ip`==`ext_ip`"
              },
              "suffix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "-YY"
                ]
              },
              "value": {
                "type": "string",
                "description": "If \n  * `src`==`ext_ip`, `src`==`subnet` or `src`==`model`, the site name\n  * `src`==`geoip`: site name for the device to be assigned to (\\\"city\\\" / \\\"city+country\\\" / ...)\""
              }
            },
            "description": "Auto_rules in org settings"
          },
          "description": ""
        }
      }
    },
    "auto_site_assignment": {
      "title": "org_setting_auto_site_assignment",
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "title": "org_setting_auto_assignment_rule",
            "required": [
              "src"
            ],
            "type": "object",
            "properties": {
              "create_new_site_if_needed": {
                "type": "boolean",
                "description": "If `src`==`geoip`. By default, a claimed device only gets assigned if the site exists to auto-create the site, enable this",
                "default": false
              },
              "expression": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`, `src`==`lldp_system_name`,  `src`==`dns_suffix`  \n      \"[0:3]\"            // \"abcdef\" -> \"abc\"  \n      \"split(.)[1]\"      // \"a.b.c\" -> \"b\"  \n      \"split(-)[1][0:3]\" // \"a1234-b5678-c90\" -> \"b56\"'",
                "examples": [
                  "split(.)[1]"
                ]
              },
              "gatewaytemplate_id": {
                "type": "string",
                "description": "If `src`==`geoip` and `create_new_site_if_needed`==`true`. If a gateway template is desired for this newly created site"
              },
              "match_country": {
                "type": "string",
                "description": "If `src`==`geoip`"
              },
              "match_device_type": {
                "type": "string",
                "description": "enum: `ap`, `gateway`, `switch`"
              },
              "match_model": {
                "type": "string",
                "description": "Optional/additional filter"
              },
              "model": {
                "type": "string",
                "description": "If `src`==`model`"
              },
              "prefix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "XX-"
                ]
              },
              "src": {
                "type": "string",
                "description": "enum: `ext_ip`, `dns_suffix`, `geoip`, `lldp_port_desc`, `lldp_system_name`, `model`, `name`, `subnet`"
              },
              "subnet": {
                "type": "string",
                "description": "If `src`==`subnet` or `ext_ip`==`ext_ip`"
              },
              "suffix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "-YY"
                ]
              },
              "value": {
                "type": "string",
                "description": "If \n  * `src`==`ext_ip`, `src`==`subnet` or `src`==`model`, the site name\n  * `src`==`geoip`: site name for the device to be assigned to (\\\"city\\\" / \\\"city+country\\\" / ...)\""
              }
            },
            "description": "Auto_rules in org settings"
          },
          "description": ""
        }
      }
    },
    "blacklist_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/blacklist/xxx..."
      ]
    },
    "cacerts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "RADSec certificates for AP"
    },
    "celona": {
      "title": "org_setting_celona",
      "type": "object",
      "properties": {
        "api_key": {
          "type": "string",
          "examples": [
            "$2a$04$OkaLCoJn6rDjR8ha.oduQVDST3.kJNIrte"
          ]
        },
        "api_prefix": {
          "type": "string",
          "examples": [
            "cc3273fcb016470e"
          ]
        }
      }
    },
    "cloudshark": {
      "title": "org_setting_cloudshark",
      "type": "object",
      "properties": {
        "apitoken": {
          "type": "string",
          "examples": [
            "accbd6f10c6d05c3"
          ]
        },
        "url": {
          "type": "string",
          "description": "If using CS Enterprise",
          "examples": [
            "https://cloudshark.hosted.domain"
          ]
        }
      }
    },
    "cradlepoint": {
      "type": "object",
      "properties": {
        "cp_api_id": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "84446d61-2206-4ea5-855a-0043f980be54"
          ]
        },
        "cp_api_key": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "79c329da9893e34099c7d8ad5cb9c941"
          ]
        },
        "ecm_api_id": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "73446d61-2206-4ea5-855a-0043f980be62"
          ]
        },
        "ecm_api_key": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "68b329da9893e34099c7d8ad5cb9c940"
          ]
        },
        "enable_lldp": {
          "type": "boolean",
          "readOnly": true
        }
      },
      "readOnly": true
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "device_cert": {
      "type": "object",
      "properties": {
        "cert": {
          "type": "string",
          "examples": [
            "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
          ]
        },
        "key": {
          "type": "string",
          "examples": [
            "-----BEGIN PRI..."
          ]
        }
      },
      "description": "common device cert, optional"
    },
    "device_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery via\n  * device-updowns webhooks topic, \n  * Mist Alert Framework; e.g. send AP/SW/GW down event only if AP/SW/GW Up is not seen within the threshold in minutes; 0 - 240, default is 0 (trigger immediate)",
      "contentEncoding": "int32",
      "default": 0
    },
    "disable_pcap": {
      "type": "boolean",
      "description": "Whether to disallow Mist to analyze pcap files (this is required for marvis pcap)",
      "default": false
    },
    "disable_remote_shell": {
      "type": "boolean",
      "description": "Whether to disable remote shell access for an entire org",
      "default": false
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "gateway_mgmt": {
      "title": "org_setting_gateway_mgmt",
      "type": "object",
      "properties": {
        "app_probing": {
          "title": "org_setting_gateway_mgmt_app_probing",
          "type": "object",
          "properties": {
            "apps": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "APp-keys from [List Applications]($e/Constants%20Definitions/listApplications)",
              "examples": [
                [
                  "facebook"
                ]
              ]
            }
          }
        },
        "app_usage": {
          "type": "boolean",
          "description": "consumes uplink bandwidth, requires WA license"
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "host_in_policies": {
          "title": "org_setting_gateway_mgmt_host_in_policies",
          "type": "object",
          "properties": {
            "icmp": {
              "title": "org_setting_gateway_mgmt_host_in_policy",
              "type": "object",
              "properties": {
                "tenants": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                }
              }
            },
            "snmp": {
              "title": "org_setting_gateway_mgmt_host_in_policy",
              "type": "object",
              "properties": {
                "tenants": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                }
              }
            }
          }
        },
        "host_out_policies": {
          "type": "object",
          "properties": {
            "dns": {
              "title": "gateway_mgmt_host_out_policy",
              "type": "object",
              "properties": {
                "path_preference": {
                  "type": "string"
                }
              }
            },
            "ntp": {
              "title": "gateway_mgmt_host_out_policy",
              "type": "object",
              "properties": {
                "path_preference": {
                  "type": "string"
                }
              }
            },
            "syslog": {
              "title": "gateway_mgmt_host_out_policy_syslog",
              "type": "object",
              "properties": {
                "path_preference": {
                  "type": "string",
                  "examples": [
                    "broadband_wans"
                  ]
                },
                "servers": {
                  "type": "array",
                  "items": {
                    "title": "gateway_mgmt_host_out_policy_syslog_server",
                    "type": "object",
                    "properties": {
                      "host": {
                        "type": "string",
                        "examples": [
                          "103.35.3.5"
                        ]
                      },
                      "path_preference": {
                        "type": "string",
                        "examples": [
                          "dc_only"
                        ]
                      },
                      "server_name": {
                        "type": "string",
                        "examples": [
                          "dc_syslog_server"
                        ]
                      }
                    },
                    "description": "Allows to define the host_out_policy per Syslog Server. The Property key is the Syslog name"
                  },
                  "description": ""
                }
              }
            }
          },
          "description": "optional, for some of the host-out traffic, the path preference can be specified by default, ECMP will be used from all available route/path available services: dns/mist/ntp/pim"
        },
        "overlay_ip": {
          "title": "org_setting_gateway_mgmt_overlay_ip",
          "type": "object",
          "properties": {
            "ip": {
              "type": "string",
              "description": "When it's going overlay, a routable IP to overlay will be required"
            },
            "node1_ip": {
              "type": "string",
              "description": "For SSR HA cluster, another IP for node1 will be required, too"
            }
          }
        }
      }
    },
    "gateway_tunnel_updown_threshold": {
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "enable threshold-based gateway tunnel (secure edge tunnels) up-down delivery.",
      "contentEncoding": "int32"
    },
    "gateway_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for Gateway devices only. When configured it takes effect for GW devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        10
      ]
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "installer": {
      "title": "org_setting_installer",
      "type": "object",
      "properties": {
        "allow_all_devices": {
          "type": "boolean"
        },
        "allow_all_sites": {
          "type": "boolean"
        },
        "extra_site_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": ""
        },
        "grace_period": {
          "type": "integer",
          "contentEncoding": "int32"
        }
      }
    },
    "jcloud": {
      "title": "org_setting_jcloud",
      "type": "object",
      "properties": {
        "org_apitoken": {
          "type": "string",
          "description": "JCloud Org Token"
        },
        "org_apitoken_name": {
          "type": "string",
          "description": "JCloud Org Token Name"
        },
        "org_id": {
          "type": "string",
          "description": "JCloud Org ID"
        }
      }
    },
    "jcloud_ra": {
      "type": "object",
      "properties": {
        "org_apitoken": {
          "type": "string",
          "description": "JCloud Routing Assurance Org Token"
        },
        "org_apitoken_name": {
          "type": "string",
          "description": "JCloud Routing Assurance Org Token Name"
        },
        "org_id": {
          "type": "string",
          "description": "JCloud Routing Assurance Org ID"
        }
      },
      "description": "JCloud Routing Assurance connexion"
    },
    "juniper": {
      "title": "account_juniper_info",
      "type": "object",
      "properties": {
        "accounts": {
          "type": "array",
          "items": {
            "title": "juniper_account",
            "type": "object",
            "properties": {
              "linked_by": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "John Smith (john@abccorp.com)"
                ]
              },
              "name": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "ABC Corp"
                ]
              }
            }
          },
          "description": ""
        }
      }
    },
    "juniper_srx": {
      "title": "org_setting_juniper_srx",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "type": "object",
          "properties": {
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Property key is the SRX Hardware model (e.g. \"SRX4600\")"
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "snapshot": {
              "type": "boolean",
              "default": false
            },
            "version": {
              "type": "string",
              "description": "Firmware version to deploy (e.g. 23.4R2-S5.5). Optional, used when custom_versions not specified",
              "examples": [
                "23.4R2-S5.5"
              ]
            }
          },
          "description": "auto_upgrade device first time it is onboarded"
        }
      }
    },
    "junos_shell_access": {
      "type": "object",
      "properties": {
        "admin": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        },
        "helpdesk": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        },
        "read": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        },
        "write": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        }
      },
      "description": "junos_shell_access: Manages role-based web-shell access.  \nWhen junos_shell access is not defined (Default) - No additional users are configured and web-shell uses default `mist` user to login.  \nWhen junos_shell_access is defined - Additional users mist-web-admin (admin permission), mist-web-viewer(viewer permission) are configured on the device and web-shell logs in with the mist-web-admin/mist-web-viewer user depending upon the shell access level. Setting the shell access level to \"none\", disables web-shell access for that specific role."
    },
    "marvis": {
      "title": "marvis",
      "type": "object",
      "properties": {
        "auto_operations": {
          "title": "marvis_auto_operations",
          "type": "object",
          "properties": {
            "ap_insufficient_capacity": {
              "type": "boolean",
              "default": false
            },
            "ap_loop": {
              "type": "boolean",
              "default": false
            },
            "ap_non_compliant": {
              "type": "boolean",
              "default": false
            },
            "bounce_port_for_abnormal_poe_client": {
              "type": "boolean",
              "default": false
            },
            "disable_port_when_ddos_protocol_violation": {
              "type": "boolean",
              "default": false
            },
            "disable_port_when_rogue_dhcp_server_detected": {
              "type": "boolean",
              "default": false
            },
            "gateway_non_compliant": {
              "type": "boolean",
              "default": false
            },
            "switch_misconfigured_port": {
              "type": "boolean",
              "default": false
            },
            "switch_port_stuck": {
              "type": "boolean",
              "default": false
            }
          }
        }
      }
    },
    "mgmt": {
      "type": "object",
      "properties": {
        "mxtunnel_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of Mist Tunnels"
        },
        "use_mxtunnel": {
          "type": "boolean",
          "description": "Whether to use Mist Tunnel for mgmt connectivity, this takes precedence over use_wxtunnel",
          "default": false
        },
        "use_wxtunnel": {
          "type": "boolean",
          "description": "Whether to use wxtunnel for mgmt connectivity",
          "default": false
        }
      },
      "description": "management-related properties"
    },
    "mist_nac": {
      "title": "org_setting_mist_nac",
      "type": "object",
      "properties": {
        "cacerts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of PEM-encoded ca certs"
        },
        "default_idp_id": {
          "type": "string",
          "description": "use this IDP when no explicit realm present in the incoming username/CN OR when no IDP is explicitly mapped to the incoming realm."
        },
        "disable_rsae_algorithms": {
          "type": "boolean",
          "description": "to disable RSAE_PSS_SHA256, RSAE_PSS_SHA384, RSAE_PSS_SHA512 from server side. see https://www.openssl.org/docs/man3.0/man1/openssl-ciphers.html",
          "default": false
        },
        "eap_ssl_security_level": {
          "maximum": 4.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "eap ssl security level, see https://www.openssl.org/docs/man1.1.1/man3/SSL_CTX_set_security_level.html#DEFAULT-CALLBACK-BEHAVIOUR",
          "contentEncoding": "int32",
          "default": 2
        },
        "eu_only": {
          "type": "boolean",
          "description": "By default, NAC POD failover considers all NAC pods available around the globe, i.e. EU, US, or APAC based, failover happens based on geo IP of the originating site. For strict GDPR compliance NAC POD failover would only happen between the PODs located within the EU environment, and no authentication would take place outside of EU. This is an org setting that is applicable to WLANs, switch templates, mxedge clusters that have mist_nac enabled",
          "default": false
        },
        "fingerprinting": {
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean",
              "description": "enable/disable writes to NAC DDB fingerprint table",
              "default": false
            },
            "generate_coa": {
              "type": "boolean",
              "description": "enable/disable CoA triggers on fingerprint change for wired clients, always port-bounce",
              "default": false
            },
            "generate_wireless_coa": {
              "type": "boolean",
              "description": "enable/disable CoA triggers on fingerprint change for wireless clients",
              "default": false
            },
            "wireless_coa_type": {
              "type": "string",
              "description": "enum: `reauth`, `disconnect`"
            }
          },
          "description": "Allows customer to enable client fingerprinting for policy enforcement"
        },
        "idp_machine_cert_lookup_field": {
          "type": "string",
          "description": "allow customer to choose the EAP-TLS client certificate's field to use for IDP Machine Groups lookup. enum: `automatic`, `cn`, `dns`"
        },
        "idp_user_cert_lookup_field": {
          "type": "string",
          "description": "allow customer to choose the EAP-TLS client certificate's field. To use for IDP User Groups lookup. enum: `automatic`, `cn`, `email`, `upn`"
        },
        "idps": {
          "type": "array",
          "items": {
            "title": "org_setting_mist_nac_idp",
            "type": "object",
            "properties": {
              "exclude_realms": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "When the IDP of mxedge_proxy type, exclude the following realms from proxying in addition to other valid home realms in this org"
              },
              "id": {
                "type": "string",
                "description": "Unique ID of the object instance in the Mist Organization",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "53f10664-3ce8-4c27-b382-0ef66432349f"
                ]
              },
              "user_realms": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Which realm should trigger this IDP. User Realm is extracted from:\n  * Username-AVP (`mist.com` from john@mist.com)\n  * Cert CN"
              }
            }
          },
          "description": ""
        },
        "server_cert": {
          "type": "object",
          "properties": {
            "cert": {
              "type": "string",
              "examples": [
                "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
              ]
            },
            "key": {
              "type": "string",
              "examples": [
                "-----BEGIN PRI..."
              ]
            },
            "password": {
              "type": "string",
              "description": "private key password (optional)"
            }
          },
          "description": "radius server cert to be presented in EAP TLS"
        },
        "use_ip_version": {
          "type": "string",
          "description": "by default, NAS devices(switches/aps) and proxies(mxedge) are configured to reach mist-nac via IPv4. enum: `v4`, `v6`"
        },
        "use_ssl_port": {
          "type": "boolean",
          "description": "By default, NAS devices (switches/aps) and proxies(mxedge) are configured to use port TCP2083(RadSec) to reach mist-nac. Set `use_ssl_port`==`true` to override that port with TCP43 (ssl), This is an org level setting that is applicable to wlans, switch_templates, and mxedge_clusters that have mist-nac enabled",
          "default": false
        },
        "usermac_expiry": {
          "maximum": 1095.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Allow customer to configure an expiry time for usermacs by attaching a Quarantine label to those which have been inactive for the configured period of time (in days). 0 means no expiry",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            30
          ]
        }
      }
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "mxedge_mgmt": {
      "title": "mxedge_mgmt",
      "type": "object",
      "properties": {
        "config_auto_revert": {
          "type": "boolean",
          "default": false
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "mist_password": {
          "type": "string",
          "examples": [
            "MIST_PASSWORD"
          ]
        },
        "oob_ip_type": {
          "type": "string",
          "description": "enum: `dhcp`, `disabled`, `static`"
        },
        "oob_ip_type6": {
          "type": "string",
          "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
        },
        "root_password": {
          "type": "string",
          "examples": [
            "ROOT_PASSWORD"
          ]
        }
      }
    },
    "optic_port_config": {
      "type": "object",
      "additionalProperties": {
        "title": "optic_port_config_port",
        "type": "object",
        "properties": {
          "channelized": {
            "type": "boolean",
            "description": "Enable channelization",
            "default": false
          },
          "speed": {
            "type": "string",
            "description": "Interface speed (e.g. `25g`, `50g`), use the chassis speed by default",
            "examples": [
              "25g"
            ]
          }
        }
      },
      "description": "Property key is the interface name or range (e.g. `et-0/0/47`, `et-0/0/48-49`)"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "password_policy": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether the policy is enabled",
          "default": false
        },
        "expiry_in_days": {
          "maximum": 365.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Password expiry in days. Password Expiry Notice banner will display in the UI 14 days before expiration",
          "contentEncoding": "int32",
          "examples": [
            60
          ]
        },
        "min_length": {
          "type": "integer",
          "description": "Required password length",
          "contentEncoding": "int32",
          "default": 8
        },
        "requires_special_char": {
          "type": "boolean",
          "description": "Whether to require special character",
          "default": false
        },
        "requires_two_factor_auth": {
          "type": "boolean",
          "description": "Whether to require two-factor auth",
          "default": false
        }
      },
      "description": "password policy"
    },
    "pcap": {
      "title": "org_setting_pcap",
      "type": "object",
      "properties": {
        "bucket": {
          "type": "string",
          "examples": [
            "myorg_pcap"
          ]
        },
        "max_pkt_len": {
          "maximum": 128.0,
          "type": "integer",
          "description": "Max_len of non-management packets to capture",
          "contentEncoding": "int32",
          "default": 128,
          "examples": [
            128
          ]
        }
      }
    },
    "pcap_bucket_verified": {
      "type": "boolean",
      "readOnly": true
    },
    "security": {
      "title": "org_setting_security",
      "type": "object",
      "properties": {
        "disable_local_ssh": {
          "type": "boolean",
          "description": "Whether to disable local SSH (by default, local SSH is enabled with allow_mist in Org is enabled"
        },
        "fips_zeroize_password": {
          "type": "string",
          "description": "password required to zeroize devices (FIPS) on site level",
          "examples": [
            "NUKETHESITE"
          ]
        },
        "limit_ssh_access": {
          "type": "boolean",
          "description": "Whether to allow certain SSH keys to SSH into the AP (see Site:Setting)",
          "default": false
        }
      }
    },
    "simple_alert": {
      "type": "object",
      "properties": {
        "arp_failure": {
          "title": "simple_alert_arp_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 20
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            }
          }
        },
        "dhcp_failure": {
          "title": "simple_alert_dhcp_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 10
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 20
            }
          }
        },
        "dns_failure": {
          "title": "simple_alert_dns_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 20
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 10
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 30
            }
          }
        }
      },
      "description": "Set of heuristic rules will be enabled when marvis subscription is not available. It triggers when, in a Z minute window, there are more than Y distinct client encountering over X failures"
    },
    "ssr": {
      "title": "setting_ssr",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "type": "object",
          "properties": {
            "channel": {
              "type": "string",
              "description": "upgrade channel to follow. enum: `alpha`, `beta`, `stable`"
            },
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Property key is the SSR model (e.g. \"SSR130\")."
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "version": {
              "type": "string",
              "description": "Firmware version to deploy (e.g. 6.3.0-107.r1). Optional, used when custom_versions not specified",
              "examples": [
                "6.3.0-107.r1"
              ]
            }
          },
          "description": "auto_upgrade device first time it is onboarded"
        },
        "conductor_hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of Conductor IP Addresses or Hosts to be used by the SSR Devices"
        },
        "conductor_token": {
          "type": "string",
          "description": "Token to be used by the SSR Devices to connect to the Conductor"
        },
        "disable_stats": {
          "type": "boolean",
          "description": "Disable stats collection on SSR devices"
        },
        "proxy": {
          "type": "object",
          "properties": {
            "disabled": {
              "type": "boolean",
              "default": false,
              "examples": [
                true
              ]
            },
            "url": {
              "type": "string",
              "examples": [
                "https://proxy.corp.com:8080/"
              ]
            }
          },
          "description": "SSR proxy configuration to talk to Mist"
        }
      }
    },
    "switch": {
      "title": "org_setting_switch",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "title": "switch_auto_upgrade",
          "type": "object",
          "properties": {
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Custom version to be used. The Property Key is the switch hardware and the property value is the firmware version",
              "examples": [
                {
                  "QFX5120-32C": "23.4R2-S2.1",
                  "QFX5130-32CD": "23.4R2-S2.3"
                }
              ]
            },
            "enabled": {
              "type": "boolean",
              "description": "Enable auto upgrade for the switch"
            },
            "snapshot": {
              "type": "boolean",
              "description": "Enable snapshot during the upgrade process",
              "default": false
            }
          }
        }
      }
    },
    "switch_mgmt": {
      "title": "org_setting_switch_mgmt",
      "type": "object",
      "properties": {
        "ap_affinity_threshold": {
          "type": "integer",
          "description": "If the field is set in both site/setting and org/setting, the value from site/setting will be used.",
          "contentEncoding": "int32",
          "default": 12,
          "examples": [
            10
          ]
        }
      }
    },
    "switch_updown_threshold": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for Switch devices only. When configured it takes effect for SW devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        0
      ]
    },
    "synthetic_test": {
      "title": "synthetictest_config",
      "type": "object",
      "properties": {
        "aggressiveness": {
          "type": "string",
          "description": "enum: `auto`, `high`, `low`"
        },
        "custom_probes": {
          "type": "object",
          "additionalProperties": {
            "title": "synthetictest_config_custom_probe",
            "type": "object",
            "properties": {
              "aggressiveness": {
                "type": "string",
                "description": "enum: `auto`, `high`, `low`"
              },
              "target": {
                "type": "string",
                "description": "Can be URL (e.g. http://x.com, https://x.com:8080/path/to/resource), IP address, or IP:port combination",
                "examples": [
                  "10.3.5.3:8080"
                ]
              },
              "threshold": {
                "type": "integer",
                "description": "In milliseconds",
                "contentEncoding": "int32",
                "examples": [
                  100
                ]
              },
              "type": {
                "type": "string",
                "description": "enum: `application`, `curl`, `icmp`, `reachability`, `tcp`"
              }
            }
          },
          "description": "Custom probes to be used for synthetic tests"
        },
        "disabled": {
          "type": "boolean",
          "default": false
        },
        "lan_networks": {
          "type": "array",
          "items": {
            "title": "synthetictest_config_lan_network",
            "type": "object",
            "properties": {
              "networks": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of networks to be used for synthetic tests",
                "examples": [
                  [
                    "pos-stations",
                    "pos-machines"
                  ]
                ]
              },
              "probes": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "app name comes from `custom_probes` above or /const/synthetic_test_probes"
              }
            },
            "description": "configure minis probes to be tested on lan networks of gateways"
          },
          "description": "List of networks to be used for synthetic tests"
        },
        "vlans": {
          "type": "array",
          "items": {
            "title": "synthetictest_config_vlan",
            "type": "object",
            "properties": {
              "custom_test_urls": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "",
                "examples": [
                  [
                    "https://www.abc.com/",
                    "https://10.3.5.1:8080/about"
                  ]
                ],
                "deprecated": true
              },
              "disabled": {
                "type": "boolean",
                "description": "For some vlans where we don't want this to run",
                "default": false
              },
              "probes": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "app name comes from `custom_probes` above or /const/synthetic_test_probes"
              },
              "vlan_ids": {
                "type": "array",
                "items": {
                  "oneOf": [
                    {
                      "type": "string"
                    },
                    {
                      "maximum": 4094.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "contentEncoding": "int32"
                    }
                  ]
                },
                "description": "",
                "examples": [
                  [
                    10,
                    20,
                    "{{vlan}}"
                  ]
                ]
              }
            }
          },
          "description": "",
          "deprecated": true
        },
        "wan_speedtest": {
          "title": "synthetictest_config_wan_speedtest",
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "time_of_day": {
              "type": "string",
              "description": "`any` / HH:MM (24-hour format)",
              "default": "any",
              "examples": [
                "12:00"
              ]
            }
          }
        }
      }
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of tags"
    },
    "ui_idle_timeout": {
      "maximum": 480.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Automatically logout the user when UI session is inactive. `0` means disabled",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        10
      ]
    },
    "ui_no_tracking": {
      "type": "boolean",
      "default": false
    },
    "vpn_options": {
      "title": "org_setting_vpn_options",
      "type": "object",
      "properties": {
        "as_base": {
          "maximum": 2147483647.0,
          "minimum": 1.0,
          "type": "integer",
          "contentEncoding": "int32"
        },
        "enable_ipv6": {
          "type": "boolean",
          "default": false
        },
        "st_subnet": {
          "type": "string",
          "description": "requiring /12 or bigger to support 16 private IPs for 65535 gateways",
          "default": "10.224.0.0/12"
        }
      }
    },
    "wan_pma": {
      "title": "org_setting_wan_pma",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "wired_pma": {
      "title": "org_setting_wired_pma",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "wireless_pma": {
      "title": "org_setting_wireless_pma",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        }
      }
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "allow_mist": {
      "type": "boolean",
      "description": "whether to allow Mist to look at this org",
      "default": false
    },
    "ap_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for AP devices only. When configured it takes effect for AP devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0
    },
    "api_policy": {
      "title": "org_setting_api_policy",
      "type": "object",
      "properties": {
        "no_reveal": {
          "type": "boolean",
          "description": "By default, API hides password/secrets when the user doesn't have write access\n  * `true`: API will hide passwords/secrets for all users\n  * `false`: API will hide passwords/secrets for read-only users",
          "default": false
        }
      }
    },
    "auto_device_naming": {
      "title": "org_setting_auto_device_naming",
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "title": "org_setting_auto_device_naming_rule",
            "type": "object",
            "properties": {
              "expression": {
                "type": "string",
                "description": "\"[0:3]\"            // \"abcdef\" -> \"abc\"  \n      \"split(.)[1]\"      // \"a.b.c\" -> \"b\"  \n      \"split(-)[1][0:3]\" // \"a1234-b5678-c90\" -> \"b56\"'",
                "examples": [
                  "split(.)[1]"
                ]
              },
              "match_device": {
                "type": "string",
                "description": "enum: `ap`, `gateway`, `switch`"
              },
              "prefix": {
                "type": "string",
                "description": "Prefix to append to the device name"
              },
              "src": {
                "type": "string",
                "description": "enum: `lldp_port_desc`, `mac`"
              },
              "suffix": {
                "type": "string",
                "description": "Suffix to append to the device name"
              }
            }
          },
          "description": ""
        }
      }
    },
    "auto_deviceprofile_assignment": {
      "title": "org_setting_auto_deviceprofile_assignment",
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "title": "org_setting_auto_assignment_rule",
            "required": [
              "src"
            ],
            "type": "object",
            "properties": {
              "create_new_site_if_needed": {
                "type": "boolean",
                "description": "If `src`==`geoip`. By default, a claimed device only gets assigned if the site exists to auto-create the site, enable this",
                "default": false
              },
              "expression": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`, `src`==`lldp_system_name`,  `src`==`dns_suffix`  \n      \"[0:3]\"            // \"abcdef\" -> \"abc\"  \n      \"split(.)[1]\"      // \"a.b.c\" -> \"b\"  \n      \"split(-)[1][0:3]\" // \"a1234-b5678-c90\" -> \"b56\"'",
                "examples": [
                  "split(.)[1]"
                ]
              },
              "gatewaytemplate_id": {
                "type": "string",
                "description": "If `src`==`geoip` and `create_new_site_if_needed`==`true`. If a gateway template is desired for this newly created site"
              },
              "match_country": {
                "type": "string",
                "description": "If `src`==`geoip`"
              },
              "match_device_type": {
                "type": "string",
                "description": "enum: `ap`, `gateway`, `switch`"
              },
              "match_model": {
                "type": "string",
                "description": "Optional/additional filter"
              },
              "model": {
                "type": "string",
                "description": "If `src`==`model`"
              },
              "prefix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "XX-"
                ]
              },
              "src": {
                "type": "string",
                "description": "enum: `ext_ip`, `dns_suffix`, `geoip`, `lldp_port_desc`, `lldp_system_name`, `model`, `name`, `subnet`"
              },
              "subnet": {
                "type": "string",
                "description": "If `src`==`subnet` or `ext_ip`==`ext_ip`"
              },
              "suffix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "-YY"
                ]
              },
              "value": {
                "type": "string",
                "description": "If \n  * `src`==`ext_ip`, `src`==`subnet` or `src`==`model`, the site name\n  * `src`==`geoip`: site name for the device to be assigned to (\\\"city\\\" / \\\"city+country\\\" / ...)\""
              }
            },
            "description": "Auto_rules in org settings"
          },
          "description": ""
        }
      }
    },
    "auto_site_assignment": {
      "title": "org_setting_auto_site_assignment",
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "title": "org_setting_auto_assignment_rule",
            "required": [
              "src"
            ],
            "type": "object",
            "properties": {
              "create_new_site_if_needed": {
                "type": "boolean",
                "description": "If `src`==`geoip`. By default, a claimed device only gets assigned if the site exists to auto-create the site, enable this",
                "default": false
              },
              "expression": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`, `src`==`lldp_system_name`,  `src`==`dns_suffix`  \n      \"[0:3]\"            // \"abcdef\" -> \"abc\"  \n      \"split(.)[1]\"      // \"a.b.c\" -> \"b\"  \n      \"split(-)[1][0:3]\" // \"a1234-b5678-c90\" -> \"b56\"'",
                "examples": [
                  "split(.)[1]"
                ]
              },
              "gatewaytemplate_id": {
                "type": "string",
                "description": "If `src`==`geoip` and `create_new_site_if_needed`==`true`. If a gateway template is desired for this newly created site"
              },
              "match_country": {
                "type": "string",
                "description": "If `src`==`geoip`"
              },
              "match_device_type": {
                "type": "string",
                "description": "enum: `ap`, `gateway`, `switch`"
              },
              "match_model": {
                "type": "string",
                "description": "Optional/additional filter"
              },
              "model": {
                "type": "string",
                "description": "If `src`==`model`"
              },
              "prefix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "XX-"
                ]
              },
              "src": {
                "type": "string",
                "description": "enum: `ext_ip`, `dns_suffix`, `geoip`, `lldp_port_desc`, `lldp_system_name`, `model`, `name`, `subnet`"
              },
              "subnet": {
                "type": "string",
                "description": "If `src`==`subnet` or `ext_ip`==`ext_ip`"
              },
              "suffix": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "If `src`==`name`",
                "examples": [
                  "-YY"
                ]
              },
              "value": {
                "type": "string",
                "description": "If \n  * `src`==`ext_ip`, `src`==`subnet` or `src`==`model`, the site name\n  * `src`==`geoip`: site name for the device to be assigned to (\\\"city\\\" / \\\"city+country\\\" / ...)\""
              }
            },
            "description": "Auto_rules in org settings"
          },
          "description": ""
        }
      }
    },
    "blacklist_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/blacklist/xxx..."
      ]
    },
    "cacerts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "RADSec certificates for AP"
    },
    "celona": {
      "title": "org_setting_celona",
      "type": "object",
      "properties": {
        "api_key": {
          "type": "string",
          "examples": [
            "$2a$04$OkaLCoJn6rDjR8ha.oduQVDST3.kJNIrte"
          ]
        },
        "api_prefix": {
          "type": "string",
          "examples": [
            "cc3273fcb016470e"
          ]
        }
      }
    },
    "cloudshark": {
      "title": "org_setting_cloudshark",
      "type": "object",
      "properties": {
        "apitoken": {
          "type": "string",
          "examples": [
            "accbd6f10c6d05c3"
          ]
        },
        "url": {
          "type": "string",
          "description": "If using CS Enterprise",
          "examples": [
            "https://cloudshark.hosted.domain"
          ]
        }
      }
    },
    "cradlepoint": {
      "type": "object",
      "properties": {
        "cp_api_id": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "84446d61-2206-4ea5-855a-0043f980be54"
          ]
        },
        "cp_api_key": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "79c329da9893e34099c7d8ad5cb9c941"
          ]
        },
        "ecm_api_id": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "73446d61-2206-4ea5-855a-0043f980be62"
          ]
        },
        "ecm_api_key": {
          "type": "string",
          "readOnly": true,
          "examples": [
            "68b329da9893e34099c7d8ad5cb9c940"
          ]
        },
        "enable_lldp": {
          "type": "boolean",
          "readOnly": true
        }
      },
      "readOnly": true
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "device_cert": {
      "type": "object",
      "properties": {
        "cert": {
          "type": "string",
          "examples": [
            "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
          ]
        },
        "key": {
          "type": "string",
          "examples": [
            "-----BEGIN PRI..."
          ]
        }
      },
      "description": "common device cert, optional"
    },
    "device_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery via\n  * device-updowns webhooks topic, \n  * Mist Alert Framework; e.g. send AP/SW/GW down event only if AP/SW/GW Up is not seen within the threshold in minutes; 0 - 240, default is 0 (trigger immediate)",
      "contentEncoding": "int32",
      "default": 0
    },
    "disable_pcap": {
      "type": "boolean",
      "description": "Whether to disallow Mist to analyze pcap files (this is required for marvis pcap)",
      "default": false
    },
    "disable_remote_shell": {
      "type": "boolean",
      "description": "Whether to disable remote shell access for an entire org",
      "default": false
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "gateway_mgmt": {
      "title": "org_setting_gateway_mgmt",
      "type": "object",
      "properties": {
        "app_probing": {
          "title": "org_setting_gateway_mgmt_app_probing",
          "type": "object",
          "properties": {
            "apps": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "APp-keys from [List Applications]($e/Constants%20Definitions/listApplications)",
              "examples": [
                [
                  "facebook"
                ]
              ]
            }
          }
        },
        "app_usage": {
          "type": "boolean",
          "description": "consumes uplink bandwidth, requires WA license"
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "host_in_policies": {
          "title": "org_setting_gateway_mgmt_host_in_policies",
          "type": "object",
          "properties": {
            "icmp": {
              "title": "org_setting_gateway_mgmt_host_in_policy",
              "type": "object",
              "properties": {
                "tenants": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                }
              }
            },
            "snmp": {
              "title": "org_setting_gateway_mgmt_host_in_policy",
              "type": "object",
              "properties": {
                "tenants": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                }
              }
            }
          }
        },
        "host_out_policies": {
          "type": "object",
          "properties": {
            "dns": {
              "title": "gateway_mgmt_host_out_policy",
              "type": "object",
              "properties": {
                "path_preference": {
                  "type": "string"
                }
              }
            },
            "ntp": {
              "title": "gateway_mgmt_host_out_policy",
              "type": "object",
              "properties": {
                "path_preference": {
                  "type": "string"
                }
              }
            },
            "syslog": {
              "title": "gateway_mgmt_host_out_policy_syslog",
              "type": "object",
              "properties": {
                "path_preference": {
                  "type": "string",
                  "examples": [
                    "broadband_wans"
                  ]
                },
                "servers": {
                  "type": "array",
                  "items": {
                    "title": "gateway_mgmt_host_out_policy_syslog_server",
                    "type": "object",
                    "properties": {
                      "host": {
                        "type": "string",
                        "examples": [
                          "103.35.3.5"
                        ]
                      },
                      "path_preference": {
                        "type": "string",
                        "examples": [
                          "dc_only"
                        ]
                      },
                      "server_name": {
                        "type": "string",
                        "examples": [
                          "dc_syslog_server"
                        ]
                      }
                    },
                    "description": "Allows to define the host_out_policy per Syslog Server. The Property key is the Syslog name"
                  },
                  "description": ""
                }
              }
            }
          },
          "description": "optional, for some of the host-out traffic, the path preference can be specified by default, ECMP will be used from all available route/path available services: dns/mist/ntp/pim"
        },
        "overlay_ip": {
          "title": "org_setting_gateway_mgmt_overlay_ip",
          "type": "object",
          "properties": {
            "ip": {
              "type": "string",
              "description": "When it's going overlay, a routable IP to overlay will be required"
            },
            "node1_ip": {
              "type": "string",
              "description": "For SSR HA cluster, another IP for node1 will be required, too"
            }
          }
        }
      }
    },
    "gateway_tunnel_updown_threshold": {
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "enable threshold-based gateway tunnel (secure edge tunnels) up-down delivery.",
      "contentEncoding": "int32"
    },
    "gateway_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for Gateway devices only. When configured it takes effect for GW devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        10
      ]
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "installer": {
      "title": "org_setting_installer",
      "type": "object",
      "properties": {
        "allow_all_devices": {
          "type": "boolean"
        },
        "allow_all_sites": {
          "type": "boolean"
        },
        "extra_site_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": ""
        },
        "grace_period": {
          "type": "integer",
          "contentEncoding": "int32"
        }
      }
    },
    "jcloud": {
      "title": "org_setting_jcloud",
      "type": "object",
      "properties": {
        "org_apitoken": {
          "type": "string",
          "description": "JCloud Org Token"
        },
        "org_apitoken_name": {
          "type": "string",
          "description": "JCloud Org Token Name"
        },
        "org_id": {
          "type": "string",
          "description": "JCloud Org ID"
        }
      }
    },
    "jcloud_ra": {
      "type": "object",
      "properties": {
        "org_apitoken": {
          "type": "string",
          "description": "JCloud Routing Assurance Org Token"
        },
        "org_apitoken_name": {
          "type": "string",
          "description": "JCloud Routing Assurance Org Token Name"
        },
        "org_id": {
          "type": "string",
          "description": "JCloud Routing Assurance Org ID"
        }
      },
      "description": "JCloud Routing Assurance connexion"
    },
    "juniper": {
      "title": "account_juniper_info",
      "type": "object",
      "properties": {
        "accounts": {
          "type": "array",
          "items": {
            "title": "juniper_account",
            "type": "object",
            "properties": {
              "linked_by": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "John Smith (john@abccorp.com)"
                ]
              },
              "name": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "ABC Corp"
                ]
              }
            }
          },
          "description": ""
        }
      }
    },
    "juniper_srx": {
      "title": "org_setting_juniper_srx",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "type": "object",
          "properties": {
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Property key is the SRX Hardware model (e.g. \"SRX4600\")"
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "snapshot": {
              "type": "boolean",
              "default": false
            },
            "version": {
              "type": "string",
              "description": "Firmware version to deploy (e.g. 23.4R2-S5.5). Optional, used when custom_versions not specified",
              "examples": [
                "23.4R2-S5.5"
              ]
            }
          },
          "description": "auto_upgrade device first time it is onboarded"
        }
      }
    },
    "junos_shell_access": {
      "type": "object",
      "properties": {
        "admin": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        },
        "helpdesk": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        },
        "read": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        },
        "write": {
          "type": "string",
          "description": "enum: `admin`, `viewer`, `none`"
        }
      },
      "description": "junos_shell_access: Manages role-based web-shell access.  \nWhen junos_shell access is not defined (Default) - No additional users are configured and web-shell uses default `mist` user to login.  \nWhen junos_shell_access is defined - Additional users mist-web-admin (admin permission), mist-web-viewer(viewer permission) are configured on the device and web-shell logs in with the mist-web-admin/mist-web-viewer user depending upon the shell access level. Setting the shell access level to \"none\", disables web-shell access for that specific role."
    },
    "marvis": {
      "title": "marvis",
      "type": "object",
      "properties": {
        "auto_operations": {
          "title": "marvis_auto_operations",
          "type": "object",
          "properties": {
            "ap_insufficient_capacity": {
              "type": "boolean",
              "default": false
            },
            "ap_loop": {
              "type": "boolean",
              "default": false
            },
            "ap_non_compliant": {
              "type": "boolean",
              "default": false
            },
            "bounce_port_for_abnormal_poe_client": {
              "type": "boolean",
              "default": false
            },
            "disable_port_when_ddos_protocol_violation": {
              "type": "boolean",
              "default": false
            },
            "disable_port_when_rogue_dhcp_server_detected": {
              "type": "boolean",
              "default": false
            },
            "gateway_non_compliant": {
              "type": "boolean",
              "default": false
            },
            "switch_misconfigured_port": {
              "type": "boolean",
              "default": false
            },
            "switch_port_stuck": {
              "type": "boolean",
              "default": false
            }
          }
        }
      }
    },
    "mgmt": {
      "type": "object",
      "properties": {
        "mxtunnel_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of Mist Tunnels"
        },
        "use_mxtunnel": {
          "type": "boolean",
          "description": "Whether to use Mist Tunnel for mgmt connectivity, this takes precedence over use_wxtunnel",
          "default": false
        },
        "use_wxtunnel": {
          "type": "boolean",
          "description": "Whether to use wxtunnel for mgmt connectivity",
          "default": false
        }
      },
      "description": "management-related properties"
    },
    "mist_nac": {
      "title": "org_setting_mist_nac",
      "type": "object",
      "properties": {
        "cacerts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of PEM-encoded ca certs"
        },
        "default_idp_id": {
          "type": "string",
          "description": "use this IDP when no explicit realm present in the incoming username/CN OR when no IDP is explicitly mapped to the incoming realm."
        },
        "disable_rsae_algorithms": {
          "type": "boolean",
          "description": "to disable RSAE_PSS_SHA256, RSAE_PSS_SHA384, RSAE_PSS_SHA512 from server side. see https://www.openssl.org/docs/man3.0/man1/openssl-ciphers.html",
          "default": false
        },
        "eap_ssl_security_level": {
          "maximum": 4.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "eap ssl security level, see https://www.openssl.org/docs/man1.1.1/man3/SSL_CTX_set_security_level.html#DEFAULT-CALLBACK-BEHAVIOUR",
          "contentEncoding": "int32",
          "default": 2
        },
        "eu_only": {
          "type": "boolean",
          "description": "By default, NAC POD failover considers all NAC pods available around the globe, i.e. EU, US, or APAC based, failover happens based on geo IP of the originating site. For strict GDPR compliance NAC POD failover would only happen between the PODs located within the EU environment, and no authentication would take place outside of EU. This is an org setting that is applicable to WLANs, switch templates, mxedge clusters that have mist_nac enabled",
          "default": false
        },
        "fingerprinting": {
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean",
              "description": "enable/disable writes to NAC DDB fingerprint table",
              "default": false
            },
            "generate_coa": {
              "type": "boolean",
              "description": "enable/disable CoA triggers on fingerprint change for wired clients, always port-bounce",
              "default": false
            },
            "generate_wireless_coa": {
              "type": "boolean",
              "description": "enable/disable CoA triggers on fingerprint change for wireless clients",
              "default": false
            },
            "wireless_coa_type": {
              "type": "string",
              "description": "enum: `reauth`, `disconnect`"
            }
          },
          "description": "Allows customer to enable client fingerprinting for policy enforcement"
        },
        "idp_machine_cert_lookup_field": {
          "type": "string",
          "description": "allow customer to choose the EAP-TLS client certificate's field to use for IDP Machine Groups lookup. enum: `automatic`, `cn`, `dns`"
        },
        "idp_user_cert_lookup_field": {
          "type": "string",
          "description": "allow customer to choose the EAP-TLS client certificate's field. To use for IDP User Groups lookup. enum: `automatic`, `cn`, `email`, `upn`"
        },
        "idps": {
          "type": "array",
          "items": {
            "title": "org_setting_mist_nac_idp",
            "type": "object",
            "properties": {
              "exclude_realms": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "When the IDP of mxedge_proxy type, exclude the following realms from proxying in addition to other valid home realms in this org"
              },
              "id": {
                "type": "string",
                "description": "Unique ID of the object instance in the Mist Organization",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "53f10664-3ce8-4c27-b382-0ef66432349f"
                ]
              },
              "user_realms": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Which realm should trigger this IDP. User Realm is extracted from:\n  * Username-AVP (`mist.com` from john@mist.com)\n  * Cert CN"
              }
            }
          },
          "description": ""
        },
        "server_cert": {
          "type": "object",
          "properties": {
            "cert": {
              "type": "string",
              "examples": [
                "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
              ]
            },
            "key": {
              "type": "string",
              "examples": [
                "-----BEGIN PRI..."
              ]
            },
            "password": {
              "type": "string",
              "description": "private key password (optional)"
            }
          },
          "description": "radius server cert to be presented in EAP TLS"
        },
        "use_ip_version": {
          "type": "string",
          "description": "by default, NAS devices(switches/aps) and proxies(mxedge) are configured to reach mist-nac via IPv4. enum: `v4`, `v6`"
        },
        "use_ssl_port": {
          "type": "boolean",
          "description": "By default, NAS devices (switches/aps) and proxies(mxedge) are configured to use port TCP2083(RadSec) to reach mist-nac. Set `use_ssl_port`==`true` to override that port with TCP43 (ssl), This is an org level setting that is applicable to wlans, switch_templates, and mxedge_clusters that have mist-nac enabled",
          "default": false
        },
        "usermac_expiry": {
          "maximum": 1095.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Allow customer to configure an expiry time for usermacs by attaching a Quarantine label to those which have been inactive for the configured period of time (in days). 0 means no expiry",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            30
          ]
        }
      }
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "mxedge_mgmt": {
      "title": "mxedge_mgmt",
      "type": "object",
      "properties": {
        "config_auto_revert": {
          "type": "boolean",
          "default": false
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "mist_password": {
          "type": "string",
          "examples": [
            "MIST_PASSWORD"
          ]
        },
        "oob_ip_type": {
          "type": "string",
          "description": "enum: `dhcp`, `disabled`, `static`"
        },
        "oob_ip_type6": {
          "type": "string",
          "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
        },
        "root_password": {
          "type": "string",
          "examples": [
            "ROOT_PASSWORD"
          ]
        }
      }
    },
    "optic_port_config": {
      "type": "object",
      "additionalProperties": {
        "title": "optic_port_config_port",
        "type": "object",
        "properties": {
          "channelized": {
            "type": "boolean",
            "description": "Enable channelization",
            "default": false
          },
          "speed": {
            "type": "string",
            "description": "Interface speed (e.g. `25g`, `50g`), use the chassis speed by default",
            "examples": [
              "25g"
            ]
          }
        }
      },
      "description": "Property key is the interface name or range (e.g. `et-0/0/47`, `et-0/0/48-49`)"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "password_policy": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether the policy is enabled",
          "default": false
        },
        "expiry_in_days": {
          "maximum": 365.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Password expiry in days. Password Expiry Notice banner will display in the UI 14 days before expiration",
          "contentEncoding": "int32",
          "examples": [
            60
          ]
        },
        "min_length": {
          "type": "integer",
          "description": "Required password length",
          "contentEncoding": "int32",
          "default": 8
        },
        "requires_special_char": {
          "type": "boolean",
          "description": "Whether to require special character",
          "default": false
        },
        "requires_two_factor_auth": {
          "type": "boolean",
          "description": "Whether to require two-factor auth",
          "default": false
        }
      },
      "description": "password policy"
    },
    "pcap": {
      "title": "org_setting_pcap",
      "type": "object",
      "properties": {
        "bucket": {
          "type": "string",
          "examples": [
            "myorg_pcap"
          ]
        },
        "max_pkt_len": {
          "maximum": 128.0,
          "type": "integer",
          "description": "Max_len of non-management packets to capture",
          "contentEncoding": "int32",
          "default": 128,
          "examples": [
            128
          ]
        }
      }
    },
    "pcap_bucket_verified": {
      "type": "boolean",
      "readOnly": true
    },
    "security": {
      "title": "org_setting_security",
      "type": "object",
      "properties": {
        "disable_local_ssh": {
          "type": "boolean",
          "description": "Whether to disable local SSH (by default, local SSH is enabled with allow_mist in Org is enabled"
        },
        "fips_zeroize_password": {
          "type": "string",
          "description": "password required to zeroize devices (FIPS) on site level",
          "examples": [
            "NUKETHESITE"
          ]
        },
        "limit_ssh_access": {
          "type": "boolean",
          "description": "Whether to allow certain SSH keys to SSH into the AP (see Site:Setting)",
          "default": false
        }
      }
    },
    "simple_alert": {
      "type": "object",
      "properties": {
        "arp_failure": {
          "title": "simple_alert_arp_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 20
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            }
          }
        },
        "dhcp_failure": {
          "title": "simple_alert_dhcp_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 10
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 20
            }
          }
        },
        "dns_failure": {
          "title": "simple_alert_dns_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 20
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 10
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 30
            }
          }
        }
      },
      "description": "Set of heuristic rules will be enabled when marvis subscription is not available. It triggers when, in a Z minute window, there are more than Y distinct client encountering over X failures"
    },
    "ssr": {
      "title": "setting_ssr",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "type": "object",
          "properties": {
            "channel": {
              "type": "string",
              "description": "upgrade channel to follow. enum: `alpha`, `beta`, `stable`"
            },
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Property key is the SSR model (e.g. \"SSR130\")."
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "version": {
              "type": "string",
              "description": "Firmware version to deploy (e.g. 6.3.0-107.r1). Optional, used when custom_versions not specified",
              "examples": [
                "6.3.0-107.r1"
              ]
            }
          },
          "description": "auto_upgrade device first time it is onboarded"
        },
        "conductor_hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of Conductor IP Addresses or Hosts to be used by the SSR Devices"
        },
        "conductor_token": {
          "type": "string",
          "description": "Token to be used by the SSR Devices to connect to the Conductor"
        },
        "disable_stats": {
          "type": "boolean",
          "description": "Disable stats collection on SSR devices"
        },
        "proxy": {
          "type": "object",
          "properties": {
            "disabled": {
              "type": "boolean",
              "default": false,
              "examples": [
                true
              ]
            },
            "url": {
              "type": "string",
              "examples": [
                "https://proxy.corp.com:8080/"
              ]
            }
          },
          "description": "SSR proxy configuration to talk to Mist"
        }
      }
    },
    "switch": {
      "title": "org_setting_switch",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "title": "switch_auto_upgrade",
          "type": "object",
          "properties": {
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Custom version to be used. The Property Key is the switch hardware and the property value is the firmware version",
              "examples": [
                {
                  "QFX5120-32C": "23.4R2-S2.1",
                  "QFX5130-32CD": "23.4R2-S2.3"
                }
              ]
            },
            "enabled": {
              "type": "boolean",
              "description": "Enable auto upgrade for the switch"
            },
            "snapshot": {
              "type": "boolean",
              "description": "Enable snapshot during the upgrade process",
              "default": false
            }
          }
        }
      }
    },
    "switch_mgmt": {
      "title": "org_setting_switch_mgmt",
      "type": "object",
      "properties": {
        "ap_affinity_threshold": {
          "type": "integer",
          "description": "If the field is set in both site/setting and org/setting, the value from site/setting will be used.",
          "contentEncoding": "int32",
          "default": 12,
          "examples": [
            10
          ]
        }
      }
    },
    "switch_updown_threshold": {
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for Switch devices only. When configured it takes effect for SW devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        0
      ]
    },
    "synthetic_test": {
      "title": "synthetictest_config",
      "type": "object",
      "properties": {
        "aggressiveness": {
          "type": "string",
          "description": "enum: `auto`, `high`, `low`"
        },
        "custom_probes": {
          "type": "object",
          "additionalProperties": {
            "title": "synthetictest_config_custom_probe",
            "type": "object",
            "properties": {
              "aggressiveness": {
                "type": "string",
                "description": "enum: `auto`, `high`, `low`"
              },
              "target": {
                "type": "string",
                "description": "Can be URL (e.g. http://x.com, https://x.com:8080/path/to/resource), IP address, or IP:port combination",
                "examples": [
                  "10.3.5.3:8080"
                ]
              },
              "threshold": {
                "type": "integer",
                "description": "In milliseconds",
                "contentEncoding": "int32",
                "examples": [
                  100
                ]
              },
              "type": {
                "type": "string",
                "description": "enum: `application`, `curl`, `icmp`, `reachability`, `tcp`"
              }
            }
          },
          "description": "Custom probes to be used for synthetic tests"
        },
        "disabled": {
          "type": "boolean",
          "default": false
        },
        "lan_networks": {
          "type": "array",
          "items": {
            "title": "synthetictest_config_lan_network",
            "type": "object",
            "properties": {
              "networks": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of networks to be used for synthetic tests",
                "examples": [
                  [
                    "pos-stations",
                    "pos-machines"
                  ]
                ]
              },
              "probes": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "app name comes from `custom_probes` above or /const/synthetic_test_probes"
              }
            },
            "description": "configure minis probes to be tested on lan networks of gateways"
          },
          "description": "List of networks to be used for synthetic tests"
        },
        "vlans": {
          "type": "array",
          "items": {
            "title": "synthetictest_config_vlan",
            "type": "object",
            "properties": {
              "custom_test_urls": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "",
                "examples": [
                  [
                    "https://www.abc.com/",
                    "https://10.3.5.1:8080/about"
                  ]
                ],
                "deprecated": true
              },
              "disabled": {
                "type": "boolean",
                "description": "For some vlans where we don't want this to run",
                "default": false
              },
              "probes": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "app name comes from `custom_probes` above or /const/synthetic_test_probes"
              },
              "vlan_ids": {
                "type": "array",
                "items": {
                  "oneOf": [
                    {
                      "type": "string"
                    },
                    {
                      "maximum": 4094.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "contentEncoding": "int32"
                    }
                  ]
                },
                "description": "",
                "examples": [
                  [
                    10,
                    20,
                    "{{vlan}}"
                  ]
                ]
              }
            }
          },
          "description": "",
          "deprecated": true
        },
        "wan_speedtest": {
          "title": "synthetictest_config_wan_speedtest",
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "time_of_day": {
              "type": "string",
              "description": "`any` / HH:MM (24-hour format)",
              "default": "any",
              "examples": [
                "12:00"
              ]
            }
          }
        }
      }
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of tags"
    },
    "ui_idle_timeout": {
      "maximum": 480.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Automatically logout the user when UI session is inactive. `0` means disabled",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        10
      ]
    },
    "ui_no_tracking": {
      "type": "boolean",
      "default": false
    },
    "vpn_options": {
      "title": "org_setting_vpn_options",
      "type": "object",
      "properties": {
        "as_base": {
          "maximum": 2147483647.0,
          "minimum": 1.0,
          "type": "integer",
          "contentEncoding": "int32"
        },
        "enable_ipv6": {
          "type": "boolean",
          "default": false
        },
        "st_subnet": {
          "type": "string",
          "description": "requiring /12 or bigger to support 16 private IPs for 65535 gateways",
          "default": "10.224.0.0/12"
        }
      }
    },
    "wan_pma": {
      "title": "org_setting_wan_pma",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "wired_pma": {
      "title": "org_setting_wired_pma",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "wireless_pma": {
      "title": "org_setting_wireless_pma",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        }
      }
    }
  },
  "description": "Org Settings"
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.setting.updateOrgSettings()`

## Usage Context

Updates the organization-level settings.

## Gotchas

- Org settings control global behaviors like auto-provisioning, security policies, and integrations.
- Changes affect all sites in the organization.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings

## MistHelper Notes

Not currently used by MistHelper directly.
