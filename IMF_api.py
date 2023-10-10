import numpy as np
import pandas as pd
import re
from functools import reduce
import requests
import time
from tqdm.notebook import tqdm
import warnings

class IMF_API():
    url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc'
    query_method = 'CompactData'
    collection = 'Dataflow'
    databaseInfo = 'DataStructure'
    max_query_size = 355

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
        try:
            dataStructure = pd.DataFrame(res.json()['Structure']['KeyFamilies']['KeyFamily']['Components']['Dimension'])
            dimensions = list(dataStructure['@codelist'])
        except:
            warnings.warn(f'Failed to retrieve the code list. Please try again.', UserWarning)
            return {}

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
            dates = pd.to_datetime(dates).copy()
        elif freq=='M':
            dates = pd.to_datetime(dates).copy()
        elif freq=='Q':
            dates = pd.PeriodIndex(dates, freq='Q').to_timestamp().copy()
        else:
            warnings.warn(f'Unknown frequency {freq}', UserWarning)
        return dates

    def format_series(self, series):
        column_names = {'@TIME_PERIOD':'date', '@OBS_VALUE':series['@INDICATOR']}
        if 'Obs' not in series:
            return None
        if type(series['Obs'])==dict:
            series['Obs'] = [series['Obs']]
        data_series = pd.DataFrame(series['Obs'])
        if '@OBS_VALUE' not in data_series.columns:
            return None
        data_series = data_series.rename(columns=column_names)[column_names.values()]
        data_series['date'] = self._handle_date_format(data_series['date'], series['@FREQ'])
        data_series[series['@INDICATOR']] = data_series[series['@INDICATOR']].astype('float').copy()
        data_series['country'] = series['@REF_AREA']
        data_series = data_series.set_index(['date', 'country'])
        return data_series

    def get_data(self, query):
        try:
            res = requests.get(query)
            res_text = res.json()['CompactData']['DataSet']
        except:
            res_text = []
            warning_text = 'Server denied the request.'
            ql = len(query)
            if ql > IMF_API.max_query_size:
                warning_text+= f' The query length of {ql} exceeds the the maximum limit of {IMF_API.max_query_size}. Please try reducing the number of variables or countries per request.'
            warnings.warn(warning_text, UserWarning)
        if 'Series' in res_text:
            res_series = res_text['Series']
            if type(res_series)==list:
                countries = set([s['@REF_AREA'] for s in res_series])
                formated_series = [(s['@REF_AREA'], self.format_series(s)) for s in res_series]
                country_data = {c:[data for name, data in formated_series if name==c] for c in countries}
                data = pd.concat([pd.concat(d, axis=1) for d in country_data.values() if any(map(lambda x: None if type(x)==type(None) else type(x), d))])
            else:
                data = self.format_series(res_series)
            return data
        return None

    def make_query(self, country_codes, indicators, startYear, endYear, frequency):
        country_codes_text = '+'.join(country_codes)
        indicators_text = '+'.join(indicators)
        query = f'{IMF_API.url}/{IMF_API.query_method}/{self.database}/{frequency}.{country_codes_text}.{indicators_text}?startPeriod={startYear}&endPeriod={endYear}'
        return query

    def make_queries(self, indicator, country, startYear, endYear, frequency):
        country_codes = [self.get_country_code(country)] if type(country)==str else [self.get_country_code(c) for c in country]
        indicators = [indicator] if type(indicator)==str else list(indicator)
        v_sets = {'country_codes':[country_codes], 'indicators':[indicators]}
        q_list = [self.make_query(c, i, startYear, endYear, frequency) for c in v_sets['country_codes'] for i in v_sets['indicators']]

        while max(map(len, q_list)) > IMF_API.max_query_size:
            # Calculate total number of chars in each set
            c_counts = {k:list(map(lambda x: sum(map(len, x)), v)) for k, v in v_sets.items()}

            # Determine the largest set
            largest_set_name = max(c_counts, key=lambda x: max(c_counts[x]))
            largest_set_values_index = np.argmax(c_counts[largest_set_name])

            # Split the largest set and update v_sets
            largest_set = v_sets[largest_set_name].pop(largest_set_values_index)
            mid = len(largest_set) // 2
            v_sets[largest_set_name].extend([largest_set[mid:], largest_set[:mid]])

            # define a new q_list
            q_list = [self.make_query(c, i, startYear, endYear, frequency) for c in v_sets['country_codes'] for i in v_sets['indicators']]
        return q_list

    def get_series(self, indicator, country, startYear, endYear, frequency='A', sleep_time=3):
        # retrieve queries required to construct the dataset
        self.queries = self.make_queries(indicator, country, startYear, endYear, frequency)

        # for each query run a for loop
        data = []
        country_groups = {}
        for query in tqdm(self.queries, leave=True, desc = f'Retrieving data from {self.database}'):
            time.sleep(sleep_time)
            country_key = re.search(f'{IMF_API.query_method}\/\w+\/\w\.([\w\+]+)\.([\w\+]+)', query).group(1)
            query_data = self.get_data(query)
            if type(query_data)!=type(None):
                if country_key in country_groups:
                    country_groups[country_key].append(query_data)
                else:
                    country_groups[country_key] = [query_data]

        # merging country based data and then stacking the dataframe on to of each other
        data = [reduce(lambda x, y: pd.merge(x, y, how='outer', on=['date', 'country']), cg) for cg in country_groups.values()]
        if len(data)!=0:
            data = pd.concat(data)
        else:
            return None
        if type(data)!=type(None):
            data.rename(columns={col:self.get_indicator_name(col) for col in data.columns}, inplace=True)
        else:
            return None
        return data

    @staticmethod
    def get_valid_years(col):
        fvi = col.first_valid_index()
        lvi = col.last_valid_index()
        return f"{fvi.year}-{lvi.year}" if not pd.isna(fvi) else np.nan

    def search_data_availability(self, search, country, startYear, endYear, frequency='A', sleep_time=3):
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
        dataset = self.get_series(indicator_results['@value'].values, country, startYear, endYear, frequency, sleep_time)
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
