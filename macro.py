"""Quarterly macroeconomic research, extracted from an exploratory notebook project."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LEVELS = ['GDP', 'S&P500', 'VIX', 'M2', 'Credit', 'Rate', 'Yield10', 'GS2']
FINANCIAL = ['SP500_ret', 'M2_qoq', 'Credit_qoq', 'Rate_diff', 'Spread_lvl', 'VIX_diff']


def validate_levels(frame: pd.DataFrame) -> pd.DataFrame:
    """Require unique, contiguous quarters; preserve unavailable observations."""
    missing = set(['Date', *LEVELS]) - set(frame.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    out = frame[['Date', *LEVELS]].copy()
    out.index = pd.PeriodIndex(out.pop('Date'), freq='Q')
    if out.index.hasnans or out.index.has_duplicates:
        raise ValueError('Quarter keys must be valid and unique')
    out = out.sort_index()
    if len(out) < 8 or not out.index.equals(pd.period_range(out.index[0], out.index[-1], freq='Q')):
        raise ValueError('Expected at least eight contiguous quarters; gaps must be explicit rows')
    out = out.apply(pd.to_numeric, errors='raise')
    if np.isinf(out.to_numpy(dtype=float)).any():
        raise ValueError('Infinite observations are invalid')
    positive = out[['GDP', 'S&P500', 'M2', 'Credit']]
    if (positive <= 0).any().any():
        raise ValueError('GDP, market, money and credit levels must be positive when present')
    return out


def transform(frame: pd.DataFrame) -> pd.DataFrame:
    """Growth in percent; rate differences in percentage points. No filling."""
    levels = validate_levels(frame)
    out = pd.DataFrame(index=levels.index)
    for source, target in [('GDP', 'GDP_qoq'), ('M2', 'M2_qoq'), ('Credit', 'Credit_qoq')]:
        out[target] = levels[source].pct_change(fill_method=None) * 100
    out['GDP_yoy'] = levels.GDP.pct_change(4, fill_method=None) * 100
    out['SP500_ret'] = np.log(levels['S&P500']).diff() * 100
    out['Rate_diff'] = levels.Rate.diff()
    out['Spread_lvl'] = levels.Yield10 - levels.GS2
    out['VIX_diff'] = levels.VIX.diff()
    return out


def supervised(frame: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    """At origin t, use observations through t-1 to predict GDP qoq at t+h.

    A one-quarter lag is an explicit research assumption, not a point-in-time
    release calendar. Revised input vintages still prevent a real-time claim.
    """
    if horizon not in (1, 4):
        raise ValueError('Supported horizons: one or four quarters')
    values = transform(frame)
    out = pd.DataFrame(index=values.index)
    for col in [*FINANCIAL, 'GDP_qoq']:
        for lag in (1, 2):
            out[f'{col}_lag{lag}'] = values[col].shift(lag)
    out['target'] = values.GDP_qoq.shift(-horizon)
    out['target_quarter'] = out.index + horizon
    # Shift on the full calendar BEFORE dropping incomplete records.
    return out.dropna()


def split(frame: pd.DataFrame, cutoff: str = '2020Q1'):
    """Embargo crossing labels: train targets strictly precede cutoff."""
    boundary = pd.Period(cutoff, freq='Q')
    train = frame.loc[frame.target_quarter < boundary]
    test = frame.loc[frame.index >= boundary]
    if len(train) < 40 or len(test) < 4:
        raise ValueError('Need at least 40 training and four test observations')
    return train, test


def evaluate(frame: pd.DataFrame, horizon: int = 1, cutoff: str = '2020Q1'):
    """Frozen training fit; expanding CV with calendar-aware label separation."""
    train, test = split(supervised(frame, horizon), cutoff)
    features = [c for c in train.columns if c not in ('target', 'target_quarter')]
    # Candidate splits use a horizon gap; verify actual dates too (missing rows).
    folds = list(TimeSeriesSplit(n_splits=4, gap=horizon).split(train))
    for fit, validation in folds:
        if train.target_quarter.iloc[fit].max() >= train.index[validation].min():
            raise ValueError('Training label crosses validation origin')
    ridge = GridSearchCV(make_pipeline(StandardScaler(), Ridge()),
                         {'ridge__alpha': [0.1, 1.0, 10.0, 100.0]},
                         cv=folds, scoring='neg_mean_squared_error')
    forest = RandomForestRegressor(n_estimators=100, max_depth=3,
                                   min_samples_leaf=5, random_state=42, n_jobs=1)
    predictions = pd.DataFrame({'actual': test.target,
                                'Last observed growth': test.GDP_qoq_lag1,
                                'Training mean': float(train.target.mean())})
    for name, estimator in [('Ridge', ridge), ('Random forest', forest)]:
        estimator.fit(train[features], train.target)
        predictions[name] = estimator.predict(test[features])
    predictions.index = pd.PeriodIndex(test.target_quarter, freq='Q')
    scores = pd.DataFrame([
        {'model': name, 'RMSE': float(np.sqrt(mean_squared_error(predictions.actual, predictions[name]))),
         'MAE': float(mean_absolute_error(predictions.actual, predictions[name]))}
        for name in predictions.columns if name != 'actual'
    ]).set_index('model')
    return scores, predictions, {
        'horizon_quarters': horizon, 'train_rows': len(train), 'test_rows': len(test),
        'train_last_target': str(train.target_quarter.max()),
        'test_first_origin': str(test.index.min()),
        'test_first_target': str(predictions.index.min()),
        'test_last_target': str(predictions.index.max()),
        'ridge_alpha': ridge.best_params_['ridge__alpha'],
    }


def synthetic_levels() -> pd.DataFrame:
    """Seeded fictitious data for an offline demonstration, not US history."""
    rng = np.random.default_rng(42)
    periods = pd.period_range('1980Q1', '2024Q4', freq='Q')
    n = len(periods)
    data = pd.DataFrame({'Date': periods.astype(str)})
    for col, start, growth, volatility in [('GDP', 7000, .006, .006), ('S&P500', 100, .015, .07),
                                          ('M2', 1500, .012, .007), ('Credit', 2700, .013, .008)]:
        data[col] = start * np.exp(np.cumsum(rng.normal(growth, volatility, n)))
    data['Rate'] = 3 + np.sin(np.arange(n) / 9)
    data['Yield10'] = 4 + rng.normal(0, .4, n)
    data['GS2'] = 3 + rng.normal(0, .5, n)
    data['VIX'] = 20 + rng.normal(0, 3, n)
    return data
