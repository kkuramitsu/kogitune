import os
from .commons import *

@adhoc.cli
def texteval_cli(**kwargs):
    """
    テキスト評価

    - files（必須）: JSONLファイル
    - texteval（必須）: 評価関数 例. "alpha-fraction"
    - input_key='text': 評価の対象となるキー
    - transform, columns: JSONを変形したいとき
    - head: 先頭だけをテストいたいとき
    - output_file: 出力先を指定したいとき
    - overwrite=False: 上書き

    例:
    ```python
    from kogitune.cli import texteval_cli

    texteval_cli(
        texteval='alpha-fraction',
        files=['jhumaneval.jsonl'],
        input_key='prompt',
        head=5,
    )
    ```
    """
    with adhoc.aargs_from(**kwargs) as aargs:
        files = listfy(aargs["files|!!"])
        textevals = adhoc.list_values(aargs["texteval|!!"])
        transform = adhoc.load("from_kwargs", "transform", **aargs)
        format_key = aargs["text_key|input_key|format|=text"]

        for filepath in files:
            record = adhoc.load("record", filepath)
            head = record.rename_save_path(**aargs)
            for i, texteval in enumerate(textevals, start=1):
                texteval = adhoc.load("texteval", texteval, **aargs)
                record_key = texteval.record_key()
                record_key = aargs[f"output_key|record_key|={record_key}"]
                if i > 1:
                    record_key = f"{record_key}.{i}"
                try:
                    verbose = VerboseCounter(head, **aargs)
                    for sample in record.samples(0, head):
                        sample = transform.transform(sample)
                        text = adhoc.get_formatted_text(sample, format_key)
                        sample[record_key] = texteval(text)
                        verbose.print_sample(sample)
                except KeyError as e:
                    report_KeyError(e, sample)
            record.save()