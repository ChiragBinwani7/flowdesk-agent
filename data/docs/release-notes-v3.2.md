# FlowDesk Release Notes — Version 3.2

**Release Date:** 2026-02-01
**End of Support:** 2027-02-01

## New Features

### AI-Powered Anomaly Detection
Dashboard widgets now include automatic anomaly detection. Unusual spikes or drops are highlighted with explanations. Available for Business and Enterprise plans.

### OAuth 2.0 Device Flow
CLI tools and headless applications can now authenticate using OAuth 2.0 Device Authorization Grant. See Developer > API > OAuth for setup instructions.

### Advanced Export Scheduling
Schedule recurring exports with advanced options:
- Daily, weekly, or monthly schedules
- CSV or JSON format
- Incremental exports (changed records only)
- Email or webhook delivery
- Custom column selection per schedule

## Breaking Changes

### Webhook Payload Format Update
Webhook payloads now include `event_id` (UUID v4) and `timestamp` (ISO 8601) fields at the top level:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-01T12:00:00Z",
  "event_type": "user.created",
  "data": { ... }
}
```

If your webhook handler validates against a strict schema, update it to accept the new fields. The old payload format (without these fields) is no longer supported.

## Bug Fixes

- Fixed custom date-range filter on dashboards (known issue from v3.1)
- Fixed SAML SSO attribute mapping for nested groups (groups within organizational units)
- Fixed CSV export progress indicator for files larger than 100,000 rows
- Fixed webhook delivery to IPv6-only endpoints
- Fixed concurrent session limit not being enforced for SSO users
- Fixed dashboard export respecting column visibility settings

## Performance Improvements

- Dashboard load times improved by additional 25% (cumulative ~65% improvement since v3.0)
- Real-time data refresh interval reduced to 30 seconds for Business and Enterprise plans
- Search indexing now incremental (updates only changed records)
- Webhook delivery pipeline optimized for 3x throughput

## Plan Changes

- Starter plan CSV export increased from 1,000 to 5,000 rows
- All plans now support webhook retry policies
- Starter plan webhook limit increased from 3 to 5 endpoints

## Security

- Added OAuth 2.0 token revocation endpoint
- PKCE required for all OAuth authorization code flows
- Session hijacking detection based on IP/User-Agent changes
- Security event logging to dedicated audit trail

## Upgrade Notes

Upgrading from v3.1 to v3.2:
1. No database migration required
2. Webhook handlers must be updated to accept `event_id` and `timestamp` top-level fields
3. OAuth clients using authorization code flow must implement PKCE
4. Custom date-range filter now works correctly — remove workarounds
5. All existing SSO configurations migrate automatically

## Deprecation Notice

- API v1 endpoints will be removed on 2026-03-01 (as announced in v3.1)
- Legacy audit log format will be removed in v3.3
