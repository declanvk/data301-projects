import requests
import pandas as pd
import pathlib
import json
import pickle
import re

CASES_DF = pathlib.Path.home() / 'slopolice' / 'cases_dataframe.pickle'
CONVERTED_DF = pathlib.Path.home() / 'slopolice' / 'converted_addresses.pickle'
ADDRESS_FIELD = 'address'
API_ROOT = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
API_KEY = "AIzaSyC-NrTYVZitI2prYVSIsNJgH1NsdJ_NLuA"

def get_raw_addresses(df_path=CASES_DF):
    case_df = pd.read_pickle(str(df_path))
    return case_df[ADDRESS_FIELD]

def convert_raw_address(previous_converted=dict(), to_do=10):
    try:
        raw_addresses = get_raw_addresses()
        count = 0
        if previous_converted is None:
            previous_converted = dict()
        for index, item in raw_addresses.iteritems():
            if index not in previous_converted.keys() and count < to_do:
                previous_converted[index] = interact_raw_address(item)
                count += 1
    except Exception as e:
        print(e)
        raise e
    finally:
        return previous_converted
    
def request_from_input(input_query):
    params = {'key': API_KEY, 'input': input_query}
    autocomplete_request = requests.get(API_ROOT, params)
    predictions = [prediction['description'] for prediction in json.loads(autocomplete_request.text)['predictions']]
    return predictions
        
    
def replace_substring_in(to_search_for, minimum_search, to_check):
    substrings = [to_search_for[:-idx] for idx in range(1, len(to_search_for) - len(minimum_search) + 1)]
    substrings.insert(0, to_search_for)
    for sub in substrings:
        if sub in to_check:
            return re.sub(sub, to_search_for, to_check)
    return to_check

def interact_raw_address(raw_address):
    predictions = request_from_input(raw_address)
    
    if len(predictions) == 0:
        new_raw_address = raw_address.strip().replace(";", "")
        new_raw_address = replace_substring_in("san luis obispo", "san", new_raw_address)
        print("Retrying query with {}".format(new_raw_address))
        predictions = request_from_input(new_raw_address)
    
    print("For {}\n".format(raw_address))
    print("Returned {} predictions:".format(len(predictions)))
    for index, pred_string in enumerate(predictions):
        print("\t{}: {}".format(index, pred_string))
        
    pred_choice = -1
    while True and len(predictions) > 0:
        pred_choice = input("Index of selected, or -1 if none: ")
        try:
            pred_choice = int(pred_choice)
            break
        except ValueError:
            pass

    print()
    
    if pred_choice == -1 or len(predictions) == 0:
        return input("Enter address for '{}': ".format(raw_address))
    else:
        return predictions[pred_choice]
    
def get_previous(converted_path=CONVERTED_DF):
    if converted_path.exists():
        with converted_path.open('rb') as converted_df_file:
            return pickle.load(converted_df_file)
    else:
        return None

if __name__ == "__main__":
    previous_converted = dict()
    try:
        previous_converted = get_previous()
        previous_converted = convert_raw_address(previous_converted=previous_converted, to_do=20)
    finally:
        with CONVERTED_DF.open('wb+') as converted_df_file:
            pickle.dump(previous_converted, converted_df_file, protocol=pickle.HIGHEST_PROTOCOL)
    