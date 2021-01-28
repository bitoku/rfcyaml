import codecs
import json
import pathlib
import re
from typing import List, Optional, Tuple, Union

from tqdm import tqdm

from RFC import RFC, RFCSection, RFCStatus
from matplotlib import pyplot as plt
import spacy
from multiprocessing import Pool

RFC_DIR = pathlib.Path(__file__).parent / 'rfc'
# nlp = spacy.load('en_core_web_sm')

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
        r'\[?Categor[ies|y]:? ?|CATEGOR[IES|y]|' \
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
    pages = [page[6:-3] for page in pages]
    pages[0] = ignore_trivial_line(pages[0])
    text = [line for each_page in pages for line in each_page if line.strip() != '']
    return text


def preprocess_old(n: int) -> List[str]:
    txt_file = RFC_DIR / f'rfc{n}.txt'
    pages: List[List[str]] = []
    page: List[str] = []
    with codecs.open(txt_file, 'r', 'utf-8', 'ignore') as f:
        for line in f:
            sep = False
            for c in line:
                if ord(c) == 12:
                    sep = True
                    break
            if sep:  # feedforward character
                pages.append(page)
                page = []
                continue
            page.append(line)
        if page:
            pages.append(page)
    pages = [page[5:-3] for page in pages]
    pages[0] = ignore_trivial_line(pages[0])
    text = [line for each_page in pages for line in each_page if line.strip() != '']
    return text


def extract_sections(rfc_n: int, text: List[str]):
    return get_sections_l0(text)


def get_sections_l0(text: List[str]) -> List[RFCSection]:
    sections = []
    section = []
    title = '__initial_text__'
    for line in text:
        if line[0] == ' ':
            section.append(line)
        else:
            sections.append(RFCSection(title=title, contents=[''.join(section)]))
            title = line.strip()
            section = [line]
    sections.append(RFCSection(title=title, contents=[''.join(section)]))
    return sections


def get_sections_l1(text:List[str]) -> List[RFCSection]:
    return [RFCSection(title='__initial_text__', contents=[''.join(text)])]


def section_parse(s: str) -> Optional[List[int]]:
    m = re.match(r'(\d+(\.\d+)*)\.?', s)
    current_section_number: Optional[List[int]] = None
    if m:
        current_section_number = list(map(lambda x: int(x), m.group(1).split('.')))
    if not current_section_number:
        m = re.match(r'([A-Z](\.\d+)+)\.?', s)
        if m:
            current_section_number = list(map(lambda x: intalpha(x), m.group(1).split('.')))
    if not current_section_number:
        m = re.match(r'Appendix ([A-Z])', s)
        if m:
            current_section_number = [intalpha(m.group(1))]
    if not current_section_number:
        m = re.match(r'Appendix', s)
        if m:
            current_section_number = [100]
    if not current_section_number:
        m = re.match(r'Annex ([A-Z])', s)
        if m:
            current_section_number = [intalpha(m.group(1))]
    return current_section_number


def intalpha(x: str) -> int:
    if x.isnumeric():
        return int(x)
    if len(x) > 1:
        raise NotImplementedError
    return ord(x) - ord('A') + 100


def create_tree(sections: List[RFCSection]) -> List[RFCSection]:
    new_sections: List[RFCSection] = []
    stack: List[RFCSection] = []
    latest_section_number = [0]
    latest_section: Optional[RFCSection] = None
    temp_sections: List[RFCSection] = []
    for section in sections:
        current_section_number: Optional[List[int]] = section_parse(section.title)
        if not current_section_number:
            temp_sections.append(section)
            continue
        # 番号付きセクションである場合
        if not is_successive_section(latest_section_number, current_section_number):
            # 連番でない場合
            raise Exception('section is not successive')
        if temp_sections:
            # 番号なしセクションがその前にある場合
            # 直前のセクションにcontentsを含める
            if latest_section is None:
                new_sections += temp_sections
            else:
                for temp_section in temp_sections:
                    latest_section.contents += temp_section.contents
            temp_sections = []
        while len(stack) >= len(current_section_number):
            sec = stack.pop()
            if len(stack) == 0:
                new_sections.append(sec)
            else:
                stack[-1].contents.append(sec)
        stack.append(section)
        latest_section_number = current_section_number
        latest_section = section
    while len(stack) > 0:
        sec = stack.pop()
        if len(stack) == 0:
            new_sections.append(sec)
        else:
            stack[-1].contents.append(sec)
    if temp_sections:
        new_sections += temp_sections
    return new_sections


def is_successive_section(latest, current) -> bool:
    if len(latest) == 0 and len(current) == 0:
        return True
    latest_top = latest[0] if len(latest) > 0 else -1
    current_top = current[0] if len(current) > 0 else -1
    if latest_top > current_top:
        return False
    if latest_top < current_top:
        return True
    return is_successive_section(latest[1:], current[1:])


def check_dup(sections: List[RFCSection]):
    a = set()
    for section in sections:
        if section.title in a:
            return True
        a.add(section.title)
    return False


def main(start, end):
    for i in tqdm(range(start, end+1)):
        try:
            rfc = RFC(i)
            sections = rfc.sections
            if rfc.info.status in {
                RFCStatus.PROPOSED_STANDARD,
                RFCStatus.INTERNET_STANDARD,
                RFCStatus.DRAFT_STANDARD
            } and not rfc.info.obsoleted_by:
                new_sections = create_tree(sections)
                rfc = RFC(i, new_sections)
                rfc.dump()
        except FileNotFoundError:
            continue


def lines(n):
    try:
        rfc = RFC(n)
        text = rfc.get_text()
        text = ' '.join([sentence.strip() for sentence in text.split('\n')])
        text = re.sub(r' o | - |-+>|<-+|=+|--+|[+-]+|\||_+|\+|\*', ' ', text)

        doc = nlp(text)
        sents = list(doc.sents)
        new_sents = []

        for sent in sents:
            ss = str(sent).strip()
            if len(ss.split()) <= 4:
                continue
            if re.search(r'\W{5,}', ss):
                continue
            new_sents.append(str(sent).strip() + '\n')
        with open(RFC_DIR / f'rfclines{n}.txt', 'w') as f:
            f.writelines(new_sents)
    except FileNotFoundError:
        return
    except ValueError:
        print(n)


def concat_contents(x: int, start: str, end: str):
    rfc = RFC(x)
    sections = []
    stop = False
    for section in rfc.sections:
        if section.title == end:
            stop = False
        if not stop:
            sections.append(section)
        else:
            sections[-1].contents += section.contents
        if section.title == start:
            stop = True
    r = RFC(x, sections)
    r.dump()


def remove_footer(x: int):
    rfc = RFC(x)
    sections = []
    for section in rfc.sections:
        if re.match(f'RFC {x}', section.title):
            continue
        sections.append(section)
    r = RFC(x, sections)
    r.dump()


def print_sec(sections: List[Union[str, RFCSection]], indent=0):
    for section in sections:
        if isinstance(section, str):
            continue
        print('  ' * indent + section.title)
        print_sec(section.contents, indent+1)
