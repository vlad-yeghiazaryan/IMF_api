import pandas as pd
import numpy as np
import requests
import time
import warnings

class IMF_API():
    url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc'
    query_method = 'CompactData'
    collection = 'Dataflow'
    databaseInfo = 'DataStructure'

    def __init__(self, database):
        self.database = database
        self.code_list = self.get_code_list()
    
    def database_search(self, query):
        dataflow = pd.DataFrame(requests.get(f'{IMF_API.url}/{IMF_API.collection}').json()['Structure']['Dataflows']['Dataflow'])
        dataflow = pd.concat([dataflow.drop(['Name', 'KeyFamilyRef'], axis=1), pd.json_normalize(dataflow.Name), 
                              pd.json_normalize(dataflow.KeyFamilyRef)], axis=1)
        results = dataflow['#text'][dataflow['#text'].str.lower().str.contains(query.lower())].reset_index()['#text']
        return results
    
    def indicator_search(self, query):
        base = r'^{}'
        expr = '(?=.*{})'
        words = query.lower().split(' ')
        regex_search = base.format(''.join(expr.format(w) for w in words))
        matches = self.code_list['INDICATOR'][['@value','#text']][self.code_list['INDICATOR']['#text'].str.lower().str.contains(regex_search)]
        return matches.reset_index()[['@value','#text']]

    def get_code_list(self):
        query = f'{IMF_API.url}/{IMF_API.databaseInfo}/{self.database}'
        res = requests.get(query)
        res.raise_for_status()
        dataStructure = pd.DataFrame(res.json()['Structure']['KeyFamilies']['KeyFamily']['Components']['Dimension'])
        time.sleep(5) # 2 seconds is enough
        dimensions = list(dataStructure['@codelist'])
        
        # extracting code data
        code_urls = [f'{IMF_API.url}/CodeList/{dimension}' for dimension in dimensions]
        code_urls = dict(zip(dataStructure['@conceptRef'], code_urls))
        codes = {name: r.json()['Structure']['CodeLists']['CodeList']['Code'] for name, url in code_urls.items() if (r := requests.get(url)).ok}

        code_list = {}
        for name, code in codes.items():
            codes_table = pd.concat([pd.DataFrame(code).drop('Description', axis=1), pd.json_normalize(pd.DataFrame(code).Description)], axis=1)
            code_list.update({name:codes_table})
        return code_list

    def get_country_code(self, country_name):
        matches = list(self.code_list['REF_AREA'][self.code_list['REF_AREA']['#text'].str.lower().str.strip() == country_name.lower().strip()]['@value'])
        if len(matches) == 0:
            return None
        else:
            return matches[0]

    def get_country_name(self, country_code):
        matches = list(self.code_list['REF_AREA'][self.code_list['REF_AREA']['@value'] == country_code]['#text'])
        if len(matches) == 0:
            return None
        else:
            return matches[0]

    def get_indicator_name(self, indicator_code):
        matches = list(self.code_list['INDICATOR'][self.code_list['INDICATOR']['@value'] == indicator_code]['#text'])
        if len(matches) == 0:
            return None
        else:
            return matches[0]

    @staticmethod
    def _handle_date_format(dates, freq):
        if freq=='A':
            dates = pd.to_datetime(dates)
        elif freq=='M':
            dates = pd.to_datetime(dates)
        elif freq=='Q':
            dates = pd.PeriodIndex(dates, freq='Q').to_timestamp()
        else:
            warnings.warn(f'Unknown frequency {freq}', UserWarning)
        return dates

    def format_series(self, series):
        column_names = {'@TIME_PERIOD':'date', '@OBS_VALUE':series['@INDICATOR']}
        data_series = pd.DataFrame(series['Obs']).rename(columns=column_names)[column_names.values()]
        data_series['date'] = self._handle_date_format(data_series['date'], series['@FREQ'])
        data_series[series['@INDICATOR']] = data_series[series['@INDICATOR']].astype('float')
        data_series['country'] = series['@REF_AREA']
        data_series = data_series.set_index(['date', 'country'])
        return data_series
    
    def get_data(self, query):
        try:
            res = requests.get(query)
            res_text = res.json()['CompactData']['DataSet']
        except:
            res_text = []
            warnings.warn('Server denied the request.', UserWarning)
        if 'Series' in res_text:
            res_series = res_text['Series']
            if type(res_series)==list:
                countries = set([s['@REF_AREA'] for s in res_series])
                formated_series = [(s['@REF_AREA'], self.format_series(s)) for s in res_series]
                country_data = {c:[data for name, data in formated_series if name==c] for c in countries}
                data = pd.concat([pd.concat(d, axis=1) for d in country_data.values()])
            else:
                data = self.format_series(res_series)
            return data
        return None

    def get_series(self, indicator, country, startYear, endYear, frequency='A'):
        country_code = self.get_country_code(country) if type(country)==str else '+'.join([self.get_country_code(c) for c in country])
        indicator = indicator if type(indicator)==str else '+'.join(indicator)
        self.query = f'{IMF_API.url}/{IMF_API.query_method}/{self.database}/{frequency}.{country_code}.{indicator}?startPeriod={startYear}&endPeriod={endYear}'
        data = self.get_data(self.query)
        if type(data)!=type(None):
            data.rename(columns={col:self.get_indicator_name(col) for col in data.columns}, inplace=True)
        return data

    @staticmethod
    def get_valid_years(col):
        fvi = col.first_valid_index()
        lvi = col.last_valid_index()
        return f"{fvi.year}-{lvi.year}" if not pd.isna(fvi) else np.nan

    def search_data_availability(self, search, country, startYear, endYear, frequency='A'):
        if type(search)==str:
            indicator_results = self.indicator_search(search)
        else: 
            indicator_results = pd.DataFrame({"@value":search, '#text':[self.get_indicator_name(i) for i in search]})
        reverse_name_mapping = {v:k for k, v in indicator_results.set_index('@value')['#text'].to_dict().items()}
        countires = [country] if type(country)==str else country
        country_codes = [self.get_country_code(c) for c in countires]
        freq_mapping = {'A':'AS', 'Q':'QS', 'M':'MS'}

        if len(indicator_results) == 0:
            warnings.warn(f'Search term "{search}" was not found in the {self.database} database.')
            return None
        dataset = self.get_series(indicator_results['@value'].values, country, startYear, endYear, frequency)
        if type(dataset)==type(None):
            return None

        # custom index for adding back all the missing values
        date_index = dataset.reset_index()['date']
        pindex = pd.date_range(start=date_index.min(), end=date_index.max(), freq=freq_mapping[frequency])
        full_index = pd.MultiIndex.from_product([pindex, country_codes], names=['date', 'country'])
        missing_columns = set(indicator_results['#text']) - set(dataset.columns)
        
        # adding back the missing values
        for col in missing_columns:
            dataset[col] = np.NaN
        dataset.rename(columns=reverse_name_mapping, inplace=True)
        dataset = dataset.reindex(full_index)
        summary = dataset.reset_index(level=1).groupby('country').apply(lambda x: x.apply(self.get_valid_years)).drop(columns='country')
        return summary