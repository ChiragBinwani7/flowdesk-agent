# SAML SSO Setup (FlowDesk v3.x)

**Applies to:** FlowDesk versions 3.0 and above
**Last updated:** 2025-03-01

## Overview

SAML 2.0 Single Sign-On allows your organization to authenticate FlowDesk users through your existing identity provider (IdP). Starting from version 3.0, SAML SSO is available to a broader set of plans.

## Availability

| Plan       | SAML SSO Support | Max IdPs |
|------------|-----------------|----------|
| Starter    | Not available   | —        |
| Pro        | Not available   | —        |
| Business   | Available       | 3        |
| Enterprise | Available       | Unlimited |

## Setup Instructions

### Step 1: Navigate to Security Settings

Go to **Settings > Security > Single Sign-On**.

### Step 2: Choose Protocol

Select **SAML 2.0** as your SSO protocol (OpenID Connect is also available for Enterprise plans).

### Step 3: Enter IdP Details

| Field              | Description                                      |
|--------------------|--------------------------------------------------|
| IdP Entity ID      | The Entity ID from your IdP metadata              |
| SSO URL            | The Single Sign-On service URL                    |
| X.509 Certificate  | The public certificate from your IdP (PEM format) |

### Step 4: Configure Attribute Mapping

Map the following attributes:

```yaml
email: user.email
first_name: user.firstName
last_name: user.lastName
role: user.groups[0]    # Optional — maps to FlowDesk role
```

### Step 5: Enable and Enforce

1. Toggle **Enable SSO** to activate.
2. Test with a pilot user.
3. Toggle **Enforce SSO** to require SSO for all users.

> **Tip:** Use the **SSO Login Test** button to validate with a real IdP login before enforcing.

## SCIM Provisioning

SCIM is **included** for both Business and Enterprise plans in v3.x. No separate add-on required.

To enable SCIM:
1. Go to **Settings > Security > Provisioning**
2. Toggle **Enable SCIM**
3. Copy the SCIM endpoint URL and bearer token
4. Configure your IdP with the endpoint and token

## What's New in v3.x (vs v2.x)

- SAML SSO available for Business plans (not just Enterprise)
- Support for up to 3 IdPs on Business, unlimited on Enterprise
- SCIM included at no extra cost for Business and Enterprise
- Just-In-Time (JIT) user provisioning
- Configurable session timeout (1-72 hours)
- IdP-initiated logout (SLO) support
- SAML request signing option

## Troubleshooting

### "SSO option unavailable in settings"
Your plan does not support SAML SSO. Available for Business and Enterprise plans only.

### "Certificate expired"
Rotate your IdP certificate and update the X.509 Certificate field in FlowDesk.

### "User not provisioned"
If SCIM is enabled, check the provisioning logs. If SCIM is not enabled, users must be created manually before SSO login.

### "Role mapping incorrect"
Verify your SAML attribute mapping, especially the role attribute. Use the **Preview Mapping** tool in the SSO settings page.

### Upgrade from v2.x
If you're upgrading from v2.x to v3.x with an existing Enterprise SSO configuration, your settings will be migrated automatically. Business plan customers upgrading from v2.x will need to configure SSO from scratch.
