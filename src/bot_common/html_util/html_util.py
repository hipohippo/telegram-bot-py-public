import logging
from typing import List, Tuple

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver


def extract_content(web_driver: WebDriver, url: str) -> Tuple[str, List[str], BeautifulSoup]:
    web_driver.switch_to.window(web_driver.window_handles[0])
    web_driver.get(url)
    soup = BeautifulSoup(web_driver.page_source, "html.parser")
    title, paragraphs = extract_from_soup(soup)
    logging.getLogger(__name__).info(f"extracted {title}")
    return title, paragraphs, soup


def paragraphs_to_html(paragraphs: List[str]):
    return "".join([f"<p>{text}</p>" for text in paragraphs])


def extract_from_soup(soup: BeautifulSoup):
    tags = soup("p")
    title = soup.find_all("title")[0].text
    paragraphs = []
    for tag in tags:
        text = tag.get_text()
        if text.find("<audio>") == -1 and text.find("hoto:") == -1 and text != "Advertisement":
            paragraphs.append(text)
    return title, paragraphs
