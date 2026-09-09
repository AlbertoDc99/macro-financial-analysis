import numpy as np
import pytest
from macro import evaluate, split, supervised, synthetic_levels, transform, validate_levels


def test_growth_compounds_and_spread_keeps_definition():
    levels = synthetic_levels()
    levels['GDP'] = 100 * 1.1 ** np.arange(len(levels))
    levels['Yield10'], levels['GS2'] = 5., 3.
    values = transform(levels)
    assert values.GDP_qoq.iloc[4] == pytest.approx(10.)
    assert values.GDP_yoy.iloc[4] == pytest.approx(46.41)
    assert values.Spread_lvl.iloc[4] == 2.


def test_missing_observations_are_not_filled_or_compressed():
    levels = synthetic_levels()
    levels.loc[20, 'GDP'] = np.nan
    assert transform(levels).GDP_qoq.iloc[20:22].isna().all()
    values = supervised(levels, 4)
    assert (values.target_quarter == values.index + 4).all()
    assert '1984Q1' not in values.index.astype(str)  # target is missing at row 20


@pytest.mark.parametrize('horizon', [1, 4])
def test_features_and_labels_stay_on_the_correct_side_of_time(horizon):
    levels = synthetic_levels()
    values = supervised(levels, horizon)
    raw = transform(levels)
    origin = values.index[30]
    assert values.loc[origin, 'GDP_qoq_lag1'] == raw.loc[origin - 1, 'GDP_qoq']
    assert values.loc[origin, 'target'] == raw.loc[origin + horizon, 'GDP_qoq']
    train, test = split(values)
    assert train.target_quarter.max() < test.index.min()
    scores, predictions, metadata = evaluate(levels, horizon)
    assert scores.shape == (4, 2)
    assert np.isfinite(scores.to_numpy()).all()
    assert metadata['test_rows'] == len(predictions)


def test_duplicate_and_missing_quarters_rejected():
    data = synthetic_levels()
    with pytest.raises(ValueError, match='gaps'):
        validate_levels(data.drop(index=5))
    data.loc[1, 'Date'] = data.loc[0, 'Date']
    with pytest.raises(ValueError, match='unique'):
        validate_levels(data)
