from typing import List

import argostranslate.translate


def argos_translate(paragraphs: List[str], original_language_code: str) -> List[str]:
    return [argostranslate.translate.translate(paragraph, original_language_code, "zh") for paragraph in paragraphs]
