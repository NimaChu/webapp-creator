# Dashboard Patterns

## Start From Decisions

A dashboard should answer a bounded question. Organize it as:

1. Scope and freshness: period, source, filters, and last refresh.
2. Headline measures: only KPIs needed to orient the reader.
3. Main comparison or trend: the visual that answers the central question.
4. Drivers and exceptions: why the number changed and where attention is needed.
5. Detail: an accessible table or drill-down list.

Do not fill the viewport with interchangeable KPI cards. If a metric does not change a decision, move it to detail or omit it.

## Chart Selection

- Trend over ordered time: line chart; use bars when periods are discrete and few.
- Category comparison: horizontal bar chart, sorted by value when order is not semantic.
- Part-to-whole: stacked bar for comparison across groups; avoid multiple pie charts.
- Distribution: histogram or box plot when the library supports it.
- Relationship: scatter plot with explicit units and a useful tooltip.
- Process or conversion: funnel only when each stage is a true subset of the previous stage.
- Exact values and many dimensions: table with alignment, sorting, and optional highlighting.

Avoid dual axes unless the relationship is essential and clearly labeled. Do not use 3D charts.

## Numeric Formatting

Keep raw values numeric in the data model and format only at render time. Use `Intl.NumberFormat` for locale-aware output.

- Counts: grouped thousands, no unnecessary decimals.
- Percentages: usually one decimal; state whether the source uses `0.23` or `23`.
- Currency: include currency code or symbol and consistent compact units.
- Duration: human-readable units appropriate to scale.
- Missing values: use a deliberate symbol and explanation; never silently coerce to zero.

Use tabular numbers for KPI values and numeric table columns.

## Interaction

- Filters must show the active scope and offer a clear reset.
- Hover cannot be the only way to access important information.
- Keep chart and table filters synchronized.
- Resize chart instances when their container or viewport changes.
- Preserve user-selected filters when switching dashboard sections unless reset is explicit.
- Provide a textual insight summary based on the same data, not a hard-coded claim.

## Data Integrity

- Never invent production or company data.
- If sample data is needed to develop the layout, label it in the interface and source.
- Keep units, denominator, time zone, and date range explicit.
- Validate totals and percentages before visual QA.
- Escape untrusted strings before inserting them into HTML; prefer DOM APIs over `innerHTML` for external data.

## Implementation Choice

Use native HTML/CSS/SVG for a small number of static bars or progress indicators. For multiple interactive charts, use a proven chart engine already available in the host project. If a CDN is used, the tool is not fully offline; disclose that tradeoff and consider bundling the dependency when licensing and package size allow it.
