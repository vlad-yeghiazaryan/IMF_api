import pandas as pd
import numpy as np
import requests
import time
from tqdm.notebook import tqdm_notebook

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
        matches = list(self.code_list['REF_AREA'][self.code_list['REF_AREA']['#text'].str.lower() == country_name.lower()]['@value'])
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

    def get_series(self, indicator, country, startYear, endYear, frequency='A', sleep_time=1): 
        country_code = self.get_country_code(country)
        indicator_name = self.get_indicator_name(indicator)
        query = f'{IMF_API.url}/{IMF_API.query_method}/{self.database}/{frequency}.{country_code}.{indicator}?startPeriod={startYear}&endPeriod={endYear}'
        try:
            res = requests.get(query)
            res_text = res.json()['CompactData']['DataSet']
            time.sleep(sleep_time)
        except:
            res_text = []
            print(f'Server denied the request: {indicator} for {country}')
        if 'Series' in res_text:
            if 'Obs'in res_text['Series']:
                try:
                    data = pd.DataFrame(res_text['Series']['Obs']).iloc[:,:2]
                    data.columns = ['Date', indicator_name]
                    data = data.set_index(pd.to_datetime(data['Date']))[indicator_name].astype('float')
                    data.name = indicator_name
                    return data
                except:
                    pass
        return None

    def search_data_availability(self, search, countries, startYear, endYear, frequency='A', sleep_time=1):
        indicator_results = self.indicator_search(search) if type(search)==str else pd.DataFrame({"@value":search, '#text':['']*len(search)})
        if len(indicator_results) == 0:
            print(f'Search term "{search}" was not found in the {self.database} database.')
            return None
        search_results = []
        for country in tqdm_notebook(countries, leave=True, desc = f'All countries, progress'):
            for indicator in tqdm_notebook(indicator_results['@value'].values, leave=False, desc = f'{country}'):
                query = {'indicator':indicator, 'country':country, 'startYear':startYear, 'endYear':endYear, 'frequency':frequency, 'sleep_time':sleep_time}
                data = self.get_series(**query)
                data = f'{data.index[0].year}-{data.index[-1].year}' if data is not None else 'N/A'
                result = {'@value': indicator, 'country': country, 'data_availability': data}
                search_results.append(result)
        results = pd.merge(indicator_results, pd.DataFrame(search_results), on='@value')
        return results

    def get_indicators(self, indicators, countries, startYear, endYear, frequency='A', sleep_time=1):
        dataset = []
        for country in tqdm_notebook(countries, leave=True, desc = f'All countries, progress'):
            subset = []
            for indicator in tqdm_notebook(indicators, leave=False, desc = f'{country}'):
                data = self.get_series(indicator, country, startYear, endYear, frequency, sleep_time=sleep_time)
                try:
                    data.name = ','.join(data.name.split(',')[-2:])
                    subset.append(data)
                except:
                    subset.append(None) 
            try:
                subset = pd.concat(subset, axis=1)
                subset['country'] = country
                dataset.append(subset)
            except:
                dataset.append(None)
        try:
            dataset = pd.concat(dataset)
        except:
            dataset = None
        return dataset