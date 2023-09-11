import json
import pandas as pd
import urllib3
from typing import Any, Dict

import constants


def get_click_counts(totals: pd.DataFrame, clicks_needed: pd.DataFrame, bitly_key: str) -> pd.DataFrame:
    """
    Takes in totals csv and the clicks_needed then updates as many
    click_counts as possible.
    :return: updated clicks_needed, totals_updated
    """
    bit_link_dict = {}
    outstanding_bitlinks = {}
    http = urllib3.PoolManager()
    old_values_dict = dict(zip(totals.bitly_id, totals.alltime_clicks))
    clicks_dict = {}

    # create hashmap for clicks_needed bitlinks
    for link in clicks_needed['0']:
        clicks_dict[link] = 'x'

    # from totals check if bitlink is needed if so run the api call
    # when api calls are exhausted record outstanding links for
    # next batch of calls
    for bitlink in totals['bitly_id']:
        if bitlink in clicks_dict:
            api_call = f'{constants.BITLY_API_DOMAIN}/bitlinks/bit.ly/{bitlink}/clicks?unit=month'
            response = http.request('GET', f'{api_call}', headers={'authorization': 'Bearer ' + bitly_key})
            data = json.loads(response.data)
            click_count = 0
            if 'link_clicks' in data.keys():
                for clicks in data['link_clicks']:
                    total = clicks['clicks']
                    click_count = click_count + total
                if bitlink in old_values_dict:
                    click_count = max(click_count, old_values_dict[bitlink])
            else:
                click_count = old_values_dict[bitlink]
                outstanding_bitlinks[bitlink] = str(bitlink)
        # if the values are not in clicks needed then use the value
        # from totals table
        else:
            click_count = old_values_dict[bitlink]
        bit_link_dict[bitlink] = click_count
    outstanding_clicks = pd.DataFrame.from_dict(outstanding_bitlinks, orient='index')
    outstanding_clicks.to_csv('clicks_needed_updated.csv', index=False)
    totals['alltime_clicks'] = totals['bitly_id'].apply(lambda x: bit_link_dict[x])
    return totals
