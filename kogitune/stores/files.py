from typing import List, Union
import os
import re

import json
import subprocess

import gzip
import pyzstd

import kogitune.adhocs as adhoc

# ファイルシステム


def list_filenames(filenames) -> List[str]:
    if isinstance(filenames, str):
        filenames = filenames.split("|")
    return filenames


def safe_dir(dir):
    if dir.endswith("/"):
        dir = dir[:-1]
    return dir


def safe_join_path(dir, file):
    if file is None:
        return dir
    if dir.endswith("/"):
        dir = dir[:-1]
    if file.startswith("/"):
        file = file[1:]
    return f"{dir}/{file}"


def basename(path: str, split_ext=True, split_dir=True):
    if "?" in path:
        path = path.partition("?")[0]
    if "#" in path:
        path = path.partition("#")[0]
    if split_dir and "/" in path:
        path = path.rpartition("/")[-1]
    if split_dir and "\\" in path:
        path = path.rpartition("\\")[-1]
    if split_ext and "." in path:
        path = path.partition(".")[0]
    return path


def get_filename_by_pid(prefix="cache"):
    return f"{prefix}{os.getpid()}"


def get_alphapid():
    pid = os.getpid() + 17576
    ss = []
    while pid >= 26:
        ss.append(chr(ord("A") + pid % 26))
        pid //= 26
    return "".join(ss)[:3]


## file


def zopen(filepath, mode="rt"):
    if filepath.endswith(".zst"):
        return pyzstd.open(filepath, mode)
    elif filepath.endswith(".gz"):
        return gzip.open(filepath, mode)
    else:
        return open(filepath, mode)


## linenum

linenum_pattern = re.compile(r"_L(\d{2,})\D")


def extract_linenum(filepath: str):
    matched = linenum_pattern.search(filepath)
    if matched:
        return int(matched.group(1))
    return None


def rename_linenum(filepath: str, N: int, rename=False):
    linenum = extract_linenum(filepath)
    sub = "" if N == 0 else f"_L{N}"
    if linenum is None:
        newfilepath = filepath.replace(f".", f"{sub}.", 1)
    else:
        newfilepath = filepath.replace(f"_L{linenum}", sub)
    if rename:
        if os.path.exists(newfilepath):
            os.remove(newfilepath)
        if os.path.exists(filepath):
            os.rename(filepath, newfilepath)
    return newfilepath


def remove_linenum(filepath: str, rename=False):
    return rename_linenum(filepath, 0, rename=rename)


def get_linenum(filepath):
    linenum = extract_linenum(filepath)
    if linenum is not None:
        return linenum
    if filepath.endswith(".gz"):
        ret = subprocess.run(
            f"gzcat {filepath} | wc -l",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
    elif filepath.endswith(".zst"):
        ret = subprocess.run(
            f"zstd -dcf {filepath} | wc -l",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
    else:
        ret = subprocess.run(
            f"wc -l {filepath}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
    try:
        return int(ret.stdout)
    except:
        pass
    with zopen(filepath) as f:
        c = 0
        line = f.readline()
        while line:
            c += 1
            line = f.readline()
    return c


# readline


class _JSONTemplate(object):
    def __init__(self, template="{text}"):
        self.template = template
        self.test_mode = True

    def __call__(self, s) -> str:
        if self.test_mode:
            self.test_mode = False
            try:
                sample = json.loads(s)
                return self.template.format(**sample)
            except KeyError as e:
                adhoc.warn(key_error=e, template=self.template, sample=sample)
        return self.template.format(**json.loads(s))


def reader_strip(s):
    return s.strip()


def reader_json(s):
    return json.loads(s)["text"]


def reader_jsonl(s):
    return json.loads(s)["text"]


def _find_reader_fn(reader_name):
    func = globals().get(f"reader_{reader_name}")
    if func is None:
        patterns = [
            s.replace("reader_", "") for s in globals() if s.startswith("reader_")
        ]
        adhoc.warn(
            unknown_line_reader=reader_name,
            expected=patterns,
            default_line_reader="strip",
        )
        return reader_strip
    return func


def adhoc_line_reader(**kwargs):
    with adhoc.kwargs_from_stacked(**kwargs) as aargs:
        template = adhoc.get(kwargs, "json_template"]
        if template:
            return _JSONTemplate(template)
        reader_name = adhoc.get(kwargs, "line_reader|=strip"]
        return _find_reader_fn(reader_name)


def filelines(
    filenames: Union[str, List[str]], N=-1, json_template=None, line_reader="strip"
):
    reader_fn = adhoc_line_reader(json_template=json_template, line_reader=line_reader)
    if isinstance(filenames, str):
        filenames = filenames.split("|")
    for i, filename in enumerate(filenames):
        N = get_linenum(filename) if N == -1 else N
        pbar = adhoc.progress_bar(total=N, desc=f"{filename}[{i+1}/{len(filenames)}]")
        with zopen(filename) as f:
            line = f.readline()
            c = 1
            pbar.update()
            while line and c < N:
                line = reader_fn(line)
                yield line
                line = f.readline()
                c += 1
                pbar.update()
            pbar.close()
            yield line


def read_multilines(
    filenames: Union[str, List[str]],
    bufsize=4096,
    N=-1,
    json_template=None,
    line_reader="strip",
):
    if isinstance(filenames, str):
        filenames = filenames.split("|")
    if filenames[0].endswith(".jsonl"):
        line_reader = "jsonl"
    reader_fn = adhoc_line_reader(json_template=json_template, line_reader=line_reader)
    for i, filename in enumerate(filenames):
        N = get_linenum(filename) if N == -1 else N
        pbar = adhoc.progress_bar(total=N, desc=f"{filename}[{i+1}/{len(filenames)}]")
        buffer = []
        with zopen(filename) as f:
            line = f.readline()
            c = 0
            while line:
                buffer.append(reader_fn(line))
                c += 1
                pbar.update()
                if len(buffer) == bufsize:
                    yield buffer
                    buffer = []
                if N != -1 and c >= N:
                    break
                line = f.readline()
            yield buffer
        pbar.close()


def rename_linenum_cli(**kwargs):
    with adhoc.kwargs_from_stacked(**kwargs) as aargs:
        for file in adhoc.get(kwargs, "files"]:
            n = extract_linenum(file)
            if n is None:
                n = get_linenum(file)
                file = rename_linenum(file, n)


def split_file(input_file, lines_per_file):
    file_number = 1
    current_line_count = 0
    output_file = rename_linenum(input_file, N=0, rename=False)
    base, _, ext = output_file.partition(".")
    output_file = f"{base}_{file_number:03d}.{ext}"
    w = zopen(output_file, "w")
    pbar = adhoc.progress_bar(total=lines_per_file, desc=output_file)
    with zopen(input_file, "r") as infile:
        for line in infile:
            if current_line_count >= lines_per_file:
                pbar.close()
                w.close()
                file_number += 1
                current_line_count = 0
                output_file = f"{base}_{file_number:03d}.{ext}"
                w = zopen(output_file, "w")
                pbar = adhoc.progress_bar(total=lines_per_file, desc=output_file)
            w.write(line)
            current_line_count += 1
            pbar.update()
    w.close()


def split_lines_cli(**kwargs):
    with adhoc.kwargs_from_stacked(**kwargs) as aargs:
        files = list_filenames(adhoc.get(kwargs, "files|!!"])
        lines_per_file = adhoc.get(kwargs, "lines_per_file|lines|max|N|=1000000"]
        for file in files:
            split_file(file, lines_per_file)
