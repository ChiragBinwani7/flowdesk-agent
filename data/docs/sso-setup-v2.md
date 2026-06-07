# SAML SSO Setup (FlowDesk v2.x)

**Applies to:** FlowDesk versions 2.0 through 2.9
**Last updated:** 2024-01-15

## Overview

SAML 2.0 Single Sign-On allows your organization to authenticate FlowDesk users through your existing identity provider (IdP).

## Availability

| Plan       | SAML SSO Support |
|------------|-----------------|
| Starter    | Not available   |
| Pro        | Not available   |
| Business   | Not available   |
| Enterprise | Available       |

SAML SSO is available **only** for Enterprise customers in version 2.x.

## Setup Instructions

### Step 1: Access SSO Settings

Navigate to **Admin > Authentication > SAML SSO**.

> **Note:** This menu item is only visible for Enterprise accounts.

### Step 2: Upload IdP Metadata

1. Download the metadata XML from your identity provider (Okta, Azure AD, OneLogin, etc.)
2. Click **Upload Metadata** in FlowDesk
3. Select the XML file and confirm

### Step 3: Map User Attributes

FlowDesk requires the following SAML attributes:

| SAML Attribute       | FlowDesk Field | Required |
|---------------------|----------------|----------|
| email               | Email          | Yes      |
| firstName           | First Name     | Yes      |
| lastName            | Last Name      | Yes      |
| role                | Role           | No       |

### Step 4: Test Connection

Click **Test SSO Connection** to verify the configuration before enforcing SSO.

### Step 5: Enforce SSO

Toggle **Enforce SSO** to require all users to authenticate through your IdP.

> **Warning:** Before enforcing, ensure at least one admin user has successfully tested SSO login. You may lock yourself out otherwise.

## SCIM Provisioning

SCIM (System for Cross-domain Identity Management) provisioning requires a **separate Enterprise add-on** in version 2.x. It is not included in the base Enterprise plan.

Contact your account manager to enable SCIM.

## Limitations in v2.x

- Only 1 SAML identity provider supported per account
- No Just-In-Time (JIT) provisioning
- Session timeout fixed at 8 hours (not configurable)
- No support for IdP-initiated logout (SLO)
- SCIM requires separate add-on purchase

## Troubleshooting

### "SSO Configuration Not Found"
Your plan does not include SAML SSO. Upgrade to Enterprise or contact sales.

### "Invalid IdP Certificate"
Ensure the certificate in your metadata XML is valid and not expired.

### "Attribute Mapping Failed"
Verify that your IdP is sending all required attributes and that attribute names match exactly.
