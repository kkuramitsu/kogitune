from typing import List, Dict, Type, Union, Any, Optional
import kogitune.adhocs as adhoc
import json

from .files import os, basename, zopen, safe_makedirs, write_config, read_config, join_name


def singlefy(v):
    if isinstance(v, list):
        return None if len(v) == 0 else singlefy(v[0])
    return v

def singlefy_if_single(v):
    assert isinstance(v, list)
    return v[0] if len(v) == 1 else v

def listfy(v):
    """
    常にリスト化する
    """
    if not isinstance(v, list):
        return [v]
    if v is None:
        return []
    return v


def list_tqdm(list_or_value, desc=None):
    if not isinstance(list_or_value, (list, tuple)):
        list_or_value = [list_or_value]
    if len(list_or_value) == 1:
        return list_or_value
    return adhoc.tqdm(list_or_value, desc=desc)

def is_config(path):
    return isinstance(path, str) and path.endswith('.json')

def load_config(url_path: str) -> dict:
    if url_path.startswith('https://') or url_path.startswith('http://'):
        requests = adhoc.safe_import("requests")
        response = requests.get(url_path)
        if response.status_code == 200:
            try:
                # JSONデータをインメモリでパース
                data = response.json()  # json.loads(response.text) でも可
                return data
            except json.JSONDecodeError as e:
                print(repr(e))
    with open(url_path, "r") as file:
        return json.load(file)


class VerboseCounter(object):

    def __init__(self, head=None, /, **kwargs):
        default_count = 2 if adhoc.is_verbose() else 0
        self.count = 0
        self.verbose_count = head or adhoc.get(kwargs, f"_head|verbose|head|={default_count}")
        self.color = kwargs.get('color', 'green')
        self.notice = kwargs.get('notice', '')
        self.prev_sample = None
    
    def __enter__(self):
        self.count = 0
        self.prev_sample = None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            if self.prev_sample:
                adhoc.print(adhoc.dump(self.prev_sample), face=f" 🐼[{self.count}]", color=self.color)
                self.prev_sample = None

    def print(self, *args, **kwargs) -> None:
        if self.count < self.verbose_count:
            kwargs['face'] = kwargs.get("face", "") + f"🐼[{self.count}]"
            kwargs['color'] = self.color
            adhoc.print(*args, **kwargs)
            self.count += 1

    def print_sample(self, sample:Union[dict, List[dict]]) -> None:
        if isinstance(sample, list):
            samples = sample
            for sample in samples:
                self.print_sample(sample)
            return
        if self.count < self.verbose_count:
            adhoc.print(self.notice, dump=sample, 
                        face=f" 🐼[{self.count}]", color=self.color)
            self.count += 1
        else:
            self.prev_sample = sample


def report_KeyError(e: KeyError, sample: dict):
    adhoc.print(repr(e), face="🙈")
    adhoc.print(adhoc.dump(sample), face="")
    raise e


def save_table(filename, table:dict, save_path='.'):
    import pandas as pd
    PERCENTILES = [0.05, 0.1, 0.2, 0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 0.9, 0.95, 0.99]
    df = pd.DataFrame(table)
    print(df.describe(percentiles=PERCENTILES))
    path = os.path.join(save_path, filename)
    df.to_csv(path, index=False)
    adhoc.saved(path, 'Statistics of Additional Vocabulary//追加語彙の統計')
    if path.endswith('.csv'):
        with open(path.replace('.csv', '_describe.txt'), "w") as w:
            print(df.describe(percentiles=PERCENTILES), file=w)
    