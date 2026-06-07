# FlowDesk Release Notes — Version 3.1

**Release Date:** 2025-09-15
**End of Support:** 2026-09-15

## New Features

### Custom Dashboard Widgets
Create custom widgets using SQL-like queries or the visual query builder. Available for Business and Enterprise plans.

### Webhook Retry Policies
Configure custom retry policies per webhook endpoint. Control retry count, backoff strategy, and failure notifications.

### Bulk User Import
Import users in bulk via CSV upload. Supports up to 10,000 users per import. Includes validation preview before committing.

### Enhanced Audit Logs
Audit logs now support advanced filtering by user, action type, date range, and resource type. Export audit logs as CSV or JSON.

## Breaking Changes

### Legacy API v1 Deprecation
API v1 endpoints are now deprecated and will be removed on **2026-03-01**. Migrate to API v2 before this date.

**Migrating from v1 to v2:**
- Base URL changes from `/api/v1/` to `/api/v2/`
- Response format is now JSON:API compliant
- Pagination uses cursor-based pagination instead of offset-based
- Authentication uses Bearer tokens instead of API keys

## Known Issues

- **Custom date-range filter on dashboards** may not apply correctly. Use preset date ranges as a workaround. Fix planned for v3.2.
- **SSO certificate rotation** now requires explicit admin confirmation, which may cause confusion for automated rotation pipelines.
- **Bulk user import** may fail silently for CSV files with BOM markers. Resave as UTF-8 without BOM.

## Bug Fixes

- Fixed CSV export timeout for files larger than 25,000 rows (previously timed out at 5 minutes)
- Fixed webhook signature verification for URL-encoded payloads
- Fixed SCIM user deprovisioning race condition during bulk operations
- Fixed dashboard memory leak affecting long-running sessions (>8 hours)
- Fixed search returning deleted (soft-deleted) records

## Performance Improvements

- Dashboard load times improved by 40% (caching layer rewrite)
- Search indexing reduced from 15 minutes to 3 minutes
- API response times improved by 25% (connection pooling)

## Plan Changes

- CSV export limits increased for Pro (5,000 → 10,000) and Business (25,000 → 50,000)
- API rate limits increased for all plans

## Security

- Added support for SAML request signing
- Session token rotation on password change
- Rate limiting on login endpoints (5 attempts per minute per IP)

## Upgrade Notes

Upgrading from v3.0 to v3.1:
1. No database migration required
2. Review API v1 usage and plan migration to v2
3. Test SSO configuration after upgrade (certificate rotation behavior changed)
4. Update webhook endpoints if using signature verification (payload encoding fix may affect verification logic)
