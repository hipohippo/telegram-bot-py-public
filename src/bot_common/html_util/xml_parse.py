import xml.etree.ElementTree as ET


def parse_from_file(xml_content):
    # create element tree object
    tree = ET.parse(xml_content)
    root = tree.getroot()


def parse_from_string(xml_content):
    # create empty list for news items
    root: ET.Element = ET.fromstring(xml_content)
    root[0].findall("item")
