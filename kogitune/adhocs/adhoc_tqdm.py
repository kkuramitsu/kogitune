
from .main import aargs_from

# if 'get_ipython' in globals():
#     from tqdm.notebook import tqdm
# else:
#     from tqdm import tqdm

from tqdm.auto import tqdm

def adhoc_tqdm(iterable, desc=None, total=None, **kwargs):
    with aargs_from(**kwargs) as aargs:
        enabled_tqdm = aargs['enabled_tqdm|tqdm|=true']
        if enabled_tqdm:
            return tqdm(iterable, desc=desc, total=total)
        else:
            return iterable

class _DummyTqdm:
    def update(self, n=1):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

def adhoc_progress_bar(desc=None, total=None, **kwargs):
    """
    from kogitune.utils_tqdm import progress_bar

    with progress_bar(total=10) as pbar:
        for n in range(10):
            pbar.update()
    """
    with aargs_from(**kwargs) as aargs:
        enabled_tqdm = aargs['enabled_tqdm|tqdm|=true']
        if enabled_tqdm:
            return tqdm(desc=desc, total=total)
        else:
            return _DummyTqdm()

