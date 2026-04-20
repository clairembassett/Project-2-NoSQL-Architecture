import requests
from getpass import getpass
from datetime import datetime, timezone
from pymongo import MongoClient

# Retrieves monthly Carbon Dioxide, Methane, Nitrous Oxide, and Temperature Anomalies from the Global Warming API, puts it in to Mongo, and creates two collections to seperate raw and processed data

# API Endpoints
ENDPOINTS = {
    'temperature':   'https://global-warming.org/api/temperature-api',
    'co2':           'https://global-warming.org/api/co2-api',
    'methane':       'https://global-warming.org/api/methane-api',
    'nitrous_oxide': 'https://global-warming.org/api/nitrous-oxide-api',
}

# Ensuring that the retrieved data has correct units
UNITS = {
    'temperature':   'degC_anomaly',
    'co2':           'ppm',
    'methane':       'ppb',
    'nitrous_oxide': 'ppb',
}


# Standardizing dates to only contain year and month
def decimal_year_to_ym(dy):
    dy = float(dy)
    y = int(dy)
    frac = dy - y
    m = int(round(frac * 12)) + 1
    if m == 13:
        m, y = 1, y + 1
    return f'{y:04d}-{m:02d}'

# Replacing -999(the API's value for missing) as None instead of a real value
def safe_float(x):
    try:
        v = float(x)
        return v if v > -999 else None
    except (TypeError, ValueError):
        return None

# Enables each endpoint to have records in a different key
def _first_list(payload, preferred_keys=()):
    for k in preferred_keys:
        if k in payload and isinstance(payload[k], list):
            return payload[k]
    for v in payload.values():
        if isinstance(v, list):
            return v
    return []


# Fetches data from all four endpoints and prints the shape of each for debugging
def fetch_all():
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

# Normalizing Temperature so the time and station is standardized
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

# Normalizing Carbon Dioxide to accept the year format and defining cycle as the main value
def normalize_co2(payload):
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

# Normalizing the decimal year between Methan and Nitrous Oxide, setting average as monthly mean
def normalize_decimal_year(payload, keys):
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

# Preparing pipeline to handle possible different variants that may be passed by the input
def build_series(raw):
    series = {
        'temperature':   normalize_temperature(raw['temperature']),
        'co2':           normalize_co2(raw['co2']),
        'methane':       normalize_decimal_year(raw['methane'], ('methane',)),
        'nitrous_oxide': normalize_decimal_year(
            raw['nitrous_oxide'],
            ('nitrous oxide', 'nitrousoxide', 'nitrous_oxide'),
        ),
    }

# Printing the date range for debugging
    for name, s in series.items():
        if s:
            print(f'{name:15s}  {len(s):5d} records   {s[0]["ym"]} -> {s[-1]["ym"]}')
        else:
            print(f'{name:15s}  0 records  (inspect the sample record above and adjust the normalizer)')
    return series


# Loading data to MongoDB
def load_to_mongo(client, series):
    # using a separate db so I don't step on sample_mflix
    proj        = client['ds4320_project']
    raw_col     = proj['raw_measurements']
    monthly_col = proj['monthly']

    fetched_at = datetime.now(timezone.utc)

# Wiping MongoDB to remove duplicates, and track of the number of raw document, and appending data to the raw docs
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

    # Creating a document for each month with all the four variables included
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

# Checking the monthly documents to ensure accuracy
def verify(monthly_col):

    total    = monthly_col.count_documents({})
    all_four = monthly_col.count_documents({
        'temperature':   {'$exists': True},
        'co2':           {'$exists': True},
        'methane':       {'$exists': True},
        'nitrous_oxide': {'$exists': True},
    })
    print(f'Total monthly docs          : {total}')
    print(f'Months with ALL four present: {all_four}  ({round(all_four/total*100,1)}%)')

    for v in ('temperature', 'co2', 'methane', 'nitrous_oxide'):
        first = monthly_col.find_one({v: {'$exists': True}}, sort=[('ym', 1)])
        last  = monthly_col.find_one({v: {'$exists': True}}, sort=[('ym', -1)])
        print(f'  {v:15s}  {first["ym"]} -> {last["ym"]}')

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

# Running the connection to MongoDB and keeping the password private
password = getpass("Enter your MongoDB password: ")
uri = f"mongodb+srv://clairemckbassett:{password}@hw10.cy0djtp.mongodb.net/?appName=HW10"
client = MongoClient(uri)

raw = fetch_all()
series = build_series(raw)
CUTOFF = '2001-01'
series = {name: [o for o in obs if o['ym'] >= CUTOFF] for name, obs in series.items()}
raw_col, monthly_col = load_to_mongo(client, series)
verify(monthly_col)y
