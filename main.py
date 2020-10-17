import codecs
import pathlib
import re
from typing import List

from RFC import RFC, RFCSection

RFC_DIR = pathlib.Path(__file__).parent / 'rfc'


def ignore_trivial_line(text: List[str]) -> List[str]:
    """Ignore blank lines or fixed lines."""
    ignore_pattern = \
        'Network Working Group|NETWORK WORKING GROUP|' \
        'Network Graphics Group|' \
        'Network Working Note|' \
        'NWG/RFC ?#|' \
        'Request [Ff]or Comments?:? |REQUEST FOR COMMENTS|REQUEST +COMMENTS|RFC|' \
        'Network Information Center |' \
        'Supercedes NWG/RFC |' \
        'Obsoletes|OBSOLETES|' \
        'Updates|UPDATES|' \
        '\[?Categor[ies|y]:? ?|CATEGOR[IES|y]|' \
        'Internet Engineering Task Force|' \
        'Related:? |' \
        'References?:? |' \
        'ISSN|' \
        'STD|' \
        'NIC: |NIC |NIC#|' \
        'FYI: |' \
        'BCP: |' \
        'IESG Note:|' \
        'IANA Note:|' \
        r'RFC\-\d+'
    lines = []
    for line in text:
        if line.strip() == '':  # remove empty line
            continue
        if re.match(ignore_pattern, line):  # remove header
            continue
        if re.search(r'\.{5,}', line):  # remove ToC
            continue
        if re.match(r'\W{32,}', line):  # remove right aligned sentence
            continue
        lines.append(line)
    return lines


def preprocess(n: int) -> List[str]:
    txt_file = RFC_DIR / f'rfc{n}.txt'
    pages: List[List[str]] = []
    page: List[str] = []
    with codecs.open(txt_file, 'r', 'utf-8', 'ignore') as f:
        for line in f:
            if ord(line[0]) == 12:  # feedforward character
                pages.append(page)
                page = []
                continue
            page.append(line)
        if page:
            pages.append(page)
    pages = [page[3:-3] for page in pages]
    pages[0] = ignore_trivial_line(pages[0])
    text = [line for each_page in pages for line in each_page if line.strip() != '']
    return text


def get_sections(text: List[str]) -> List[RFCSection]:
    sections = []
    section = []
    for line in text:
        if line[0] == ' ':
            section.append(line)
        else:
            sections.append(RFCSection(title=line.strip(), contents=[''.join(section)]))
            section = []
    return sections


def main():
    for i in range(1, 10):
        try:
            text = preprocess(i)
            rfc = RFC(i, get_sections(text))
            rfc.dump()
        except FileNotFoundError:
            continue


if __name__ == '__main__':
    main()
