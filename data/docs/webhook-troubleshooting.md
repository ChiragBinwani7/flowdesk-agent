# Webhook Troubleshooting Guide

**Applies to:** All FlowDesk versions
**Last updated:** 2025-06-01

## Overview

FlowDesk webhooks deliver real-time event notifications to your specified endpoints. When webhooks fail, events may be missed, causing integration issues.

## Common Issues

### 1. Webhooks Not Delivering

**Symptoms:**
- No events received at your endpoint
- All deliveries showing "failed" status in the dashboard

**Checks:**
- Verify the destination URL is publicly reachable (not behind a VPN or firewall)
- Ensure the URL responds to HTTP POST with a 2xx status code within 5 seconds
- Check that your server accepts `Content-Type: application/json`
- Verify your endpoint is not blocking FlowDesk IP ranges:
  ```
  34.120.0.0/16
  35.190.0.0/17
  104.198.0.0/16
  ```
- Check DNS resolution from an external network

### 2. Invalid Signature

**Symptoms:**
- Webhook events are received but signature verification fails
- "X-FlowDesk-Signature" header does not match

**Resolution:**
1. Compare the signing secret in FlowDesk (Settings > Integrations > Webhooks) with your endpoint
2. Regenerate the secret if it has been compromised
3. Ensure your verification code uses HMAC-SHA256:
   ```python
   import hmac, hashlib
   expected = hmac.new(
       secret.encode(), payload, hashlib.sha256
   ).hexdigest()
   ```
4. The raw request body must be used (before any JSON parsing)

### 3. Payload Mismatch

**Symptoms:**
- Your endpoint receives events but cannot parse them
- Missing fields in the payload

**Resolution:**
- Ensure your parser handles the webhook payload schema
- In v3.2+, the payload includes `event_id` and `timestamp` fields at the top level
- Check the webhook event type documentation for the expected schema

### 4. Rate Limiting

**Symptoms:**
- Your endpoint returns HTTP 429 Too Many Requests
- Some events are delivered but others are missing

**Resolution:**
- FlowDesk delivers up to 50 events per second
- If your endpoint cannot handle this rate, implement a queue
- FlowDesk retries failed deliveries with exponential backoff (1min, 5min, 15min, 1hr, 6hr, 24hr)
- After 7 failed retries, the webhook is disabled and you are notified by email

### 5. SSL/TLS Errors

**Symptoms:**
- All deliveries fail with "SSL handshake failed"

**Resolution:**
- Your endpoint must present a valid, non-expired SSL certificate
- Self-signed certificates are not supported
- The certificate must be issued by a trusted CA
- Check certificate expiry date

### 6. Network Timeout

**Symptoms:**
- Deliveries show "timeout" after 5 seconds

**Resolution:**
- Your endpoint must respond within 5 seconds
- If processing takes longer, acknowledge immediately (return 200) and process asynchronously
- Check server load and database query performance

## Collecting Delivery Logs

For unresolved issues, collect webhook delivery logs:

1. Go to **Settings > Integrations > Webhooks**
2. Click on the affected webhook
3. Go to the **Delivery Log** tab
4. Export the last 50 delivery attempts
5. Attach the log to your support ticket

## Testing Your Webhook

Use the **Send Test Event** button in the webhook configuration page to send a sample payload to your endpoint. This helps isolate whether the issue is with your endpoint or FlowDesk.
