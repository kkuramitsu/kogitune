from typing import Optional
import unicodedata
from .commons import TextFilter

class UnicodeNormalization(TextFilter):

    def __init__(self, form = 'NFKC', verbose=0):
        super().__init__(verbose=verbose)
        self.form = form

    def __call__(self, text: str, record: dict) -> Optional[str]:
        return unicodedata.normalize(self.form, text)

class DuplicatedLine(TextFilter):
    """
    重複した行を取り除く
    """
    def __init__(self, prefix_length=8, **kwargs):
        """
        重複した行を取り除くフィルタを作る
        :param prefix_length: 重複をチェックする先頭の文字数
        """
        super().__init__(**kwargs)
        self.prefix_length = prefix_length

    def __call__(self, text: str, record: dict) -> Optional[str]:
        lines = ['']
        for line in text.split('\n'):
            prev = lines[-1]
            if self.prefix_length < len(line) < 80 and prev.startswith(line[:self.prefix_length]):
                if len(line) > len(prev):
                    lines[-1] = line
                continue
            if len(line.strip()) == 0 and prev == '':
                continue
            if 1 < len(prev) < 40 and not prev.endswith('。') and len(line) > 80 and line.count('。') > 1:
                if lines[-1] != '':
                    lines[-1] = f'\n{prev}'
            lines.append(line)
        return '\n'.join(lines[1:])


## 行単位の処理

class LineByLineFilter(TextFilter):
    """
    行単位の処理をするフィルター
    """
    def __init__(self, *filters, separator='\n'):
        """
        行単位の処理をするフィルターを作る
        :param sep: セパレータの調整
        """
        super().__init__(*filters)
        self.separator = separator

    def __call__(self, text: str, record: dict) -> Optional[str]:
        lines = []
        for line in text.split(self.separator):
            for f in self.filters:
                line = f(line, record)
                if line is None:
                    break
            if line:
                lines.append(line)
            else:
                lines.append('')
        if len(lines) == 0:
            return None
        return self.separator.join(lines)





