from pathlib import Path
from typing import List

import pandas as pd


def init_df(working_dir: Path):
    sub_files = list(working_dir.rglob("*"))
    book_names = [x.stem for x in sub_files if not x.is_dir()]
    book_full_paths = [x for x in sub_files if not x.is_dir()]
    book_categories = [x.relative_to(working_dir).parts[0] for x in book_full_paths]
    df = pd.DataFrame(
        {"name": book_names, "fullpath": book_full_paths, "category": book_categories}
    )  # schema
    return df


def search_book_df(keyword: str, book_df: pd.DataFrame) -> List[Path]:
    return [
        x["fullpath"]
        for idx, x in book_df.iterrows()
        if x["name"].lower().find(keyword.lower()) >= 0
    ]
