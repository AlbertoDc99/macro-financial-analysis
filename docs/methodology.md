# Methodology and research limits

## Transformations

- GDP, M2 and credit qoq growth: `(level_t / level_t-1 - 1) * 100`.
- GDP yoy growth: `(level_t / level_t-4 - 1) * 100`, not the sum of four qoq rates.
- Equity return: `100 * diff(log(close))`.
- Policy rate and VIX: first differences; policy-rate changes are percentage points, VIX changes are index points.
- Term spread: 10-year yield minus 2-year yield, in percentage points.

GDP qoq growth here is **not annualized**, even though the underlying GDP level is expressed at an annual rate. It differs from the annualized percentage change commonly quoted in BEA releases.

## Temporal evaluation

For an origin quarter t, features contain financial variables and GDP growth at t-1 and t-2. The target is GDP qoq growth at t+1 or t+4. Shifts are calculated on the full continuous calendar before incomplete rows are removed.

The training set only contains targets strictly before 2020Q1. Test origins start at 2020Q1. Training rows with labels crossing that boundary are embargoed. Therefore the first evaluated target is 2020Q2 for h=1 and 2021Q1 for h=4. COVID-era observations are not manually removed.

Ridge selects alpha from four candidates in expanding time-series CV, with a gap equal to the forecast horizon and an explicit date check at each fold. Standardization is inside the fitted pipeline. Random forest uses a deliberately small, fixed configuration rather than selecting it on holdout results. The fitted models are frozen during test evaluation; features advance with each test origin. Last observed GDP growth and the training mean are included as baselines.

There is no full release-time or revision-vintage model. A quarter lag does not guarantee that BIS credit or every other series was actually available at that origin. The code prevents the specified label-overlap error, but it cannot remove vintage leakage from revised source data. Treat all real-data results as retrospective.

## Changes from the original exploratory notebooks

This edition extracts a small Python core and keeps notebooks as the research interface. It removes machine-specific paths and stale outputs, fixes the inconsistent spread sign and yoy calculation, and introduces label-aware holdout separation. It omits pre-CV winsorization and the original large hyperparameter searches. The original custom IRF plots and their confidence bands require separate validation and are not published here.

The scope is transparent: the original notebooks explored more models and econometric techniques than this compact edition exposes. No original score or causal conclusion is carried over as a validated result.

## Next research steps

1. Record source checksums and release timestamps at ingestion.
2. Harmonize the two yield series and evaluate first-release GDP vintages.
3. Reserve a genuinely new holdout before further model selection.
4. Revalidate VAR/IRF identification and uncertainty separately.

Reference: [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
