import xml.etree.ElementTree as ET
from typing import Union

import requests
from bs4 import BeautifulSoup


def get_hblr_alert_link(xml_content: Union[str, bytearray]):
    # create empty list for news items
    root: ET.Element = ET.fromstring(xml_content)
    travel_advisory_item = root[0].findall("item")

    hblr_alert = [
        item for item in travel_advisory_item if item.find("description").text.find("Hudson-Bergen Light Rail") >= 0
    ]
    if len(hblr_alert) > 0:
        hblr_alert_content_link = hblr_alert[0].find("link").text
    else:
        hblr_alert_content_link = None
    return hblr_alert_content_link


def extract_lightrail_alert(alert_link: str) -> str:
    resp = requests.get(alert_link)
    soup = BeautifulSoup(resp.content)
    alert_html_nodes = soup.find_all(["p", "ul"])
    for idxs, node in enumerate(alert_html_nodes):
        if node.text.find("Boarding Change") >= 0:
            break

    for idxe, node in enumerate(alert_html_nodes[::-1]):
        if node.text.find("normal weekend revenue service will resume") >= 0:
            break

    idxe = len(alert_html_nodes) - idxe
    relevant_nodes = alert_html_nodes[idxs : (idxe + 1)]
    alert_html_texts = []
    for node in relevant_nodes:
        if node.name == "p":
            alert_html_texts.append("<b>" + node.text + "</b>")
        else:
            alert_html_texts.append(node.text)
    alert_html = "\n".join(alert_html_texts)

    return (
        alert_html
        + "Tonnelle Ave to Lincoln Harbor 5 minutes \n"
        + "Liberty State Park to Lincoln Harbor 24 minutes \n"
        + "West Side Ave to Liberty State Park 7 minutes \n"
        + "West Side Ave to Harsimus Cove 18 minutes"
    )


def get_hblr_alert() -> str:
    HBLR_RSS = "https://www.njtransit.com/rss/LightRailAdvisories_feed.xml"
    xml_content = requests.get(HBLR_RSS).content
    hblr_alert_link = get_hblr_alert_link(xml_content)

    if hblr_alert_link:
        return extract_lightrail_alert(hblr_alert_link)
    else:
        return "No travel advisory alert at this moment"
