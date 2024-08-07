from .prints import (
    format_unit,
    aargs_print as print,
    open_log_file,
    notice, warn,
    saved, report_saved_files,
    start_timer, 
    describe_counters,
)

from .dicts import (
    find_simkey, 
    get_key_value,
    copy_dict_keys, move_dict_keys, transform_keys,
    parse_path_args, 
    list_keys, list_values, 
    ChainMap,
)

from .main import (
    AdhocArguments, 
    AdhocArguments as Arguments, 
    parse_main_args, 
    load_class, instantiate_from_dict,
    launch_subcommand, 
    aargs_from,
    aargs_from as from_kwargs,
    verbose_print,
)

from .inspects import (
    extract_kwargs,
    check_kwargs, # OLD
    get_parameters, 
    get_version
)

from .adhoc_tqdm import (
    adhoc_progress_bar as progress_bar,
    adhoc_tqdm as tqdm,
)

def load_tokenizer(tokenizer=None, **kwargs):
    from ..stores.tokenizers import load_tokenizer
    return load_tokenizer(tokenizer, **kwargs)



