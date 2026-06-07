# CSV Export Limits (FlowDesk v3.x)

**Applies to:** FlowDesk versions 3.0 and above
**Last updated:** 2025-03-01

## Plan Limits

| Plan       | Max Rows Per Export |
|------------|--------------------|
| Starter    | 5,000              |
| Pro        | 10,000             |
| Business   | 50,000             |
| Enterprise | 500,000            |

## Error Code FD-4297

Error **FD-4297** indicates the export job exceeded your plan's row limit.

### Common Causes

1. The dataset returned by your filters contains more rows than your plan allows
2. The export includes all columns, increasing file size beyond implicit limits
3. Scheduled exports accumulated more data than a single export can handle
4. The row count includes child/related records (e.g., line items within invoices)

### Resolution Steps

1. **Check your current row count** — the error message includes the actual row count and your plan limit
2. **Apply filters** to reduce the dataset before exporting
3. **Split by date range** — export one month or quarter at a time
4. **Split by category** — export one department/team at a time
5. **Remove unused columns** from the export configuration
6. **Use the Export Scheduler** — set up recurring exports that each stay within limits
7. **Upgrade your plan** — Business (50K) or Enterprise (500K) plans have higher limits
8. **Contact support** — Enterprise customers can request custom limits

### Example

If you're on a Business plan (50,000 row limit) and your dataset has 72,000 rows:

```
✗ Single export of all 72,000 rows → FD-4297
✓ Export Jan–Jun (36,000 rows) + Export Jul–Dec (36,000 rows)
✓ Apply department filter → Export Sales (45,000) + Export Marketing (27,000)
```

## Export Timeouts

Exports taking longer than 10 minutes time out with error **FD-4300**. This was improved from 5 minutes in v2.x.

Additional improvements in v3.x:
- Export progress bar shows real-time percentage
- Failed exports can be resumed from where they stopped
- Scheduled exports auto-retry up to 3 times

## New in v3.x

- **Export Scheduler**: Schedule recurring exports (daily, weekly, monthly)
- **Export Formats**: CSV and JSON formats available
- **Incremental Exports**: Export only records changed since last export
- **Webhook Notifications**: Get notified when scheduled exports complete or fail

## CSV Format Notes

- All CSV exports use UTF-8 encoding with BOM
- Date columns use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Null values are represented as empty fields
- Maximum file size: 250 MB (all plans)
- Column selection available in the export dialog
