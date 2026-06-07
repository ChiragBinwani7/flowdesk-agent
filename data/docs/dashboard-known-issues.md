# Dashboard Known Issues and Workarounds

**Applies to:** All FlowDesk versions
**Last updated:** 2025-06-01

## Current Issues

### 1. Slow Dashboard Loading

**Status:** Under investigation — see incident-status page for your region.

**Symptoms:**
- Dashboard takes 5-15 seconds to load (normal is under 2 seconds)
- Widgets appear one at a time with significant delay
- "Loading..." spinner persists

**Affected Regions:** May vary. Check the incident API for your region.

**Workaround:**
- Switch to a simpler dashboard layout with fewer widgets
- Use the "Basic View" toggle in the top-right corner
- Access individual widget data via the API directly
- Export dashboard data to CSV and review offline

**Technical Note:** The dashboard relies on real-time data APIs. Regional API latency directly affects dashboard performance.

### 2. Blank Widgets

**Symptoms:**
- One or more widgets show empty/blank instead of data
- No error message displayed

**Resolutions:**
1. Clear browser cache and hard-reload (Ctrl+Shift+R)
2. Check that ad-blockers or privacy extensions are not blocking FlowDesk analytics scripts
3. Verify the widget's data source is still valid (e.g., the saved filter hasn't been deleted)
4. Remove and re-add the affected widget

### 3. Data Discrepancy

**Symptoms:**
- Dashboard shows different numbers than raw API queries
- Counts don't match between widgets

**Explanation:**
- Dashboard refreshes every 5 minutes for Starter/Pro plans
- Dashboard refreshes every 60 seconds for Business plans
- Dashboard refreshes every 30 seconds for Enterprise plans (v3.2+)
- Data is cached at the widget level — different widgets may reflect different cache states

**Resolution:**
- Click the refresh icon on individual widgets
- Compare with raw API data using the API Explorer (Developer > API Explorer)
- Wait for the next refresh cycle

### 4. Custom Date Range Filter Not Working

**Affected Versions:** v3.1 only (fixed in v3.2)

**Symptoms:**
- Selecting a custom date range has no effect
- Widget shows "All time" data regardless of date selection

**Workarounds:**
- Use preset date ranges (Today, This Week, This Month, Last Month) instead of custom
- Upgrade to v3.2 where this is fixed
- Use the API with date parameters as a temporary alternative

### 5. Export from Dashboard

Dashboard exports are subject to your plan's CSV export limits:
- Starter: 5,000 rows
- Pro: 10,000 rows
- Business: 50,000 rows
- Enterprise: 500,000 rows

Large dashboards with many rows may need to be exported in sections. Use filters to reduce the dataset before exporting.

### 6. Real-Time Updates Lag

**Symptoms:**
- Changes in the system are not reflected on the dashboard for several minutes

**Expected Refresh Intervals:**
- v2.x: 5 minutes (all plans)
- v3.0 - v3.1: 5 minutes (Starter/Pro), 1 minute (Business/Enterprise)
- v3.2+: 5 minutes (Starter/Pro), 1 minute (Business), 30 seconds (Enterprise)

## Reporting New Issues

To report a dashboard issue not listed here:
1. Note your FlowDesk version and plan
2. Take a screenshot of the issue
3. Open browser developer console (F12) and capture any errors
4. Include the dashboard URL and affected widgets
5. Create a support ticket with category "dashboard"
