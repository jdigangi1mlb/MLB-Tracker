# MLB Trade Deadline Tracker 2026

Required ledgers:

- MLB.com: https://www.mlb.com/amp/news/mlb-trade-deadline-2026-deal-tracker.html
- CBS Sports: https://www.cbssports.com/mlb/news/mlb-trade-deadline-tracker-2026/

## Five-minute update behavior

The scheduled workflow runs at minutes 2, 7, 12, 17, and so on.

- It publishes a static GitHub Pages tracker.
- It creates a GitHub issue only when the canonical ledger changes.
- It fails closed if either parser returns an unexpectedly incomplete ledger.
- MLB.com controls dates, ordering, teams, and return wording whenever it lists the trade.
- Exactly 10 trades appear in each vertically stacked page section.

## One-time activation

1. Create a GitHub repository.
2. Upload this package to the repository root.
3. Go to **Settings → Pages** and select **GitHub Actions**.
4. Go to **Actions → Update MLB Trade Tracker → Run workflow**.
5. Select **Watch → All Activity** to receive the change-only GitHub issue alerts.
