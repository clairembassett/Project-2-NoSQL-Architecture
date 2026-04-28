# Downloading Dependencies and Installing Packages if Needed


```python
!pip install pymongo
```

    Collecting pymongo
      Downloading pymongo-4.17.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (10 kB)
    Collecting dnspython<3.0.0,>=2.6.1 (from pymongo)
      Downloading dnspython-2.8.0-py3-none-any.whl.metadata (5.7 kB)
    Downloading pymongo-4.17.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (1.8 MB)
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m1.8/1.8 MB[0m [31m17.1 MB/s[0m eta [36m0:00:00[0m
    [?25hDownloading dnspython-2.8.0-py3-none-any.whl (331 kB)
    [2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m331.1/331.1 kB[0m [31m12.2 MB/s[0m eta [36m0:00:00[0m
    [?25hInstalling collected packages: dnspython, pymongo
    Successfully installed dnspython-2.8.0 pymongo-4.17.0



```python
import csv
import requests
import numpy as np
import pandas as pd
import logging
import sys
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from getpass import getpass
from datetime import datetime, timezone
from pymongo import MongoClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
```

# Loading Data from API Endpoints and Loading into MongoDB


```python
import requests
import csv
import logging
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from getpass import getpass

# Setting Up Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='data_pipeline.log'
)
logger = logging.getLogger(__name__)

# Setting API endpoints, defining sources, and setting units

ENDPOINTS = {
    'temperature':   'https://global-warming.org/api/temperature-api',
    'methane':       'https://global-warming.org/api/methane-api',
    'nitrous_oxide': 'https://global-warming.org/api/nitrous-oxide-api',
}

NOAA_CO2_URL = 'https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv'

SOURCES = {
    'temperature':   ENDPOINTS['temperature'],
    'co2':           NOAA_CO2_URL,
    'methane':       ENDPOINTS['methane'],
    'nitrous_oxide': ENDPOINTS['nitrous_oxide'],
}

UNITS = {
    'temperature':   'degC_anomaly',
    'co2':           'ppm',
    'methane':       'ppb',
    'nitrous_oxide': 'ppb',
}

# Helper functions to clean data

def decimal_year_to_ym(dy):
    # Convert decimal year to YYYY-MM format
    dy = float(dy)
    y = int(dy)
    frac = dy - y
    m = int(round(frac * 12)) + 1
    if m == 13:
        m, y = 1, y + 1
    return f'{y:04d}-{m:02d}'


def safe_float(x):
    # Convert value to float, handling missing sentinel values
    try:
        v = float(x)
        return v if v > -999 else None
    except (TypeError, ValueError):
        return None


def _first_list(payload, preferred_keys=()):
    # Extract first valid list from API payload
    for k in preferred_keys:
        if k in payload and isinstance(payload[k], list):
            return payload[k]
    for v in payload.values():
        if isinstance(v, list):
            return v
    return []


def fetch_all():
    # Fetch data from global-warming API endpoints
    raw = {}
    for name, url in ENDPOINTS.items():
        try:
            logger.info(f"Fetching {name} data...")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            raw[name] = r.json()

            logger.info(f"{name}: keys = {list(raw[name].keys())}")
        except Exception as e:
            logger.error(f"Failed to fetch {name}: {e}")
            sys.exit(1)
    return raw


def fetch_noaa_co2_monthly():
    # Fetch NOAA CO2 monthly dataset
    try:
        logger.info("Fetching NOAA CO2 data...")
        r = requests.get(NOAA_CO2_URL, timeout=30)
        r.raise_for_status()

        lines = [ln for ln in r.text.splitlines()
                 if ln.strip() and not ln.lstrip().startswith('#')]

        reader = csv.DictReader(lines)
        reader.fieldnames = [f.strip() for f in reader.fieldnames]

        out = []
        for row in reader:
            try:
                y = int(row['year'])
                m = int(row['month'])
                ym = f'{y:04d}-{m:02d}'

                avg = safe_float(row.get('average'))
                trend = safe_float(row.get('deseasonalized'))

                if avg is not None and avg >= 0:
                    out.append({'ym': ym, 'value': avg, 'value_trend': trend})

            except Exception:
                continue

        logger.info(f"Parsed {len(out)} CO2 records")
        return out

    except Exception as e:
        logger.error(f"Failed to fetch NOAA CO2: {e}")
        sys.exit(1)

# Normalizing data for continuity

def normalize_temperature(payload):
    # Normalize temperature data
    out = []
    for r in _first_list(payload, ('result',)):
        t = r.get('time') or r.get('date')
        if t is None:
            continue

        v = safe_float(r.get('station') or r.get('land'))
        if v is not None:
            out.append({'ym': decimal_year_to_ym(t), 'value': v})

    logger.info(f"Normalized temperature: {len(out)} records")
    return out


def normalize_decimal_year(payload, keys):
    # Normalize methane and nitrous oxide
    out = []
    for r in _first_list(payload, keys):
        t = r.get('date') or r.get('time')
        if t is None:
            continue

        avg = safe_float(r.get('average'))
        trend = safe_float(r.get('trend'))
        val = avg if avg is not None else trend

        if val is not None:
            out.append({
                'ym': decimal_year_to_ym(t),
                'value': val,
                'value_trend': trend
            })

    logger.info(f"Normalized {keys}: {len(out)} records")
    return out

# Building dataset

def build_series(raw, co2_records):
    # Combine all normalized datasets
    try:
        series = {
            'temperature':   normalize_temperature(raw['temperature']),
            'co2':           co2_records,
            'methane':       normalize_decimal_year(raw['methane'], ('methane',)),
            'nitrous_oxide': normalize_decimal_year(
                raw['nitrous_oxide'],
                ('nitrous oxide', 'nitrousoxide', 'nitrous_oxide')
            ),
        }

        for name, s in series.items():
            logger.info(f"{name}: {len(s)} records")

        return series

    except Exception as e:
        logger.error(f"Error building series: {e}")
        sys.exit(1)

# Loading in to MongoDB

def load_to_mongo(client, series):
    # Load processed data into MongoDB
    try:
        proj = client['ds4320_project']
        raw_col = proj['raw_measurements']
        monthly_col = proj['monthly']

        fetched_at = datetime.now(timezone.utc)

        raw_col.delete_many({})
        monthly_col.delete_many({})

        raw_docs = []
        for name, obs in series.items():
            for o in obs:
                raw_docs.append({
                    'variable': name,
                    'ym': o['ym'],
                    'value': o['value'],
                    'value_trend': o.get('value_trend'),
                    'unit': UNITS[name],
                    'source_url': SOURCES[name],
                    'fetched_at': fetched_at,
                })

        if raw_docs:
            raw_col.insert_many(raw_docs)

        logger.info(f"Inserted {len(raw_docs)} raw documents")

        # Monthly aggregation
        by_month = {}
        for name, obs in series.items():
            for o in obs:
                d = by_month.setdefault(o['ym'], {'ym': o['ym']})
                d[name] = o['value']

        if by_month:
            monthly_col.insert_many(list(by_month.values()))

        logger.info(f"Inserted {len(by_month)} monthly documents")

        return raw_col, monthly_col

    except Exception as e:
        logger.error(f"MongoDB load failed: {e}")
        sys.exit(1)

# Verifying document count

def verify(monthly_col):
    """Basic data integrity checks."""
    try:
        total = monthly_col.count_documents({})
        logger.info(f"Total monthly docs: {total}")

        for v in ('temperature', 'co2', 'methane', 'nitrous_oxide'):
            count = monthly_col.count_documents({v: {'$exists': True}})
            logger.info(f"{v}: {count} records present")

    except Exception as e:
        logger.error(f"Verification failed: {e}")

# Main Pipeline Execution for connecting to MongoDB and guidelines for API

try:
    logger.info("Starting data pipeline...")

    password = getpass("Enter MongoDB password: ")
    uri = f"mongodb+srv://clairemckbassett:{password}@hw10.cy0djtp.mongodb.net/?appName=HW10"
    client = MongoClient(uri)

    raw = fetch_all()
    co2_records = fetch_noaa_co2_monthly()
    series = build_series(raw, co2_records)

    CUTOFF = '2002-07'
    series = {
        name: [o for o in obs if o['ym'] >= CUTOFF]
        for name, obs in series.items()
    }

    raw_col, monthly_col = load_to_mongo(client, series)
    verify(monthly_col)

    logger.info("Pipeline completed successfully")

except Exception as e:
    logger.error(f"Fatal pipeline error: {e}")
    sys.exit(1)
```

    Enter MongoDB password: ··········


# Forecasting Model


```python
# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='forecasting.log'
)
logger = logging.getLogger(__name__)

try:
    logger.info("Pulling monthly data from MongoDB...")

    cursor = monthly_col.find(
        {
            'temperature':   {'$exists': True},
            'co2':           {'$exists': True},
            'methane':       {'$exists': True},
            'nitrous_oxide': {'$exists': True},
        },
        {'_id': 0, 'ym': 1, 'temperature': 1,
         'co2': 1, 'methane': 1, 'nitrous_oxide': 1},
    ).sort('ym', 1)

    df = pd.DataFrame(list(cursor)).reset_index(drop=True)

    if df.empty:
        raise ValueError("No data retrieved from MongoDB")

    logger.info(f"Pulled {len(df)} rows ({df['ym'].iloc[0]} -> {df['ym'].iloc[-1]})")

except Exception as e:
    logger.error(f"Failed to load modeling data: {e}")
    sys.exit(1)

# Applying differencing to track changes

try:
    logger.info("Applying month-over-month differencing...")

    for col in ['co2', 'methane', 'nitrous_oxide']:
        df[col] = df[col].diff()

    df = df.dropna().reset_index(drop=True)

    logger.info(f"After differencing: {len(df)} rows")

except Exception as e:
    logger.error(f"Error during differencing: {e}")
    sys.exit(1)

# Building lagged features

try:
    logger.info("Creating lagged features (1–12 months)...")

    GASES = {'co2': 'co2', 'ch4': 'methane', 'n2o': 'nitrous_oxide'}

    feat = pd.DataFrame({'ym': df['ym']})

    for short, col in GASES.items():
        for k in range(1, 13):
            feat[f'{short}_lag{k}'] = df[col].shift(k)

    # Target = next month's temperature
    feat['target'] = df['temperature'].shift(-1)

    feat = feat.dropna().reset_index(drop=True)

    logger.info(f"Model frame: {len(feat)} rows, {feat.shape[1] - 2} features")

except Exception as e:
    logger.error(f"Error building lag features: {e}")
    sys.exit(1)

# Implementing Train/Test Split

try:
    logger.info("Splitting data into train/test sets...")

    train = feat[feat['ym'] <= '2022-12']
    test  = feat[feat['ym'] >= '2023-01']

    if len(test) < 12:
        raise ValueError(f"Test set too small: {len(test)} rows")

    feature_cols = [c for c in feat.columns if c not in ('ym', 'target')]

    X_train, y_train = train[feature_cols].values, train['target'].values
    X_test,  y_test  = test[feature_cols].values,  test['target'].values

    logger.info(f"Train: {len(train)} rows | Test: {len(test)} rows")

except Exception as e:
    logger.error(f"Train/test split failed: {e}")
    sys.exit(1)

# Training Random Forest Model

try:
    logger.info("Training Random Forest model...")

    rf = RandomForestRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        random_state=0,
        n_jobs=-1
    ).fit(X_train, y_train)

    logger.info("Model training complete")

except Exception as e:
    logger.error(f"Model training failed: {e}")
    sys.exit(1)

# Evaluating Model
try:
    logger.info("Evaluating model on holdout set...")

    pred = rf.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, pred))
    mae  = mean_absolute_error(y_test, pred)
    r2   = r2_score(y_test, pred)

    logger.info(f"RMSE: {rmse:.3f}")
    logger.info(f"MAE : {mae:.3f}")
    logger.info(f"R2  : {r2:.3f}")

except Exception as e:
    logger.error(f"Evaluation failed: {e}")
    sys.exit(1)

# Permuation Importance

try:
    logger.info("Computing permutation importance...")

    perm = permutation_importance(
        rf, X_test, y_test,
        n_repeats=30,
        random_state=0,
        n_jobs=-1
    )

    imp = pd.DataFrame({
        'feature': feature_cols,
        'importance': perm.importances_mean,
        'std': perm.importances_std,
    })

    imp['gas'] = imp['feature'].str.split('_').str[0]

    per_gas = imp.groupby('gas')['importance'].sum().sort_values(ascending=False)

    logger.info("Per-gas importance computed")

    for gas, score in per_gas.items():
        logger.info(f"{gas}: {score:+.4f}")

except Exception as e:
    logger.error(f"Permutation importance failed: {e}")
    sys.exit(1)

# Outputting Predictions
try:
    logger.info("Building predictions dataframe...")

    results = pd.DataFrame({
        'ym_features': test['ym'].values,
        'actual': y_test,
        'predicted': pred,
        'error': y_test - pred,
    })

    logger.info("Preview of predictions:")
    logger.info("\n" + results.head(10).to_string(index=False))

except Exception as e:
    logger.error(f"Prediction output failed: {e}")
    sys.exit(1)

logger.info("Forecasting pipeline completed successfully")
```

# Visualization


```python
import matplotlib.pyplot as plt
import numpy as np
import logging
from matplotlib.patches import Patch

# Setting up logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

logger.info("Starting 3-panel figure generation...")

# Setting colors, labels, and text parameters
colors = {
    'ch4': '#1b9e77',   # teal
    'co2': '#d95f02',   # orange
    'n2o': '#7570b3'    # purple
}

gas_labels = {
    'ch4': 'Methane',
    'co2': 'Carbon Dioxide',
    'n2o': 'Nitrous Oxide'
}

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10
})

# Setting up figure
logger.info("Creating figure layout...")

fig = plt.figure(figsize=(18, 5))
gs = fig.add_gridspec(1, 3, wspace=0.45)

# Panel A: Gas Importance
try:
    logger.info("Building Panel A (gas importance)...")

    ax1 = fig.add_subplot(gs[0, 0])

    gases = per_gas.index.tolist()
    scores = per_gas.values
    bar_colors = [colors[g] for g in gases]

    bars = ax1.bar(
        [gas_labels[g] for g in gases],
        scores,
        color=bar_colors,
        edgecolor='black',
        lw=0.6
    )

    ax1.axhline(0, color='black', lw=0.6)
    ax1.set_title("A. Gas-level importance", pad=10)
    ax1.set_ylabel("Permutation importance")
    ax1.grid(axis='y', alpha=0.2)

    for bar, score in zip(bars, scores):
        y = bar.get_height()
        offset = 0.01 if score >= 0 else -0.03 # Added offset for text position
        ax1.text(
            bar.get_x() + bar.get_width()/2,
            y + offset,
            f"{score:+.2f}",
            ha='center',
            va='bottom',
            fontsize=9
        )

    logger.info("Panel A complete")

except Exception as e:
    logger.error(f"Panel A failed: {e}")
    raise


# Panel B: Lag Structure
try:
    logger.info("Building Panel B (lag structure)...")

    ax2 = fig.add_subplot(gs[0, 1])

    for gas in ['ch4', 'co2', 'n2o']:
        rows = imp[imp['gas'] == gas].copy()
        rows['lag'] = rows['feature'].str.extract(r'lag(\d+)').astype(int)
        rows = rows.sort_values('lag')

        ax2.plot(
            rows['lag'],
            rows['importance'],
            marker='o',
            lw=2,
            color=colors[gas],
            label=gas_labels[gas]
        )

    ax2.axhline(0, color='black', lw=0.5)
    ax2.set_title("B. Lag structure of importance", pad=10)
    ax2.set_xlabel("Lag (months)")
    ax2.grid(alpha=0.2)
    ax2.set_xticks(range(1, 13))

    logger.info("Panel B complete")

except Exception as e:
    logger.error(f"Panel B failed: {e}")
    raise


# Panel C: Top Lag Features
try:
    logger.info("Building Panel C (top lag features)...")

    ax3 = fig.add_subplot(gs[0, 2])

    top_lags = imp.sort_values('importance', ascending=False).head(10)
    top_lags_plot = top_lags.iloc[::-1]

    bar_colors_lag = [colors[g] for g in top_lags_plot['gas']]

    feature_labels = [
        f"{gas_labels[row['gas']]} L{row['feature'].split('lag')[-1]}"
        for _, row in top_lags_plot.iterrows()
    ]

    ax3.barh(
        feature_labels,
        top_lags_plot['importance'],
        color=bar_colors_lag,
        edgecolor='black',
        lw=0.6
    )

    ax3.set_title("C. Top lag features", pad=10)
    ax3.set_xlabel("Importance")
    ax3.grid(axis='x', alpha=0.2)
    ax3.axvline(0, color='black', lw=0.5)

    logger.info("Panel C complete")

except Exception as e:
    logger.error(f"Panel C failed: {e}")
    raise


# Final Output
try:
    logger.info("Finalizing figure...")

    fig.suptitle(
        "Permutation Importance Analysis of Greenhouse Gas Effects on Temperature Forecasting",
        fontsize=14,
        fontweight='bold',
        y=1.05
    )

    # Creating Global Legend
    legend_handles = [
        Patch(color=colors[g], label=gas_labels[g])
        for g in ['ch4', 'co2', 'n2o']
    ]

    fig.legend(
        handles=legend_handles,
        loc='lower center',
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, -0.05)
    )

    # Make room for bottom legend
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])

    # Save
    output_path = "figure_3panel.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Figure saved to {output_path}")

    # Showing Locally
    plt.show()

    logger.info("Figure displayed locally")

except Exception as e:
    logger.error(f"Final rendering failed: {e}")
    raise
```

    /tmp/ipykernel_14168/237879699.py:175: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
      plt.tight_layout(rect=[0, 0.08, 1, 0.95])



    
![png](pipeline_files/pipeline_8_1.png)
    


# Analysis Rationale

We chose to implement a Random Forest model for this analysis because it performs well in settings with many correlated features and nonlinear relationships, which is characteristic of time-lagged climate data. In our case, each greenhouse gas contributes 12 lagged features, creating a high-dimensional feature space where traditional linear models would require strong regularization and may still struggle to capture complex interactions. Random Forests, by contrast, naturally handle multicollinearity and can flexibly model nonlinear effects without extensive preprocessing.

Before modeling, we transformed the greenhouse gas variables (CO₂, CH₄, and N₂O) into month-over-month changes rather than using their raw levels. This decision was critical because these gases exhibit strong upward trends over time, and Random Forests are not designed to extrapolate beyond the range of the training data. By differencing the series, we ensured that the model learns from short-term fluctuations rather than long-term trends, keeping both training and test data within a comparable distribution. Temperature anomalies were left in their original form since they already fluctuate around a stable mean.

We also constructed lagged features for each gas, covering the previous 12 months, to capture delayed relationships between atmospheric changes and temperature response. This allows the model to learn not just whether a gas matters, but when it matters most. A time-based train/test split was used instead of random sampling to preserve temporal ordering and prevent data leakage, ensuring that the model is evaluated under realistic forecasting conditions.

For model interpretation, we used permutation importance rather than the built-in feature importance from the Random Forest. Permutation importance measures how much model performance degrades when a feature is randomly shuffled, making it less biased and more reflective of true predictive contribution. We then aggregated these importance scores across all 12 lags for each gas to produce a clear, comparable ranking of their overall influence. This approach provides both global insight into which gas is most predictive and more granular understanding of how far back in time each signal contributes to forecasting next-month temperature anomalies.

## Visualization Rationale
The visualization was carefully designed to communicate the structure and relative importance of greenhouse gas features in the temperature forecasting model. A multi-panel layout was chosen to separate distinct levels of analysis while still presenting a unified narrative, allowing the viewer to move from overall gas-level importance (Panel A), to temporal dynamics across lag structures (Panel B), and finally to the most influential individual lagged features (Panel C).Bar charts and line plots were selected because they provide intuitive and widely recognized ways to compare magnitude and trend, making it easier for viewers to quickly interpret differences in feature importance. The top-lag feature ranking in Panel C was intentionally limited to the most influential 10 features to avoid visual clutter while still capturing the most meaningful drivers of the model. Color was consistently used across all panels to distinguish between methane, carbon dioxide, and nitrous oxide, ensuring that patterns can be tracked across different views of the data. A single consolidated legend was placed along the bottom of the figure to reduce redundancy and maintain a cleaner visual structure, improving readability and emphasizing cross-panel consistency.
