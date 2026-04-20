import requests
from getpass import getpass
from datetime import datetime, timezone
from pymongo import MongoClient

# Pulls monthly CO2, methane, N2O, and temp anomaly from the Global Warming API
# and dumps it into Mongo. Two collections so I can keep the raw pull separate
# from the reshaped version I'll actually run regressions on.

ENDPOINTS = {
    'temperature':   'https://global-warming.org/api/temperature-api',
    'co2':           'https://global-warming.org/api/co2-api',
    'methane':       'https://global-warming.org/api/methane-api',
    'nitrous_oxide': 'https://global-warming.org/api/nitrous-oxide-api',
}

UNITS = {
    'temperature':   'degC_anomaly',
    'co2':           'ppm',
    'methane':       'ppb',
    'nitrous_oxide': 'ppb',
}


# ---- helpers ----

def decimal_year_to_ym(dy):
    # temp/methane/N2O come back as decimal years like "1983.75"
    # pulling out year + month so everything keys off YYYY-MM
    dy = float(dy)
    y = int(dy)
    frac = dy - y
    m = int(round(frac * 12)) + 1
    if m == 13:
        m, y = 1, y + 1
    return f'{y:04d}-{m:02d}'


def safe_float(x):
    # API uses -999 for missing, so treat that as None instead of a real value
    try:
        v = float(x)
        return v if v > -999 else None
    except (TypeError, ValueError):
        return None


def _first_list(payload, preferred_keys=()):
    # each endpoint wraps its records under a different key
    # check the obvious ones first, then fall back to whatever list shows up
    for k in preferred_keys:
        if k in payload and isinstance(payload[k], list):
            return payload[k]
    for v in payload.values():
        if isinstance(v, list):
            return v
    return []


# ---- fetch ----

def fetch_all():
    # hit all four endpoints, print shape of each one so I can spot it
    # if the API changes field names on me later
    raw = {}
    for name, url in ENDPOINTS.items():
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        raw[name] = r.json()
        print(f'--- {name} ---')
        print('  top-level keys:', list(raw[name].keys()))
        for k, v in raw[name].items():
            if isinstance(v, list) and v:
                print(f"  list key '{k}' — {len(v)} records")
                print(f'  sample record : {v[0]}')
                break
        print()
    return raw


# ---- normalize ----
# each series has its own shape, so one function per endpoint.
# all of them spit out {ym, value, value_trend} so the loader doesn't care

def normalize_temperature(payload):
    # temperature records have 'time' (decimal year) and 'station' (land-ocean anomaly)
    out = []
    for r in _first_list(payload, ('result',)):
        t = r.get('time') or r.get('date')
        if t is None:
            continue
        v = safe_float(r.get('station') or r.get('land'))
        if v is not None:
            out.append({'ym': decimal_year_to_ym(t), 'value': v})
    return out


def normalize_co2(payload):
    # co2 is the odd one out - separate year/month/day fields instead of decimal year
    # 'cycle' = seasonal, 'trend' = deseasonalized. grab both, use cycle as the main value
    out = []
    for r in _first_list(payload, ('co2',)):
        try:
            ym = f"{int(r['year']):04d}-{int(r['month']):02d}"
        except (KeyError, ValueError, TypeError):
            continue
        val = safe_float(r.get('cycle') or r.get('trend'))
        trend = safe_float(r.get('trend'))
        if val is not None:
            out.append({'ym': ym, 'value': val, 'value_trend': trend})
    return out


def normalize_decimal_year(payload, keys):
    # methane and N2O are the same shape so they share a normalizer
    # 'average' is the monthly mean, 'trend' is smoothed
    out = []
    for r in _first_list(payload, keys):
        t = r.get('date') or r.get('time')
        if t is None:
            continue
        avg = safe_float(r.get('average'))
        trend = safe_float(r.get('trend'))
        val = avg if avg is not None else trend
        if val is not None:
            out.append({'ym': decimal_year_to_ym(t), 'value': val, 'value_trend': trend})
    return out


def build_series(raw):
    # N2O endpoint has a space in its key ('nitrous oxide') so passing a few
    # variants in case they clean it up later
    series = {
        'temperature':   normalize_temperature(raw['temperature']),
        'co2':           normalize_co2(raw['co2']),
        'methane':       normalize_decimal_year(raw['methane'], ('methane',)),
        'nitrous_oxide': normalize_decimal_year(
            raw['nitrous_oxide'],
            ('nitrous oxide', 'nitrousoxide', 'nitrous_oxide'),
        ),
    }
    # print the date range per series - good sanity check, and also shows
    # the coverage gap (CO2 goes way further back than N2O) that I need for 10.7
    for name, s in series.items():
        if s:
            print(f'{name:15s}  {len(s):5d} records   {s[0]["ym"]} -> {s[-1]["ym"]}')
        else:
            print(f'{name:15s}  0 records  (inspect the sample record above and adjust the normalizer)')
    return series


# ---- load ----

def load_to_mongo(client, series):
    # using a separate db so I don't step on sample_mflix
    proj        = client['ds4320_project']
    raw_col     = proj['raw_measurements']
    monthly_col = proj['monthly']

    fetched_at = datetime.now(timezone.utc)

    # wipe first so re-running doesn't pile up duplicates
    # raw_measurements = one doc per observation. keeps source_url on every
    # doc so I can trace any number back to where it came from (provenance)
    raw_col.delete_many({})
    raw_docs = []
    for name, obs in series.items():
        for o in obs:
            raw_docs.append({
                'variable':    name,
                'ym':          o['ym'],
                'value':       o['value'],
                'value_trend': o.get('value_trend'),
                'unit':        UNITS[name],
                'source_url':  ENDPOINTS[name],
                'fetched_at':  fetched_at,
            })
    if raw_docs:
        raw_col.insert_many(raw_docs)
    print(f'raw_measurements : {raw_col.count_documents({})} docs')

    # monthly = one doc per month with all four variables embedded.
    # this is the shape I actually want for the regression - one row = one observation
    # older months will be missing methane/N2O, which is fine (and expected)
    monthly_col.delete_many({})
    by_month = {}
    for name, obs in series.items():
        for o in obs:
            d = by_month.setdefault(o['ym'], {'ym': o['ym']})
            d[name] = o['value']
            if o.get('value_trend') is not None:
                d[f'{name}_trend'] = o['value_trend']
    if by_month:
        monthly_col.insert_many(list(by_month.values()))
    print(f'monthly          : {monthly_col.count_documents({})} docs')

    # indexes - ym lookups are what I'll do most. unique on monthly since
    # there should only ever be one doc per month
    raw_col.create_index([('variable', 1), ('ym', 1)])
    monthly_col.create_index('ym', unique=True)

    return raw_col, monthly_col


# ---- verify ----

def verify(monthly_col):
    # sanity check before I trust it
    total    = monthly_col.count_documents({})
    all_four = monthly_col.count_documents({
        'temperature':   {'$exists': True},
        'co2':           {'$exists': True},
        'methane':       {'$exists': True},
        'nitrous_oxide': {'$exists': True},
    })
    print(f'Total monthly docs          : {total}')
    print(f'Months with ALL four present: {all_four}  ({round(all_four/total*100,1)}%)')

    # per-variable date range - this is the evidence that the series don't
    # all start at the same time (needed for the bias section of 10.7)
    for v in ('temperature', 'co2', 'methane', 'nitrous_oxide'):
        first = monthly_col.find_one({v: {'$exists': True}}, sort=[('ym', 1)])
        last  = monthly_col.find_one({v: {'$exists': True}}, sort=[('ym', -1)])
        print(f'  {v:15s}  {first["ym"]} -> {last["ym"]}')

    # eyeball the most recent fully populated month to confirm the embedding worked
    sample = monthly_col.find_one(
        {'temperature':   {'$exists': True},
         'co2':           {'$exists': True},
         'methane':       {'$exists': True},
         'nitrous_oxide': {'$exists': True}},
        {'_id': 0},
        sort=[('ym', -1)],
    )
    print('\nMost recent fully-populated month:')
    print(sample)


# ---- run ----

# prompting for the password instead of hardcoding so I don't accidentally
# commit it to the repo
password = getpass("Enter your MongoDB password: ")
uri = f"mongodb+srv://clairemckbassett:{password}@hw10.cy0djtp.mongodb.net/?appName=HW10"
client = MongoClient(uri)

raw = fetch_all()
series = build_series(raw)
raw_col, monthly_col = load_to_mongo(client, series)
verify(monthly_col)y
