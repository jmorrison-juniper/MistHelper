# updateSiteWlanPortalTemplate

> updateSiteWlanPortalTemplate

## HTTP

`PUT /api/v1/sites/{site_id}/wlans/{wlan_id}/portal_template`

## Description

Update a Portal Template

#### Sponsor Email Template
Sponsor Email Template supports following template variables:

| **Name** | **Description** |
| --- | --- |
| approve_url | Renders URL to approve the request; optionally &minutes=N query param can be appended to change the Authorization period of the guest, where N is a valid integer denoting number of minutes a guest remains authorized |
| deny_url | Renders URL to reject the request |
| guest_email | Renders Email ID of the guest |
| guest_name | Renders Name of the guest |
| field1 | Renders value of the Custom Field 1 |
| field2 | Renders value of the Custom Field 2 |
| company | Renders value of the Company field |
| sponsor_link_validity_duration | Renders validity time of the request (i.e. Approve/Deny URL) |
| auth_expire_minutes | Renders Wlan-level configured Guest Authorization Expiration time period (in minutes), If not configured then default (1 day in minutes) |

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| wlan_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "portal_template": {
      "type": "object",
      "properties": {
        "accessCodeAlternateEmail": {
          "type": "string",
          "default": "Use alternate email address"
        },
        "alignment": {
          "type": "string",
          "description": "defines alignment on portal. enum: `center`, `left`, `right`"
        },
        "ar": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "authButtonAmazon": {
          "type": "string",
          "description": "Label for Amazon auth button",
          "default": "Sign in with Amazon"
        },
        "authButtonAzure": {
          "type": "string",
          "description": "Label for Azure auth button",
          "default": "Sign in with Azure"
        },
        "authButtonEmail": {
          "type": "string",
          "description": "Label for Email auth button",
          "default": "Sign in with Email"
        },
        "authButtonFacebook": {
          "type": "string",
          "description": "Label for Facebook auth button",
          "default": "Sign in with Facebook"
        },
        "authButtonGoogle": {
          "type": "string",
          "description": "Label for Google auth button",
          "default": "Sign in with Google"
        },
        "authButtonMicrosoft": {
          "type": "string",
          "description": "Label for Microsoft auth button",
          "default": "Sign in with Microsoft"
        },
        "authButtonPassphrase": {
          "type": "string",
          "description": "Label for passphrase auth button",
          "default": "Sign in with Passphrase"
        },
        "authButtonSms": {
          "type": "string",
          "description": "Label for SMS auth button",
          "default": "Sign in with Text Message"
        },
        "authButtonSponsor": {
          "type": "string",
          "description": "Label for Sponsor auth button",
          "default": "Sign in as Guest"
        },
        "authLabel": {
          "type": "string",
          "default": "Connect to Wi-Fi with"
        },
        "backLink": {
          "type": "string",
          "description": "Label of the link to go back to /logon"
        },
        "ca-ES": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "color": {
          "type": "string",
          "description": "Portal main color",
          "default": "#1074bc"
        },
        "colorDark": {
          "type": "string",
          "default": "#0b5183"
        },
        "colorLight": {
          "type": "string",
          "default": "#3589c6"
        },
        "company": {
          "type": "boolean",
          "description": "Whether company field is required",
          "default": false
        },
        "companyError": {
          "type": "string",
          "description": "Error message when company not provided",
          "default": "Please provide your company name"
        },
        "companyLabel": {
          "type": "string",
          "description": "Label of company field",
          "default": "Company"
        },
        "cs-CZ": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "da-DK": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "de-DE": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "el-GR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "email": {
          "type": "boolean",
          "description": "Whether email field is required",
          "default": false
        },
        "emailAccessDomainError": {
          "type": "string",
          "description": "Error message when a user has valid social login but doesn't match specified email domains.",
          "default": "Email Access Domain Error"
        },
        "emailCancel": {
          "type": "string",
          "description": "Label for cancel confirmation code submission using email auth",
          "default": "Cancel"
        },
        "emailCodeCancel": {
          "type": "string",
          "default": "I did not receive the code"
        },
        "emailCodeError": {
          "type": "string",
          "default": "Please provide valid alternate email"
        },
        "emailCodeFieldLabel": {
          "type": "string",
          "default": "Access Code"
        },
        "emailCodeMessage": {
          "type": "string",
          "default": "Enter the access number that was sent to your email address."
        },
        "emailCodeSubmit": {
          "type": "string",
          "default": "Sign In"
        },
        "emailCodeTitle": {
          "type": "string",
          "default": "Access Code"
        },
        "emailError": {
          "type": "string",
          "description": "Error message when email not provided",
          "default": "Please provide valid email"
        },
        "emailFieldLabel": {
          "type": "string",
          "default": "Enter your email address"
        },
        "emailLabel": {
          "type": "string",
          "description": "Label of email field",
          "default": "Email"
        },
        "emailMessage": {
          "type": "string",
          "default": "We will email you an authentication code which you can use to connect to the Wi-Fi network."
        },
        "emailSubmit": {
          "type": "string",
          "description": "Label for confirmation code submit button using email auth",
          "default": "Send Access Code"
        },
        "emailTitle": {
          "type": "string",
          "description": "Title for the Email registration",
          "default": "Sign in with Email"
        },
        "en-GB": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "en-US": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "es-ES": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "fi-FI": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "field1": {
          "type": "boolean",
          "description": "Whether to ask field1",
          "default": false
        },
        "field1Error": {
          "type": "string",
          "description": "Error message when field1 not provided",
          "default": "Please provide Custom Field 1"
        },
        "field1Label": {
          "type": "string",
          "description": "Label of field1",
          "default": "Custom Field 1"
        },
        "field1Required": {
          "type": "boolean",
          "description": "Whether field1 is required field"
        },
        "field2": {
          "type": "boolean",
          "description": "Whether to ask field2",
          "default": false
        },
        "field2Error": {
          "type": "string",
          "description": "Error message when field2 not provided",
          "default": "Please provide Custom Field 2"
        },
        "field2Label": {
          "type": "string",
          "description": "Label of field2",
          "default": "Custom Field 2"
        },
        "field2Required": {
          "type": "boolean",
          "description": "Whether field2 is required field"
        },
        "field3": {
          "type": "boolean",
          "description": "Whether to ask field3",
          "default": false
        },
        "field3Error": {
          "type": "string",
          "description": "Error message when field3 not provided",
          "default": "Please provide Custom Field 3"
        },
        "field3Label": {
          "type": "string",
          "description": "Label of field3",
          "default": "Custom Field 3"
        },
        "field3Required": {
          "type": "boolean",
          "description": "Whether field3 is required field"
        },
        "field4": {
          "type": "boolean",
          "description": "Whether to ask field4",
          "default": false
        },
        "field4Error": {
          "type": "string",
          "description": "Error message when field4 not provided",
          "default": "Please provide Custom Field 4"
        },
        "field4Label": {
          "type": "string",
          "description": "Label of field4",
          "default": "Custom Field 4"
        },
        "field4Required": {
          "type": "boolean",
          "description": "Whether field4 is required field"
        },
        "fr-FR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "he-IL": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "hi-IN": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "hr-HR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "hu-HU": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "id-ID": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "it-IT": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "ja-JP": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "ko-KR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "logo": {
          "type": [
            "string",
            "null"
          ],
          "description": "Custom logo with `data:image/png;base64,` format, default null, uses Juniper Mist Logo. File size must be less than 100kB and image dimensions must be less than 500px x 200px (width x height).",
          "examples": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAZg\u2026"
          ]
        },
        "logoHeight": {
          "maximum": 200.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Height of the logo, in px",
          "contentEncoding": "int32",
          "examples": [
            123
          ]
        },
        "logoWidth": {
          "maximum": 500.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Width of the logo, in px",
          "contentEncoding": "int32",
          "examples": [
            408
          ]
        },
        "marketingPolicyLink": {
          "type": "string",
          "description": "label of the link to go to /marketing_policy",
          "default": "Marketing Policy"
        },
        "marketingPolicyOptIn": {
          "type": "boolean",
          "description": "Whether marketing policy optin is enabled",
          "default": false
        },
        "marketingPolicyOptInLabel": {
          "type": "string",
          "description": "label for marketing optin",
          "default": "I wish to receive Marketing notifications"
        },
        "marketingPolicyOptInText": {
          "type": "string",
          "description": "marketing policy text",
          "default": "Marketing policy content"
        },
        "message": {
          "type": "string",
          "default": "Sign in to get online"
        },
        "ms-MY": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "multiAuth": {
          "type": "boolean",
          "default": false
        },
        "name": {
          "type": "boolean",
          "description": "Whether name field is required",
          "default": false
        },
        "nameError": {
          "type": "string",
          "description": "Error message when name not provided",
          "default": "Please provide your name"
        },
        "nameLabel": {
          "type": "string",
          "description": "Label of name field",
          "default": "Name"
        },
        "nb-NO": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "nl-NL": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "optOutDefault": {
          "type": "boolean",
          "description": "Default value for the `Do not store` checkbox",
          "default": true
        },
        "optout": {
          "type": "boolean",
          "description": "Whether to display Do Not Store My Personal Information",
          "default": false
        },
        "optoutLabel": {
          "type": "string",
          "description": "Label for Do Not Store My Personal Information",
          "default": "Do not store"
        },
        "pageTitle": {
          "type": "string"
        },
        "passphraseCancel": {
          "type": "string",
          "description": "Label for the Passphrase cancel button",
          "default": "Cancel"
        },
        "passphraseError": {
          "type": "string",
          "description": "Error message when invalid passphrase is provided",
          "default": "Invalid Passphrase"
        },
        "passphraseLabel": {
          "type": "string",
          "description": "Passphrase",
          "default": "Passphrase"
        },
        "passphraseMessage": {
          "type": "string",
          "default": "Enter the secret passphrase to access the Wi-Fi network."
        },
        "passphraseSubmit": {
          "type": "string",
          "description": "Label for the Passphrase submit button",
          "default": "Sign in"
        },
        "passphraseTitle": {
          "type": "string",
          "description": "Title for passphrase details page",
          "default": "Sign in with Passphrase"
        },
        "pl-PL": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "poweredBy": {
          "type": "boolean",
          "description": "Whether to show \\\"Powered by Mist\\\"",
          "default": true
        },
        "privacy": {
          "type": "boolean",
          "description": "Whether to require the Privacy Term acceptance",
          "default": false
        },
        "privacyPolicyAcceptLabel": {
          "type": "string",
          "description": "Prefix of the label of the link to go to Privacy Policy",
          "default": "I accept the Privacy Terms"
        },
        "privacyPolicyError": {
          "type": "string",
          "description": "Error message when Privacy Policy not accepted",
          "default": "Please review and accept the Privacy Terms"
        },
        "privacyPolicyLink": {
          "type": "string",
          "description": "Label of the link to go to Privacy Policy",
          "default": "Privacy Terms"
        },
        "privacyPolicyText": {
          "type": "string",
          "description": "Text of the Privacy Policy",
          "default": "<< provide your Privacy Terms here >>"
        },
        "pt-BR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "pt-PT": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "requiredFieldLabel": {
          "type": "string",
          "description": "Label to denote required field",
          "default": "required"
        },
        "responsiveLayout": {
          "type": "boolean",
          "default": true
        },
        "ro-RO": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "ru-RU": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "signInLabel": {
          "type": "string",
          "description": "Label of the button to signin",
          "default": "Sign In"
        },
        "sk-SK": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "smsCarrierDefault": {
          "type": "string",
          "default": "Please Select"
        },
        "smsCarrierError": {
          "type": "string",
          "default": "Please select a mobile carrier"
        },
        "smsCarrierFieldLabel": {
          "type": "string",
          "description": "Label for mobile carrier drop-down list",
          "default": "Mobile Carrier"
        },
        "smsCodeCancel": {
          "type": "string",
          "description": "Label for cancel confirmation code submission",
          "default": "I did not receive the code"
        },
        "smsCodeError": {
          "type": "string",
          "description": "Error message when confirmation code is invalid",
          "default": "Invalid Access Code"
        },
        "smsCodeFieldLabel": {
          "type": "string",
          "default": "Confirmation Code"
        },
        "smsCodeMessage": {
          "type": "string",
          "default": "Enter the access number that was sent to your mobile number."
        },
        "smsCodeSubmit": {
          "type": "string",
          "description": "Label for confirmation code submit button",
          "default": "Sign In"
        },
        "smsCodeTitle": {
          "type": "string",
          "default": "Access Code"
        },
        "smsCountryFieldLabel": {
          "type": "string",
          "default": "Country Code"
        },
        "smsCountryFormat": {
          "type": "string",
          "default": "+1"
        },
        "smsHaveAccessCode": {
          "type": "string",
          "description": "Label for checkbox to specify that the user has access code",
          "default": "I have an access code"
        },
        "smsIsTwilio": {
          "type": "boolean",
          "default": false
        },
        "smsMessageFormat": {
          "type": "string",
          "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
        },
        "smsNumberCancel": {
          "type": "string",
          "description": "Label for canceling mobile details for SMS auth",
          "default": "Cancel"
        },
        "smsNumberError": {
          "type": "string",
          "default": "Invalid Mobile Number"
        },
        "smsNumberFieldLabel": {
          "type": "string",
          "description": "Label for field to provide mobile number",
          "default": "Mobile Number"
        },
        "smsNumberFormat": {
          "type": "string",
          "default": "2125551212 (digits only)"
        },
        "smsNumberMessage": {
          "type": "string",
          "default": "We will send an access code to your mobile number which you can use to connect to the Wi-Fi network. Message and data rates may apply."
        },
        "smsNumberSubmit": {
          "type": "string",
          "description": "Label for submit button for code generation",
          "default": "Send Access Code"
        },
        "smsNumberTitle": {
          "type": "string",
          "description": "Title for phone number details",
          "default": "Sign in with Text Message"
        },
        "smsUsernameFormat": {
          "type": "string",
          "default": "username"
        },
        "smsValidityDuration": {
          "maximum": 30.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "How long confirmation code should be considered valid (in minutes)",
          "contentEncoding": "int32"
        },
        "sponsorBackLink": {
          "type": "string",
          "default": "Go back and edit request form"
        },
        "sponsorCancel": {
          "type": "string",
          "default": "Cancel"
        },
        "sponsorEmail": {
          "type": "string",
          "description": "Label for Sponsor Email",
          "default": "Sponsor Email"
        },
        "sponsorEmailError": {
          "type": "string",
          "default": "Please provide valid sponsor email"
        },
        "sponsorEmailTemplate": {
          "type": "string",
          "description": "HTML template to replace/override default sponsor email template \nSponsor Email Template supports following template variables:\n  * `approve_url`: Renders URL to approve the request; optionally &minutes=N query param can be appended to change the Authorization period of the guest, where N is a valid integer denoting number of minutes a guest remains authorized\n  * `deny_url`: Renders URL to reject the request\n  * `guest_email`: Renders Email ID of the guest\n  * `guest_name`: Renders Name of the guest\n  * `field1`: Renders value of the Custom Field 1\n  * `field2`: Renders value of the Custom Field 2\n  * `sponsor_link_validity_duration`: Renders validity time of the request (i.e. Approve/Deny URL)\n  * `auth_expire_minutes`: Renders Wlan-level configured Guest Authorization Expiration time period (in minutes), If not configured then default (1 day in minutes)"
        },
        "sponsorInfoApproved": {
          "type": "string",
          "default": "Your request was approved by"
        },
        "sponsorInfoDenied": {
          "type": "string",
          "default": "Your request was denied by"
        },
        "sponsorInfoPending": {
          "type": "string",
          "default": "Your notification has been sent to"
        },
        "sponsorName": {
          "type": "string",
          "description": "Label for Sponsor Name",
          "default": "Sponsor Name"
        },
        "sponsorNameError": {
          "type": "string",
          "default": "Please provide sponsor name"
        },
        "sponsorNotePending": {
          "type": "string",
          "default": "Please wait for them to acknowledge."
        },
        "sponsorRequestAccess": {
          "type": "string",
          "description": "Submit button label request Wifi Access and notify sponsor about guest request",
          "default": "Request Wi-Fi Access"
        },
        "sponsorStatusApproved": {
          "type": "string",
          "description": "Text to display if sponsor approves request",
          "default": "Your request was approved"
        },
        "sponsorStatusDenied": {
          "type": "string",
          "description": "Text to display when sponsor denies request",
          "default": "Your request was denied"
        },
        "sponsorStatusPending": {
          "type": "string",
          "description": "Text to display if request is still pending",
          "default": "Notification Sent"
        },
        "sponsorSubmit": {
          "type": "string",
          "description": "Submit button label to notify sponsor about guest request",
          "default": "Request Wi-Fi Access"
        },
        "sponsorsError": {
          "type": "string",
          "default": "Please select a sponsor"
        },
        "sponsorsFieldLabel": {
          "type": "string",
          "default": "Sponsors"
        },
        "sv-SE": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "th-TH": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "tos": {
          "type": "boolean",
          "default": true
        },
        "tosAcceptLabel": {
          "type": "string",
          "description": "Prefix of the label of the link to go to tos",
          "default": "I accept the Terms of Service"
        },
        "tosError": {
          "type": "string",
          "description": "Error message when tos not accepted",
          "default": "Please review and accept the Terms of Service"
        },
        "tosLink": {
          "type": "string",
          "description": "Label of the link to go to tos",
          "default": "Terms of Service"
        },
        "tosText": {
          "type": "string",
          "description": "Text of the Terms of Service",
          "default": "<< provide your Terms of Service here >>"
        },
        "tr-TR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "uk-UA": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "vi-VN": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "zh-Hans": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "zh-Hant": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        }
      },
      "required": [
        "pageTitle"
      ],
      "description": "Portal template wlan settings"
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
    "portal_template": {
      "type": "object",
      "properties": {
        "accessCodeAlternateEmail": {
          "type": "string",
          "default": "Use alternate email address"
        },
        "alignment": {
          "type": "string",
          "description": "defines alignment on portal. enum: `center`, `left`, `right`"
        },
        "ar": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "authButtonAmazon": {
          "type": "string",
          "description": "Label for Amazon auth button",
          "default": "Sign in with Amazon"
        },
        "authButtonAzure": {
          "type": "string",
          "description": "Label for Azure auth button",
          "default": "Sign in with Azure"
        },
        "authButtonEmail": {
          "type": "string",
          "description": "Label for Email auth button",
          "default": "Sign in with Email"
        },
        "authButtonFacebook": {
          "type": "string",
          "description": "Label for Facebook auth button",
          "default": "Sign in with Facebook"
        },
        "authButtonGoogle": {
          "type": "string",
          "description": "Label for Google auth button",
          "default": "Sign in with Google"
        },
        "authButtonMicrosoft": {
          "type": "string",
          "description": "Label for Microsoft auth button",
          "default": "Sign in with Microsoft"
        },
        "authButtonPassphrase": {
          "type": "string",
          "description": "Label for passphrase auth button",
          "default": "Sign in with Passphrase"
        },
        "authButtonSms": {
          "type": "string",
          "description": "Label for SMS auth button",
          "default": "Sign in with Text Message"
        },
        "authButtonSponsor": {
          "type": "string",
          "description": "Label for Sponsor auth button",
          "default": "Sign in as Guest"
        },
        "authLabel": {
          "type": "string",
          "default": "Connect to Wi-Fi with"
        },
        "backLink": {
          "type": "string",
          "description": "Label of the link to go back to /logon"
        },
        "ca-ES": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "color": {
          "type": "string",
          "description": "Portal main color",
          "default": "#1074bc"
        },
        "colorDark": {
          "type": "string",
          "default": "#0b5183"
        },
        "colorLight": {
          "type": "string",
          "default": "#3589c6"
        },
        "company": {
          "type": "boolean",
          "description": "Whether company field is required",
          "default": false
        },
        "companyError": {
          "type": "string",
          "description": "Error message when company not provided",
          "default": "Please provide your company name"
        },
        "companyLabel": {
          "type": "string",
          "description": "Label of company field",
          "default": "Company"
        },
        "cs-CZ": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "da-DK": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "de-DE": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "el-GR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "email": {
          "type": "boolean",
          "description": "Whether email field is required",
          "default": false
        },
        "emailAccessDomainError": {
          "type": "string",
          "description": "Error message when a user has valid social login but doesn't match specified email domains.",
          "default": "Email Access Domain Error"
        },
        "emailCancel": {
          "type": "string",
          "description": "Label for cancel confirmation code submission using email auth",
          "default": "Cancel"
        },
        "emailCodeCancel": {
          "type": "string",
          "default": "I did not receive the code"
        },
        "emailCodeError": {
          "type": "string",
          "default": "Please provide valid alternate email"
        },
        "emailCodeFieldLabel": {
          "type": "string",
          "default": "Access Code"
        },
        "emailCodeMessage": {
          "type": "string",
          "default": "Enter the access number that was sent to your email address."
        },
        "emailCodeSubmit": {
          "type": "string",
          "default": "Sign In"
        },
        "emailCodeTitle": {
          "type": "string",
          "default": "Access Code"
        },
        "emailError": {
          "type": "string",
          "description": "Error message when email not provided",
          "default": "Please provide valid email"
        },
        "emailFieldLabel": {
          "type": "string",
          "default": "Enter your email address"
        },
        "emailLabel": {
          "type": "string",
          "description": "Label of email field",
          "default": "Email"
        },
        "emailMessage": {
          "type": "string",
          "default": "We will email you an authentication code which you can use to connect to the Wi-Fi network."
        },
        "emailSubmit": {
          "type": "string",
          "description": "Label for confirmation code submit button using email auth",
          "default": "Send Access Code"
        },
        "emailTitle": {
          "type": "string",
          "description": "Title for the Email registration",
          "default": "Sign in with Email"
        },
        "en-GB": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "en-US": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "es-ES": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "fi-FI": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "field1": {
          "type": "boolean",
          "description": "Whether to ask field1",
          "default": false
        },
        "field1Error": {
          "type": "string",
          "description": "Error message when field1 not provided",
          "default": "Please provide Custom Field 1"
        },
        "field1Label": {
          "type": "string",
          "description": "Label of field1",
          "default": "Custom Field 1"
        },
        "field1Required": {
          "type": "boolean",
          "description": "Whether field1 is required field"
        },
        "field2": {
          "type": "boolean",
          "description": "Whether to ask field2",
          "default": false
        },
        "field2Error": {
          "type": "string",
          "description": "Error message when field2 not provided",
          "default": "Please provide Custom Field 2"
        },
        "field2Label": {
          "type": "string",
          "description": "Label of field2",
          "default": "Custom Field 2"
        },
        "field2Required": {
          "type": "boolean",
          "description": "Whether field2 is required field"
        },
        "field3": {
          "type": "boolean",
          "description": "Whether to ask field3",
          "default": false
        },
        "field3Error": {
          "type": "string",
          "description": "Error message when field3 not provided",
          "default": "Please provide Custom Field 3"
        },
        "field3Label": {
          "type": "string",
          "description": "Label of field3",
          "default": "Custom Field 3"
        },
        "field3Required": {
          "type": "boolean",
          "description": "Whether field3 is required field"
        },
        "field4": {
          "type": "boolean",
          "description": "Whether to ask field4",
          "default": false
        },
        "field4Error": {
          "type": "string",
          "description": "Error message when field4 not provided",
          "default": "Please provide Custom Field 4"
        },
        "field4Label": {
          "type": "string",
          "description": "Label of field4",
          "default": "Custom Field 4"
        },
        "field4Required": {
          "type": "boolean",
          "description": "Whether field4 is required field"
        },
        "fr-FR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "he-IL": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "hi-IN": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "hr-HR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "hu-HU": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "id-ID": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "it-IT": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "ja-JP": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "ko-KR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "logo": {
          "type": [
            "string",
            "null"
          ],
          "description": "Custom logo with `data:image/png;base64,` format, default null, uses Juniper Mist Logo. File size must be less than 100kB and image dimensions must be less than 500px x 200px (width x height).",
          "examples": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAZg\u2026"
          ]
        },
        "logoHeight": {
          "maximum": 200.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Height of the logo, in px",
          "contentEncoding": "int32",
          "examples": [
            123
          ]
        },
        "logoWidth": {
          "maximum": 500.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Width of the logo, in px",
          "contentEncoding": "int32",
          "examples": [
            408
          ]
        },
        "marketingPolicyLink": {
          "type": "string",
          "description": "label of the link to go to /marketing_policy",
          "default": "Marketing Policy"
        },
        "marketingPolicyOptIn": {
          "type": "boolean",
          "description": "Whether marketing policy optin is enabled",
          "default": false
        },
        "marketingPolicyOptInLabel": {
          "type": "string",
          "description": "label for marketing optin",
          "default": "I wish to receive Marketing notifications"
        },
        "marketingPolicyOptInText": {
          "type": "string",
          "description": "marketing policy text",
          "default": "Marketing policy content"
        },
        "message": {
          "type": "string",
          "default": "Sign in to get online"
        },
        "ms-MY": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "multiAuth": {
          "type": "boolean",
          "default": false
        },
        "name": {
          "type": "boolean",
          "description": "Whether name field is required",
          "default": false
        },
        "nameError": {
          "type": "string",
          "description": "Error message when name not provided",
          "default": "Please provide your name"
        },
        "nameLabel": {
          "type": "string",
          "description": "Label of name field",
          "default": "Name"
        },
        "nb-NO": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "nl-NL": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "optOutDefault": {
          "type": "boolean",
          "description": "Default value for the `Do not store` checkbox",
          "default": true
        },
        "optout": {
          "type": "boolean",
          "description": "Whether to display Do Not Store My Personal Information",
          "default": false
        },
        "optoutLabel": {
          "type": "string",
          "description": "Label for Do Not Store My Personal Information",
          "default": "Do not store"
        },
        "pageTitle": {
          "type": "string"
        },
        "passphraseCancel": {
          "type": "string",
          "description": "Label for the Passphrase cancel button",
          "default": "Cancel"
        },
        "passphraseError": {
          "type": "string",
          "description": "Error message when invalid passphrase is provided",
          "default": "Invalid Passphrase"
        },
        "passphraseLabel": {
          "type": "string",
          "description": "Passphrase",
          "default": "Passphrase"
        },
        "passphraseMessage": {
          "type": "string",
          "default": "Enter the secret passphrase to access the Wi-Fi network."
        },
        "passphraseSubmit": {
          "type": "string",
          "description": "Label for the Passphrase submit button",
          "default": "Sign in"
        },
        "passphraseTitle": {
          "type": "string",
          "description": "Title for passphrase details page",
          "default": "Sign in with Passphrase"
        },
        "pl-PL": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "poweredBy": {
          "type": "boolean",
          "description": "Whether to show \\\"Powered by Mist\\\"",
          "default": true
        },
        "privacy": {
          "type": "boolean",
          "description": "Whether to require the Privacy Term acceptance",
          "default": false
        },
        "privacyPolicyAcceptLabel": {
          "type": "string",
          "description": "Prefix of the label of the link to go to Privacy Policy",
          "default": "I accept the Privacy Terms"
        },
        "privacyPolicyError": {
          "type": "string",
          "description": "Error message when Privacy Policy not accepted",
          "default": "Please review and accept the Privacy Terms"
        },
        "privacyPolicyLink": {
          "type": "string",
          "description": "Label of the link to go to Privacy Policy",
          "default": "Privacy Terms"
        },
        "privacyPolicyText": {
          "type": "string",
          "description": "Text of the Privacy Policy",
          "default": "<< provide your Privacy Terms here >>"
        },
        "pt-BR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "pt-PT": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "requiredFieldLabel": {
          "type": "string",
          "description": "Label to denote required field",
          "default": "required"
        },
        "responsiveLayout": {
          "type": "boolean",
          "default": true
        },
        "ro-RO": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "ru-RU": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "signInLabel": {
          "type": "string",
          "description": "Label of the button to signin",
          "default": "Sign In"
        },
        "sk-SK": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "smsCarrierDefault": {
          "type": "string",
          "default": "Please Select"
        },
        "smsCarrierError": {
          "type": "string",
          "default": "Please select a mobile carrier"
        },
        "smsCarrierFieldLabel": {
          "type": "string",
          "description": "Label for mobile carrier drop-down list",
          "default": "Mobile Carrier"
        },
        "smsCodeCancel": {
          "type": "string",
          "description": "Label for cancel confirmation code submission",
          "default": "I did not receive the code"
        },
        "smsCodeError": {
          "type": "string",
          "description": "Error message when confirmation code is invalid",
          "default": "Invalid Access Code"
        },
        "smsCodeFieldLabel": {
          "type": "string",
          "default": "Confirmation Code"
        },
        "smsCodeMessage": {
          "type": "string",
          "default": "Enter the access number that was sent to your mobile number."
        },
        "smsCodeSubmit": {
          "type": "string",
          "description": "Label for confirmation code submit button",
          "default": "Sign In"
        },
        "smsCodeTitle": {
          "type": "string",
          "default": "Access Code"
        },
        "smsCountryFieldLabel": {
          "type": "string",
          "default": "Country Code"
        },
        "smsCountryFormat": {
          "type": "string",
          "default": "+1"
        },
        "smsHaveAccessCode": {
          "type": "string",
          "description": "Label for checkbox to specify that the user has access code",
          "default": "I have an access code"
        },
        "smsIsTwilio": {
          "type": "boolean",
          "default": false
        },
        "smsMessageFormat": {
          "type": "string",
          "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
        },
        "smsNumberCancel": {
          "type": "string",
          "description": "Label for canceling mobile details for SMS auth",
          "default": "Cancel"
        },
        "smsNumberError": {
          "type": "string",
          "default": "Invalid Mobile Number"
        },
        "smsNumberFieldLabel": {
          "type": "string",
          "description": "Label for field to provide mobile number",
          "default": "Mobile Number"
        },
        "smsNumberFormat": {
          "type": "string",
          "default": "2125551212 (digits only)"
        },
        "smsNumberMessage": {
          "type": "string",
          "default": "We will send an access code to your mobile number which you can use to connect to the Wi-Fi network. Message and data rates may apply."
        },
        "smsNumberSubmit": {
          "type": "string",
          "description": "Label for submit button for code generation",
          "default": "Send Access Code"
        },
        "smsNumberTitle": {
          "type": "string",
          "description": "Title for phone number details",
          "default": "Sign in with Text Message"
        },
        "smsUsernameFormat": {
          "type": "string",
          "default": "username"
        },
        "smsValidityDuration": {
          "maximum": 30.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "How long confirmation code should be considered valid (in minutes)",
          "contentEncoding": "int32"
        },
        "sponsorBackLink": {
          "type": "string",
          "default": "Go back and edit request form"
        },
        "sponsorCancel": {
          "type": "string",
          "default": "Cancel"
        },
        "sponsorEmail": {
          "type": "string",
          "description": "Label for Sponsor Email",
          "default": "Sponsor Email"
        },
        "sponsorEmailError": {
          "type": "string",
          "default": "Please provide valid sponsor email"
        },
        "sponsorEmailTemplate": {
          "type": "string",
          "description": "HTML template to replace/override default sponsor email template \nSponsor Email Template supports following template variables:\n  * `approve_url`: Renders URL to approve the request; optionally &minutes=N query param can be appended to change the Authorization period of the guest, where N is a valid integer denoting number of minutes a guest remains authorized\n  * `deny_url`: Renders URL to reject the request\n  * `guest_email`: Renders Email ID of the guest\n  * `guest_name`: Renders Name of the guest\n  * `field1`: Renders value of the Custom Field 1\n  * `field2`: Renders value of the Custom Field 2\n  * `sponsor_link_validity_duration`: Renders validity time of the request (i.e. Approve/Deny URL)\n  * `auth_expire_minutes`: Renders Wlan-level configured Guest Authorization Expiration time period (in minutes), If not configured then default (1 day in minutes)"
        },
        "sponsorInfoApproved": {
          "type": "string",
          "default": "Your request was approved by"
        },
        "sponsorInfoDenied": {
          "type": "string",
          "default": "Your request was denied by"
        },
        "sponsorInfoPending": {
          "type": "string",
          "default": "Your notification has been sent to"
        },
        "sponsorName": {
          "type": "string",
          "description": "Label for Sponsor Name",
          "default": "Sponsor Name"
        },
        "sponsorNameError": {
          "type": "string",
          "default": "Please provide sponsor name"
        },
        "sponsorNotePending": {
          "type": "string",
          "default": "Please wait for them to acknowledge."
        },
        "sponsorRequestAccess": {
          "type": "string",
          "description": "Submit button label request Wifi Access and notify sponsor about guest request",
          "default": "Request Wi-Fi Access"
        },
        "sponsorStatusApproved": {
          "type": "string",
          "description": "Text to display if sponsor approves request",
          "default": "Your request was approved"
        },
        "sponsorStatusDenied": {
          "type": "string",
          "description": "Text to display when sponsor denies request",
          "default": "Your request was denied"
        },
        "sponsorStatusPending": {
          "type": "string",
          "description": "Text to display if request is still pending",
          "default": "Notification Sent"
        },
        "sponsorSubmit": {
          "type": "string",
          "description": "Submit button label to notify sponsor about guest request",
          "default": "Request Wi-Fi Access"
        },
        "sponsorsError": {
          "type": "string",
          "default": "Please select a sponsor"
        },
        "sponsorsFieldLabel": {
          "type": "string",
          "default": "Sponsors"
        },
        "sv-SE": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "th-TH": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "tos": {
          "type": "boolean",
          "default": true
        },
        "tosAcceptLabel": {
          "type": "string",
          "description": "Prefix of the label of the link to go to tos",
          "default": "I accept the Terms of Service"
        },
        "tosError": {
          "type": "string",
          "description": "Error message when tos not accepted",
          "default": "Please review and accept the Terms of Service"
        },
        "tosLink": {
          "type": "string",
          "description": "Label of the link to go to tos",
          "default": "Terms of Service"
        },
        "tosText": {
          "type": "string",
          "description": "Text of the Terms of Service",
          "default": "<< provide your Terms of Service here >>"
        },
        "tr-TR": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "uk-UA": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "vi-VN": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "zh-Hans": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        },
        "zh-Hant": {
          "title": "wlan_portal_template_setting_locale",
          "type": "object",
          "properties": {
            "authButtonAmazon": {
              "type": "string",
              "description": "Label for Amazon auth button"
            },
            "authButtonAzure": {
              "type": "string",
              "description": "Label for Azure auth button"
            },
            "authButtonEmail": {
              "type": "string",
              "description": "Label for Email auth button"
            },
            "authButtonFacebook": {
              "type": "string",
              "description": "Label for Facebook auth button"
            },
            "authButtonGoogle": {
              "type": "string",
              "description": "Label for Google auth button"
            },
            "authButtonMicrosoft": {
              "type": "string",
              "description": "Label for Microsoft auth button"
            },
            "authButtonPassphrase": {
              "type": "string",
              "description": "Label for passphrase auth button"
            },
            "authButtonSms": {
              "type": "string",
              "description": "Label for SMS auth button"
            },
            "authButtonSponsor": {
              "type": "string",
              "description": "Label for Sponsor auth button"
            },
            "authLabel": {
              "type": "string"
            },
            "backLink": {
              "type": "string",
              "description": "Label of the link to go back to /logon"
            },
            "companyError": {
              "type": "string",
              "description": "Error message when company not provided"
            },
            "companyLabel": {
              "type": "string",
              "description": "Label of company field"
            },
            "emailAccessDomainError": {
              "type": "string",
              "description": "Error message when a user has valid social login but doesn't match specified email domains."
            },
            "emailCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission using email auth"
            },
            "emailCodeCancel": {
              "type": "string"
            },
            "emailCodeError": {
              "type": "string"
            },
            "emailCodeFieldLabel": {
              "type": "string"
            },
            "emailCodeMessage": {
              "type": "string"
            },
            "emailCodeSubmit": {
              "type": "string"
            },
            "emailCodeTitle": {
              "type": "string"
            },
            "emailError": {
              "type": "string",
              "description": "Error message when email not provided"
            },
            "emailFieldLabel": {
              "type": "string"
            },
            "emailLabel": {
              "type": "string",
              "description": "Label of email field"
            },
            "emailMessage": {
              "type": "string"
            },
            "emailSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button using email auth"
            },
            "emailTitle": {
              "type": "string",
              "description": "Title for the Email registration"
            },
            "field1Error": {
              "type": "string",
              "description": "Error message when field1 not provided"
            },
            "field1Label": {
              "type": "string",
              "description": "Label of field1"
            },
            "field2Error": {
              "type": "string",
              "description": "Error message when field2 not provided"
            },
            "field2Label": {
              "type": "string",
              "description": "Label of field2"
            },
            "field3Error": {
              "type": "string",
              "description": "Error message when field3 not provided"
            },
            "field3Label": {
              "type": "string",
              "description": "Label of field3"
            },
            "field4Error": {
              "type": "string",
              "description": "Error message when field4 not provided"
            },
            "field4Label": {
              "type": "string",
              "description": "Label of field4"
            },
            "marketingPolicyLink": {
              "type": "string",
              "description": "label of the link to go to /marketing_policy"
            },
            "marketingPolicyOptIn": {
              "type": "boolean",
              "description": "Whether marketing policy optin is enabled"
            },
            "marketingPolicyOptInLabel": {
              "type": "string",
              "description": "label for marketing optin"
            },
            "marketingPolicyOptInText": {
              "type": "string",
              "description": "marketing policy text"
            },
            "message": {
              "type": "string"
            },
            "nameError": {
              "type": "string",
              "description": "Error message when name not provided"
            },
            "nameLabel": {
              "type": "string",
              "description": "Label of name field"
            },
            "optoutLabel": {
              "type": "string",
              "description": "Label for Do Not Store My Personal Information"
            },
            "pageTitle": {
              "type": "string"
            },
            "passphraseCancel": {
              "type": "string",
              "description": "Label for the Passphrase cancel button"
            },
            "passphraseError": {
              "type": "string",
              "description": "Error message when invalid passphrase is provided"
            },
            "passphraseLabel": {
              "type": "string",
              "description": "Passphrase"
            },
            "passphraseMessage": {
              "type": "string"
            },
            "passphraseSubmit": {
              "type": "string",
              "description": "Label for the Passphrase submit button"
            },
            "passphraseTitle": {
              "type": "string",
              "description": "Title for passphrase details page"
            },
            "privacyPolicyAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to Privacy Policy"
            },
            "privacyPolicyError": {
              "type": "string",
              "description": "Error message when Privacy Policy not accepted"
            },
            "privacyPolicyLink": {
              "type": "string",
              "description": "Label of the link to go to Privacy Policy"
            },
            "privacyPolicyText": {
              "type": "string",
              "description": "Text of the Privacy Policy"
            },
            "requiredFieldLabel": {
              "type": "string",
              "description": "Label to denote required field"
            },
            "signInLabel": {
              "type": "string",
              "description": "Label of the button to signin"
            },
            "smsCarrierDefault": {
              "type": "string"
            },
            "smsCarrierError": {
              "type": "string"
            },
            "smsCarrierFieldLabel": {
              "type": "string",
              "description": "Label for mobile carrier drop-down list"
            },
            "smsCodeCancel": {
              "type": "string",
              "description": "Label for cancel confirmation code submission"
            },
            "smsCodeError": {
              "type": "string",
              "description": "Error message when confirmation code is invalid"
            },
            "smsCodeFieldLabel": {
              "type": "string"
            },
            "smsCodeMessage": {
              "type": "string"
            },
            "smsCodeSubmit": {
              "type": "string",
              "description": "Label for confirmation code submit button"
            },
            "smsCodeTitle": {
              "type": "string"
            },
            "smsCountryFieldLabel": {
              "type": "string"
            },
            "smsCountryFormat": {
              "type": "string"
            },
            "smsHaveAccessCode": {
              "type": "string",
              "description": "Label for checkbox to specify that the user has access code"
            },
            "smsMessageFormat": {
              "type": "string",
              "description": "Format of access code sms message. {{code}} and {{duration}} are placeholders and should be retained as is."
            },
            "smsNumberCancel": {
              "type": "string",
              "description": "Label for canceling mobile details for SMS auth"
            },
            "smsNumberError": {
              "type": "string"
            },
            "smsNumberFieldLabel": {
              "type": "string",
              "description": "Label for field to provide mobile number"
            },
            "smsNumberFormat": {
              "type": "string"
            },
            "smsNumberMessage": {
              "type": "string"
            },
            "smsNumberSubmit": {
              "type": "string",
              "description": "Label for submit button for code generation"
            },
            "smsNumberTitle": {
              "type": "string",
              "description": "Title for phone number details"
            },
            "smsUsernameFormat": {
              "type": "string"
            },
            "sponsorBackLink": {
              "type": "string"
            },
            "sponsorCancel": {
              "type": "string"
            },
            "sponsorEmail": {
              "type": "string",
              "description": "Label for Sponsor Email"
            },
            "sponsorEmailError": {
              "type": "string"
            },
            "sponsorInfoApproved": {
              "type": "string"
            },
            "sponsorInfoDenied": {
              "type": "string"
            },
            "sponsorInfoPending": {
              "type": "string"
            },
            "sponsorName": {
              "type": "string",
              "description": "Label for Sponsor Name"
            },
            "sponsorNameError": {
              "type": "string"
            },
            "sponsorNotePending": {
              "type": "string"
            },
            "sponsorRequestAccess": {
              "type": "string",
              "description": "Submit button label request Wifi Access and notify sponsor about guest request"
            },
            "sponsorStatusApproved": {
              "type": "string",
              "description": "Text to display if sponsor approves request"
            },
            "sponsorStatusDenied": {
              "type": "string",
              "description": "Text to display when sponsor denies request"
            },
            "sponsorStatusPending": {
              "type": "string",
              "description": "Text to display if request is still pending"
            },
            "sponsorSubmit": {
              "type": "string",
              "description": "Submit button label to notify sponsor about guest request"
            },
            "sponsorsError": {
              "type": "string"
            },
            "sponsorsFieldLabel": {
              "type": "string"
            },
            "tosAcceptLabel": {
              "type": "string",
              "description": "Prefix of the label of the link to go to tos"
            },
            "tosError": {
              "type": "string",
              "description": "Error message when tos not accepted"
            },
            "tosLink": {
              "type": "string",
              "description": "Label of the link to go to tos"
            },
            "tosText": {
              "type": "string",
              "description": "Text of the Terms of Service"
            }
          }
        }
      },
      "required": [
        "pageTitle"
      ],
      "description": "Portal template wlan settings"
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.wlans.updateSiteWlanPortalTemplate()`

## Usage Context

Updates the captive portal template for a specific WLAN.

## Gotchas

- Template changes are applied immediately. Test in a non-production WLAN first.

## Related Endpoints

- [PUT_sites_site_id_wlans_wlan_id.md](PUT_sites_site_id_wlans_wlan_id.md) — Update WLAN
- [POST_sites_site_id_wlans_wlan_id_portal_image.md](POST_sites_site_id_wlans_wlan_id_portal_image.md) — Upload portal image

## MistHelper Notes

Not currently used by MistHelper directly.
