import io
import csv
from typing import List


def convert_json_to_csv(data: List[dict]) -> str:
    """
    Converts list of json objects to CSV
    :param data: List of objects to convert
    :return: CSV string 
    """
    sio = io.StringIO()
    csv_writer = csv.writer(sio)

    # Writing headers to the CSV file
    if data:
        csv_writer.writerow(data[0].keys())

    for item in data:
        # Writing data of CSV file
        csv_writer.writerow(item.values())
    return sio.getvalue()


def split_list_based_on_key(data: List[dict], key: str, default: str = 'inbound') -> dict:
    """
    Split list based on a key value like [{'x':'y'}, {'x':'z'}] -> {'y': [{'x':'y'}], 'z': [{'x':'z'}]}
    :param list: Input list
    :param key: Key name to split the list on
    :param default: Default value to consider if key is not found in the dict
    :return: Result dict
    """
    output_dict = {}
    for item in data:
        output_dict.setdefault(item.get(key, default), []).append(item)
    return output_dict
