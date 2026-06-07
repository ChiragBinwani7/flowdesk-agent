# CSV Export Limits (FlowDesk v2.x)

**Applies to:** FlowDesk versions 2.0 through 2.9
**Last updated:** 2024-01-01

## Plan Limits

| Plan       | Max Rows Per Export |
|------------|--------------------|
| Starter    | 1,000              |
| Pro        | 5,000              |
| Business   | 25,000             |
| Enterprise | 100,000            |

## Error Code FD-4297

Error **FD-4297** indicates the export job exceeded your plan's row limit.

### Common Causes

1. The dataset returned by your filters contains more rows than your plan allows
2. The export includes all columns, increasing file size beyond implicit limits
3. Scheduled exports accumulated more data than a single export can handle

### Resolution Steps

1. **Apply filters** to reduce the dataset before exporting
2. **Split by date range** — export January, February, etc. separately
3. **Split by category** — export one department at a time
4. **Remove unused columns** from the export configuration
5. **Contact support** to request a temporary limit increase (Enterprise customers only)

### Example

If you're on a Business plan (25,000 row limit) and your dataset has 40,000 rows:

```
✗ Single export of all 40,000 rows → FD-4297
✓ Export Jan–Jun (20,000 rows) + Export Jul–Dec (20,000 rows)
```

## Export Timeouts

Exports that take longer than 5 minutes will time out with error **FD-4300**. This is more common with:
- Datasets near the row limit
- Exports with many columns (50+)
- Scheduled exports during peak hours

Workarounds:
- Export during off-peak hours
- Reduce column count
- Use the API for programmatic, paginated access

## CSV Format Notes

- All CSV exports use UTF-8 encoding
- Date columns use ISO 8601 format (YYYY-MM-DD)
- Null values are represented as empty fields
- Maximum file size: 100 MB (all plans)
