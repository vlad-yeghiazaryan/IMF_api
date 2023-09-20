## IMF API

A simple python implementation of the IMF api that allows one to request data from a variety of datasets.

### **Usage:**
```python
from IMF_api import IMF_API
IFS = IMF_API(database='IFS')
IFS.get_series(indicators=['EREER_IX'], countries=['United Kingdom'], 
                  startYear=2000, endYear=2020, frequency='Q')
```

### **Example:**
```python
import pandas as pd
import matplotlib.pyplot as plt
from IMF_api import IMF_API
```


```python
IFS_api = IMF_API('IFS')
countries = ['Russian Federation', 'United Kingdom', 'Canada']
```

```python
for country in countries:
    print(IFS_api.get_country_code(country))
```
    RU
    GB
    CA


```python
FSI_api = IMF_API('FSI')
search = 'capital risk Domes'
FSI_api.indicator_search(search)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>@value</th>
      <th>#text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>FS_ODX_CET1_FSCET_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>FS_ODX_ARW_FSCET_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>FS_ODX_ARW_FSKRC_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>FS_ODX_ARW_FSKRTC_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>FS_ODX_CT1_FSKRTC_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>FS_ODX_CRT_FSKRC_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>FSNSNO_FSSNO_XDC</td>
      <td>Monetary and Financial Accounts, Financial Sou...</td>
    </tr>
  </tbody>
</table>
</div>


```python
results = FSI_api.search_data_availability(search, countries, 2000, 2020, 'Q')
results
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>FS_ODX_ARW_FSKRTC_XDC</th>
      <th>FS_ODX_CT1_FSKRTC_XDC</th>
      <th>FS_ODX_CRT_FSKRC_XDC</th>
      <th>FS_ODX_ARW_FSKRC_XDC</th>
      <th>FSNSNO_FSSNO_XDC</th>
      <th>FS_ODX_ARW_FSCET_XDC</th>
      <th>FS_ODX_CET1_FSCET_XDC</th>
    </tr>
    <tr>
      <th>country</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>CA</th>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>GB</th>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>2005-2020</td>
      <td>2014-2020</td>
      <td>2014-2020</td>
    </tr>
    <tr>
      <th>RU</th>
      <td>2008-2020</td>
      <td>2008-2020</td>
      <td>2008-2020</td>
      <td>2008-2020</td>
      <td>2008-2020</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>

```python
IFS_api = IMF_API('IFS')
search = 'exchange real effective'
IFS_api.indicator_search(search)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>@value</th>
      <th>#text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>EREER_IX</td>
      <td>Exchange Rates, Real Effective Exchange Rate b...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>EREER_PC_CP_A_PT</td>
      <td>Exchange Rates, Real Effective Exchange Rate b...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>EREER_ULC_IX</td>
      <td>Exchange Rates, Real Effective Exchange Rate b...</td>
    </tr>
  </tbody>
</table>
</div>


```python
results = IFS_api.search_data_availability(search, countries, 2000, 2020, 'Q')
results
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>EREER_IX</th>
      <th>EREER_ULC_IX</th>
      <th>EREER_PC_CP_A_PT</th>
    </tr>
    <tr>
      <th>country</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>CA</th>
      <td>2000-2020</td>
      <td>2000-2020</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>GB</th>
      <td>2000-2020</td>
      <td>2000-2020</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>RU</th>
      <td>2000-2020</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>


```python
indicators_FSI = ['FSKRC_PT', 'FSKRTC_PT']
indicators_IFS = ['EREER_IX']
```

```python
for indicator in indicators_FSI:
    print(FSI_api.get_indicator_name(indicator))

for indicator in indicators_IFS:
    print(IFS_api.get_indicator_name(indicator))
```

    Financial, Financial Soundness Indicators, Core Set, Deposit Takers, Capital Adequacy, Regulatory Capital to Risk-Weighted Assets, Percent
    Financial, Financial Soundness Indicators, Core Set, Deposit Takers, Capital Adequacy, Regulatory Tier 1 Capital to Risk-Weighted Assets, Percent
    Exchange Rates, Real Effective Exchange Rate based on Consumer Price Index, Index

```python
uk_FSKRC_PT = FSI_api.get_series(indicator='FSKRC_PT', country='United Kingdom', startYear=2010, endYear=2020, frequency='Q').reset_index(level=1).iloc[:,1]
uk_FSKRC_PT.plot()
plt.title(uk_FSKRC_PT.name)
plt.show()
```

![png](Assets/output_9_0.png)
  

```python
IFS_api = IMF_API('IFS')
FSI_api = IMF_API('FSI')

data_IFS = IFS_api.get_series(indicators_IFS, countries, 2010, 2020, 'Q')
data_FSI = FSI_api.get_series(indicators_FSI, countries, 2010, 2020, 'Q')
dataset = pd.merge(data_FSI, data_IFS, how='outer', on=['date', "country"]).sort_index()
```

```python
dataset.head()
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th>Financial, Financial Soundness Indicators, Core Set, Deposit Takers, Capital Adequacy, Regulatory Tier 1 Capital to Risk-Weighted Assets, Percent</th>
      <th>Financial, Financial Soundness Indicators, Core Set, Deposit Takers, Capital Adequacy, Regulatory Capital to Risk-Weighted Assets, Percent</th>
      <th>Exchange Rates, Real Effective Exchange Rate based on Consumer Price Index, Index</th>
    </tr>
    <tr>
      <th>date</th>
      <th>country</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="3" valign="top">2010-01-01</th>
      <th>CA</th>
      <td>12.414406</td>
      <td>14.816699</td>
      <td>98.770285</td>
    </tr>
    <tr>
      <th>GB</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>99.079550</td>
    </tr>
    <tr>
      <th>RU</th>
      <td>14.606693</td>
      <td>20.483179</td>
      <td>98.392140</td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">2010-04-01</th>
      <th>CA</th>
      <td>12.889560</td>
      <td>15.429925</td>
      <td>100.948096</td>
    </tr>
    <tr>
      <th>GB</th>
      <td>12.351023</td>
      <td>15.027093</td>
      <td>98.877582</td>
    </tr>
  </tbody>
</table>
</div>


```python
dataset.to_csv('./data/imf_dataset.csv')
```