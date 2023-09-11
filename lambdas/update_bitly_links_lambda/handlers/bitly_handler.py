import json
import logging
import os
import urllib3
import pandas as pd

import constants


class BitlyData(object):
    def __init__(self, bitly_key: str, company: str):
        self.token = bitly_key
        self.totals = pd.read_csv(f'{company}_sms_totals.csv')

    def make_api_call(self) -> pd.DataFrame:
        """
        Finds the last date data was pulled and queries data after that
        date. Creates pandas dataframe object from API query call.
        :return: newly queried data
        """
        GROUP_ID = os.environ[constants.ENV_BITLY_GROUP]
        COMPANY = os.environ[constants.ENV_PARTNER]
        # create object for totals parquet file
        totals = self.totals
        # get unix max time for query parameter
        totals['date_created'] = pd.to_datetime(totals['date_created'])
        max_date = totals['date_created'].max()
        created_after = int(max_date.timestamp())
        # query api for data from past two days
        http = urllib3.PoolManager()
        api_call = f'{constants.BITLY_API_DOMAIN}/groups/{GROUP_ID}/bitlinks?size=100&tags=prod-{COMPANY}-sms-invite&created_after={created_after}'
        response = http.request('GET', f'{api_call}', headers={'authorization': 'Bearer ' + f'{self.token}'})
        # turn response into a json file
        new_data = json.loads(response.data)
        json_object = json.dumps(new_data['links'], indent=4)
        with open(f'bitly_prod.json', 'w') as outfile:
            outfile.write(json_object)
        df = pd.read_json('bitly_prod.json')
        # if results are > 100 use pagination
        while new_data['pagination']['next']:
            api_call = new_data['pagination']['next']
            response_n = http.request('Get', f'{api_call}', headers={'authorization': 'Bearer ' + f'{self.token}'})
            temp_data = json.loads(response_n.data)
            json_object = json.dumps(temp_data['links'], indent=4)
            with open(f'added_bitly_prod.json', 'w') as outfile:
                outfile.write(json_object)
            df2 = pd.read_json('added_bitly_prod.json')
            df = pd.concat([df, df2])
            new_data = temp_data
        return df

    def shape_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes newly acquired data, drops columns not collected by totals
        dataframe and concatenates to create new totals dataframe
        :param df: dataframe created by API call
        :return: concatenated new totals dataframe
        """
        df['bitly_id'] = df['id'].apply(lambda x: x.split('/')[-1])
        df = df[['id', 'link', 'bitly_id', 'created_at', 'title', 'long_url']]
        df = df.rename(columns={'link': 'bitlink', 'id': 'custom_link', 'created_at': 'date_created'})
        combineddf = pd.concat([df, self.totals])
        combineddf = combineddf.drop_duplicates()
        return combineddf

    def get_click_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates a loop to query clicks for data in bitly_id column. Saves those
        values to a dictionary and updates dataframe
        :param df: dataframe consisting of newly queried data concatenated to
        total data
        :return: updated totals dataframe with latest click counts
        """
        bit_link_dict = {}
        outstanding_bitlinks = {}
        http = urllib3.PoolManager()
        old_values = self.totals
        old_values = old_values.groupby(by='bitly_id', as_index=False).agg({'alltime_clicks': 'max'})

        old_values_dict = dict(zip(old_values.bitly_id, old_values.alltime_clicks))
        # only consider links made within 28 days
        df['temp'] = df['date_created'].apply(lambda x: x.replace(tzinfo=None))
        eligible_dates_cutoff = pd.to_datetime('now') - pd.Timedelta(weeks=4)

        for i, bitlink in enumerate(df['bitly_id']):
            if df['temp'].iloc[i] >= eligible_dates_cutoff:
                api_call = f'{constants.BITLY_API_DOMAIN}/bitlinks/bit.ly/{bitlink}/clicks?unit=month'
                response = http.request('GET', f'{api_call}', headers={'authorization': 'Bearer ' + self.token})
                data = json.loads(response.data)

                click_count = 0
                if 'link_clicks' in data.keys():
                    for clicks in data['link_clicks']:
                        total = clicks['clicks']
                        click_count = click_count + total
                    if bitlink in old_values_dict:
                        click_count = max(
                            click_count, old_values_dict[bitlink])
                else:
                    if bitlink in old_values_dict:
                        logging.info(old_values_dict[bitlink])
                        click_count = old_values_dict[bitlink]
                        outstanding_bitlinks[bitlink] = str(bitlink)
                    else:
                        logging.info('zero flag', bitlink)
                        click_count = 0
                        outstanding_bitlinks[bitlink] = str(bitlink)
            else:
                click_count = old_values_dict[bitlink]
            bit_link_dict[bitlink] = click_count

        outstanding_clicks = pd.DataFrame.from_dict(outstanding_bitlinks, orient='index')
        outstanding_clicks.to_csv('clicks_needed.csv', index=False)

        # overwrite alltime_clicks col with the new queried data
        df['alltime_clicks'] = df['bitly_id'].apply(lambda x: bit_link_dict[x])
        df = df.drop('temp', axis=1)
        df = df.drop_duplicates()
        df = df.fillna('')
        df = df.groupby(
            by=(['bitly_id','custom_link', 'bitlink', 'date_created', 'title', 'long_url']), as_index=False,
        ).max()
        df = df.reset_index(drop=True)

        return df
