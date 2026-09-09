# Data sources and input contract

The original US research assembled public-source macroeconomic and market observations. No original CSV, spreadsheet, PDF or provider export is included here. Data access and reuse remain subject to each provider's terms; a synthetic generator keeps the public demo reproducible without redistributing those files.

## Required quarterly input

| Column | Meaning and original source | Original aggregation |
|---|---|---|
| `Date` | Calendar quarter, e.g. `2000Q1` | Unique, contiguous quarters |
| `GDP` | BEA Table 1.1.6, real GDP, billions of chained 2017 USD, seasonally adjusted annual rate | Quarterly level |
| `S&P500` | S&P 500 closing level, Yahoo Finance `^GSPC` | Last available daily close |
| `VIX` | VIX closing level, Yahoo Finance `^VIX` | Last available daily close |
| `M2` | FRED `M2SL`, seasonally adjusted money stock | Last monthly observation |
| `Credit` | BIS total credit to US private non-financial sector, `Q.US.P.A.M.XDC.U` | Quarterly observation |
| `Rate` | FRED `FEDFUNDS`, percent | Last monthly observation |
| `Yield10` | FRED `DGS10`, percent | Last available daily observation |
| `GS2` | FRED `GS2`, percent | Last monthly observation |

The source workbook identifies its GDP vintage as revised September 25, 2025. The local merged dataset used for the portfolio rerun contains 1980Q1–2024Q4. VIX is unavailable in its first 40 quarters. The precise vintage of every other observation is not fully recorded.

**Yield-frequency limitation:** the original 10-year series is daily, while the 2-year series is monthly. Their quarter-end difference combines different observation conventions. This is preserved and disclosed; a future ingestion revision should harmonize the frequencies before comparing economic interpretations.

Input `Spread` columns, if present, are ignored. The core recomputes `Yield10 - GS2` to prevent inconsistent sign conventions. Extra input columns are ignored. Duplicate quarters, absent calendar rows, infinite numbers and invalid positive levels are rejected. Missing observations remain missing, with no forward fill.

## Source references

- [BEA GDP](https://www.bea.gov/data/gdp/gross-domestic-product) and [quarterly versus annualized growth](https://www.bea.gov/help/faq/122).
- [FRED DGS10](https://fred.stlouisfed.org/series/DGS10), [GS2](https://fred.stlouisfed.org/series/GS2), [FEDFUNDS](https://fred.stlouisfed.org/series/FEDFUNDS), [M2SL](https://fred.stlouisfed.org/series/M2SL).
- [BIS credit statistics](https://data.bis.org/topics/TOTAL_CREDIT).
- [Yahoo S&P 500](https://finance.yahoo.com/quote/%5EGSPC/history/) and [VIX](https://finance.yahoo.com/quote/%5EVIX/history/).
- [FRED terms](https://fred.stlouisfed.org/legal/terms/).

Historical data are not bundled, so the exact real-data result cannot be independently reconstructed from this repository alone. The public notebooks, synthetic fixtures and tests can be reproduced in full.
