# DS 4320 Project 2 - TITLE HERE
### Executive Summary
EXECUTIVE SUMMARY HERE

<br>

<br>

---

### Name - Claire Bassett
### NetID - qxm6fm
### DOI - 
### Press Release
[**HERE**](PressRelease.MD)
### Data - [link to data](HERE)
### Pipeline - [Pipeline Code](Pipeline/pipeline.ipynb) EDIT
### License - [MIT](LICENSE.md) FINISHED
---
| Spec | Value |
|---|---|
| Name | Claire Bassett |
| NetID | qxm6fm |
| DOI | [HEREE) |
| Press Release | [**HERE**](PressRelease.MD) |
| Data | [link to data](HERE) |
| Pipeline |  [Pipeline Code](Pipeline/pipeline.ipynb)
| License | [MIT](LICENSE.md) |

---
<br>

<br>

## Problem Definition
### General and Specific Problem

* **General Problem:** Forecasting global climate change
* **Specific Problem:** Do CO2, Methane, or Nitrous Oxide better predict global temperature anomalies?

  
### Rationale

This refinement narrows its scope to the relationship between atmospheric greenhouse gas concentrations (CO2, methane, and nitrous oxide) and global temperature anomalies, the most well-established and measurable driver of warming. This keeps the model clean and interpretable while aligning with the available data from the Global Warming API, which provides continuous measurements of each gas alongside temperature records.


### Motivation

Global warming poses an existential threat to ecosystems, economies, and human health worldwide, yet public understanding of the specific mechanisms driving temperature increases remains limited. While scientists have established that greenhouse gas emissions are the primary cause, the precise relationship between rising CO2, methane, and nitrous oxide levels and observed temperature changes is not always clearly communicated to policymakers and the public. This research is essential for setting informed emission reduction goals, allocating resources for climate adaption,and slowing the pace of global warming.


### Press Release
[**HERE**](PressRelease.MD)

## Domain Exposition
### Terminology
| Term | Definition |
|------|-----------|
| **Carbon Dioxide** | A greenhouse gas measured in parts per million (ppm) that traps heat in the atmosphere.|
| **Methane** | A greenhouse gas measured in parts per billion (ppb, sources include livestock, landfills, and natural gas systems. |
| **Nitrous Oxide** | A greenhouse gas measured in parts per billion (ppb), produced by fertilizers, sewage, and fossil fuel combustion. |
| **Temperature Anomaly** | The difference in °C between observed temperature and a long-term baseline average. Positive values indicate warming above the historical norm. |
| **PPM (Parts Per Million)** | Unit of concentration used for CO2.|
| **PPB (Parts Per Billion)** | Unit of concentration used for methane and nitrous oxide. 1 ppm = 1,000 ppb. |
| **Arctic Sea Ice Extent** | Total area in millions of square kilometers where sea ice concentration is at least 15%. Used as a key indicator of polar warming. |
| **Seasonal Cycle** | The natural annual fluctuation in gas concentration caused by seasonal biological activity such as plant growth absorbing CO2 in summer. |
| **Greenhouse Gas** | Any gas that absorbs and re-emits infrared radiation, trapping heat in the atmosphere.|
| **Baseline Period** | The reference time range against which anomalies are calculated.|

### Domain
This project lives in the domain of environmental science. Understanding the relationship between these emissions and observed temperature changes is critical for informing policy decisions, guiding mitigation strategies, and preparing communities for future environmental impacts. This project seeks to quantify how greenhouse gas concentrations correlate with global temperature anomalies and to forecast future warming trends.

### Background Reading
[Readings Linked Here](Readings)
### Summary of Readings

| Title | Summary | Link |
|-------|---------|------|
| Climate Change and the Impact of Greenhouse Gasses: CO2 and NO, Friends and Foes of Plant Oxidative Stress | This review examines how rising greenhouse gas concentrations cause oxidative stress in plants through increased reactive oxygen species (ROS), and how plants use antioxidant defense systems to cope. The authors highlight nitric oxide (NO) as a central molecule that helps plants tolerate climate change. | [Link Here](https://myuva-my.sharepoint.com/:b:/g/personal/qxm6fm_virginia_edu/IQDyL9WVGciiTYppYyMRTuf9AXRo072dAat92eiEFXZWBuI?e=lfH7nh) |
| Climate change: the greenhouse gases causing global warming | This European Parliament article explains the seven types of greenhouse gases covered by the Kyoto Protocol and Paris Agreement (including CO2, methane, nitrous oxide, and fluorinated gases), and how they differ in warming potential. It also outlines the EU's legally binding targets to cut emissions 55% by 2030 and reach net zero by 2050. | [Link Here](https://myuva-my.sharepoint.com/:b:/g/personal/qxm6fm_virginia_edu/IQASl3eH_0G3QoE9ra44H_Q6AZuTpPuowavslbkcrINj0_Q?e=1zVgUq) |
| Estimated human-induced warming from a linear temperature and atmospheric CO2 relationship | This study proposes a simple method for estimating human-induced warming by using the linear relationship between atmospheric CO2 concentrations and global temperature, producing estimates that are 30% more certain than existing climate model-based approaches. The authors estimate that humans caused 1.49 ± 0.11°C of warming by 2023 relative to a pre-1700 baseline. | [Link Here](https://myuva-my.sharepoint.com/:b:/g/personal/qxm6fm_virginia_edu/IQD5Pws5lZYTR5M2mKpcqWAgAfY33KV7CQO2ye65bqkKo7A?e=yu9fJk) |
| The Relation Between the CO2 Concentration Levels and the Temperature | This study compares four forecasting models to predict future CO2 concentrations, finding that ARIMA(2,1,1) was the most accurate with an R² of 0.9994. The authors confirmed a strong correlation between CO2 concentrations and land-ocean temperature since 1959, supporting its use in forecasting temperature changes. | [Link Here](https://myuva-my.sharepoint.com/:b:/g/personal/qxm6fm_virginia_edu/IQCgKpDrSl4AR5PdNCJasEolAX3_uK33_zbt5URGFolnwAg?e=mc1Z18) |
| The world is likely to exceed a key global warming target soon. Now what? | UNEP's 2025 Emissions Gap Report finds that global temperatures will likely exceed the Paris Agreement's 1.5°C target within the next decade, as greenhouse gas emissions continue to rise. Even if all countries fulfill their current climate pledges, the world is still projected to warm by 2.3–2.5°C by century's end. | [Link Here](https://myuva-my.sharepoint.com/:b:/g/personal/qxm6fm_virginia_edu/IQB7IA_Dag_-R4WQX_KPbeDbAbqopiVv4il0ITASqXLz0KE?e=ZoztSG) |

## Data Creation 

### Provenance
The data was retrieved using the Global Warming API from NOAA. The API has endpoints for each requested field including Temperature Anomalies, Nitrous Oxide, Carbon Dioxide, and Methane. The API was contacted through a python script connecting to MongoDB(see pipeline/pipeline.py). The API pulls from two sources the NOAA Global Monitoring Laboratory for the three gases and NASA GISTEMP for the temperature anomaly.

### Code FIXXXXX

| File | Description | Repo link |
|------|-------------|-----------|
| `pipeline.py` | This file retrieves the data, normalizes it, and loads it into MongoDB | [Link Here]('https://github.com/clairembassett/Project-2-NoSQL-Architecture/blob/main/pipeline.py') |

### Bias Identification
Bias from the data could occur due to an unequal record length across gases. Carbon Dioxide monitoring starts in 1958, Methane in 1983, and Nitrous Oxide in 2001. Additonally, all four variables come from the same API, which means that any systematic error or calibration issue would be shared across the data. The missing value is encoded as -999 for missing observations, this value could bias and skew results if included.

### Bias Mitigation
Bias must be mitigated to ensure accurate results, to standardize the unequal record length we will start our analysis in 2001, ensuring equal lengths across records. To mitigate the issue of potentially biased sources we will spot-check against the upstream sources to confirm the API is not introducing its own transformation. The missing value will be encoded as None rather then -999, thus removing bias from the results.

### Rationale
We chose to keep two collections: raw_measurements and monthly. This ensured we protected the original provenance of the data, making it more readable down the pipeline. We also chose to view the data at a monthly label to condense the data, this aligns each of the data sources making it easier to align and work with the data. We chose to keep `cycle` as the primary CO₂ value and store `trend` alongside it because `cycle` is the raw monthly reading while `trend` is already smoothed upstream. Storing both lets us use the raw values when we want the real month-to-month signal and the smoothed ones when we're looking at long-term patterns.

## Metadata
### Implicit Schema 
We set a few ground rules for how documents are structured so both collections stay consistent and easy to work with down the pipeline. All field names use the same formatting (`nitrous_oxide`, `value_trend`, `fetched_at`, etc.) to keep everything uniform. Dates are stored as `YYYY-MM` strings in a `ym` field, which is the finest grain all four sources share and sorts correctly as a string without needing a real date type. We also decided to store units explicitly on each raw document (`ppm`, `ppb`, `degC_anomaly`) instead of leaving readers to infer them from the variable name. Every raw document carries a `source_url` and `fetched_at` so any observation can be traced back to the exact pull it came from. Missing values are represented as absent fields rather than `null` or `-999`, which keeps aggregations clean since they automatically skip months where a variable wasn't measured. Finally, the `monthly` collection is set up so that each month can only appear once. This is done by putting a unique index on the `ym` field, which tells MongoDB to reject any insert that would create a duplicate month.

### Tables 
| Table | Description | Link |
|-------|-------------|------|
| Text | A table containing 134,198 tweet records from the TruthSeeker dataset, describing the text features of tweets including information on word make-up and the percentage of tags in the text. | [text.parquet](https://myuva-my.sharepoint.com/:u:/g/personal/qxm6fm_virginia_edu/IQC4h9mPQ0XPQLXMnoB4yJBgAZQjTFWv8w55AuXFZ4ZpXf4?e=cZqAc6) |
| Lexical | A table containing 134,198 tweet records from the TruthSeeker dataset, including the linguistic characteristics of each tweet such as punctuation and word classification.  | [lexical.parquet](https://myuva-my.sharepoint.com/:u:/g/personal/qxm6fm_virginia_edu/IQD-UPFOSB5OTaKMdoFk-BqCAQVtBeNMIQkpup2Z8Ty4UHM?e=mr8h1Q) |
| Meta-data | A table containing 134,198 tweet records made from the TruthSeeker dataset, including information on the user who posted the tweet, including the size of following and interaction totals on posts. | [metadata.parquet](https://myuva-my.sharepoint.com/:u:/g/personal/qxm6fm_virginia_edu/IQBvurMzcYT6Qa8fpABqehkxASOv1qsr1GLJADMs3oPsg_U?e=J2r12y) |
| Scores |A table containing 134,198 tweet records derived from the TruthSeeker dataset, capturing credibility, influence, and bot activity scores alongside fake news labels. | [scores.parquet](https://myuva-my.sharepoint.com/:u:/g/personal/qxm6fm_virginia_edu/IQDatITsN_HlQ5DUvow7xuI0AS76HvPFEMi-wZ_fZ30KiL4?e=mGfknG) |

### Data Dictionary 
| Field | Type | Description | Example |
|---|---|---|---|
| `_id` | ObjectId | MongoDB document identifier, auto-generated on insert | `ObjectId("65a3f...")` |
| `ym` | string | Year-month key in `YYYY-MM` format, the shared time grain across all variables | `"2020-01"` |
| `variable` | string | Which measurement the document represents — only present in `raw_measurements` | `"co2"` |
| `value` | float | Primary measurement for the month, in the variable's native unit | `413.4` |
| `value_trend` | float | Deseasonalized/smoothed version of `value` as published by the upstream source. Absent if the source does not provide one. | `413.2` |
| `unit` | string | Unit of measurement, stored explicitly so readers never have to guess | `"ppm"` |
| `source_url` | string | API endpoint the observation was pulled from, for provenance | `"https://global-warming.org/api/co2-api"` |
| `fetched_at` | datetime (UTC) | Timestamp of when the observation was retrieved from the API | `2026-04-20T14:32:11Z` |
| `temperature` | float | Global mean surface temperature anomaly — only in `monthly` docs | `1.12` |
| `co2` | float | Atmospheric CO₂ concentration — only in `monthly` docs | `413.4` |
| `methane` | float | Atmospheric methane concentration — only in `monthly` docs | `1877.1` |
| `nitrous_oxide` | float | Atmospheric N₂O concentration — only in `monthly` docs | `333.5` |



### Data Dictionary - Quantification of Uncertainty
| Feature | Unit | Source precision | Estimated uncertainty (±) | Notes |
|---|---|---|---|---|
| `temperature` | °C anomaly | 2 decimal places | ± 0.05 °C (recent) | GISTEMP reports formal uncertainty of roughly ±0.05 °C for recent decades. Uncertainty grows to ±0.1 °C or more for early-20th-century values, where station coverage was sparse. |
| `co2` | ppm | 2 decimal places | ± 0.1 ppm | NOAA GML reports Mauna Loa monthly means to within 0.1 ppm. Global averaging adds a small additional uncertainty from station-to-station variation. |
| `methane` | ppb | 2 decimal places | ± 2 ppb | WMO reports global mean methane to within roughly ±2 ppb. Methane varies more across stations than CO₂, so the global average has slightly looser precision. |
| `nitrous_oxide` | ppb | 2 decimal places | ± 0.1 ppb | N₂O is well-mixed in the atmosphere, so station-to-station variation is small. NOAA reports global mean N₂O to within 0.1 ppb. |
| `value_trend` (all gases) | same as `value` | 2 decimal places | `value` uncertainty + smoother uncertainty | The trend series carries extra uncertainty from the upstream smoothing algorithm. This uncertainty is largest at the edges of the time series (most recent months), where the smoother has less future data to work with. |
