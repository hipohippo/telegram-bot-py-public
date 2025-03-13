from pathlib import Path
from typing import List

import pandas as pd


def init_df(working_dir: Path):
    sub_files = list(working_dir.rglob("*"))
    names = [x.stem for x in sub_files if not x.is_dir()]
    books = [x for x in sub_files if not x.is_dir()]
    df = pd.DataFrame({"name": names, "fullpath": books})  # schema
    return df


def search_book_df(keyword: str, book_df: pd.DataFrame) -> List[Path]:
    return [
        x["fullpath"]
        for idx, x in book_df.iterrows()
        if x["name"].lower().find(keyword.lower()) >= 0
    ]
