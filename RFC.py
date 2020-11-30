from __future__ import annotations

import json
import pathlib
import re
from enum import Enum
from typing import Optional, List, Union, TypedDict

import yaml
try:
    from yaml import CLoader, CDumper as Loader, Dumper
except ImportError:
    from yaml import Loader, Dumper

RFC_DIR = pathlib.Path(__file__).parent / 'rfc'


class RFC:
    def __init__(self, rfc: Union[int, str], sections: Optional[List[RFCSection]] = None):
        if type(rfc) == int:
            self.n = rfc
        else:
            m = re.match(r'rfc(%d+)', rfc)
            if not m:
                raise ValueError
            self.n = int(m.group(1))
        filename = f'rfc{self.n}'
        self.yaml_file = RFC_DIR / f'{filename}.yaml'
        self.json_file = RFC_DIR / f'{filename}.json'
        if not self.json_file.exists():
            raise FileNotFoundError
        self.info: RFCInfo = self._load_info()
        self.sections: List[RFCSection] = sections or self._load_sections()

    def _load_sections(self) -> List[RFCSection]:
        with open(self.yaml_file) as f:
            return yaml.load(f, Loader)

    def _load_info(self) -> RFCInfo:
        with open(self.json_file) as f:
            return json.load(f, object_hook=decode_rfc_info)

    def dump(self):
        with open(self.yaml_file, "w") as f:
            yaml.dump(self.sections, f, Dumper)

    def get_text(self):
        texts: List[str] = []
        for section in self.sections:
            texts.append(get_section_text(section))
        # TODO
        one_text = ''.join(texts)
        if one_text == '':
            return self.get_text_all()
        return ''.join(texts)

    def get_text_all(self):
        ret: List[str] = []
        for section in self.sections:
            ret.append(get_section_text_all(section))
        return ''.join(ret)


def is_trivial_section(title: str) -> bool:
    initial_text = r'__initial_text__'
    status_of_this_memo = r'[Ss]tatus [Oo]f [Tt]his [Mm]emo'
    copyright_notice = r'[Cc]opyright [Nn]otice'
    table_of_contents = r'[Tt]able [Oo]f [Cc]ontents?'
    authors_address = r"[Aa]uthor('s|s')? [Aa]ddress(es)?"
    full_copyright_statement = r'[Ff]ull [Cc]opyright [Ss]tatement'
    intellectual_property = r'[Ii]ntellectual [Pp]roperty'
    acknowledgment = r'[Aa]cknowledge?ments?$'
    references = r'[Rr]eferences?$'
    if re.search(initial_text, title):
        return True
    if re.search(status_of_this_memo, title):
        return True
    if re.search(copyright_notice, title):
        return True
    if re.search(table_of_contents, title):
        return True
    if re.search(authors_address, title):
        return True
    if re.search(full_copyright_statement, title):
        return True
    if re.search(intellectual_property, title):
        return True
    if re.search(acknowledgment, title):
        return True
    if re.search(references, title):
        return True
    return False


def get_section_text(section: RFCSection):
    ret = []
    if is_trivial_section(section['title']):
        return ''
    for content in section['contents']:
        if type(content) == str:
            ret.append(content)
        else:
            ret.append(get_section_text(content))
    return ''.join(ret)


def get_section_text_all(section: RFCSection):
    ret = []
    for content in section['contents']:
        if type(content) == str:
            ret.append(content)
        else:
            ret.append(get_section_text(content))
    return ''.join(ret)


class RFCStatus(Enum):
    BEST_CURRENT_PRACTICE = 'BEST CURRENT PRACTICE'
    DRAFT_STANDARD = 'DRAFT STANDARD'
    EXPERIMENTAL = 'EXPERIMENTAL'
    HISTORIC = 'HISTORIC'
    INFORMATIONAL = 'INFORMATIONAL'
    INTERNET_STANDARD = 'INTERNET STANDARD'
    PROPOSED_STANDARD = 'PROPOSED STANDARD'
    UNKNOWN = 'UNKNOWN'
    NOT_ISSUED = 'NOT ISSUED'


class RFCFormat(Enum):
    ASCII = 'ASCII'
    HTML = 'HTML'
    PDF = 'PDF'
    PS = 'PS'
    TEXT = 'TEXT'
    XML = 'XML'
    NULL = ''


def decode_rfc_info(dct):
    if 'status' in dct:
        dct['status'] = RFCStatus(dct['status'])
    if 'pub_status' in dct:
        dct['pub_status'] = RFCStatus(dct['pub_status'])
    if 'format' in dct:
        dct['format'] = [RFCFormat(doc_format) for doc_format in dct['format']]
    return dct


class RFCInfo(TypedDict):
    draft: str
    doc_id: str
    title: str
    authors: List[str]
    format: List[RFCFormat]
    page_count: int
    pub_status: RFCStatus
    status: RFCStatus
    source: str
    abstract: str
    pub_date: str
    keywords: List[str]
    obsoletes: List[str]
    obsoleted_by: List[str]
    updates: List[str]
    updated_by: List[str]
    see_also: List[str]
    doi: str
    errata_url: Optional[str]


class RFCSection(TypedDict):
    title: str
    contents: List[Union[RFCSection, str]]
