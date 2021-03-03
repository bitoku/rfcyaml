from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Union

import yaml
from dacite import from_dict

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

RFC_DIR = pathlib.Path(__file__).parent / 'rfc'
StrTree = List[Union[str, 'StrTree']]


class RFC:
    def __init__(self, rfc: Union[int, str], sections: Optional[List[RFCSection]] = None):
        if type(rfc) == int:
            self.n = rfc
        else:
            m = re.match(r'rfc(\d+)', rfc)
            if not m:
                raise ValueError
            self.n = int(m.group(1))
        filename = f'rfc{self.n}'
        self.yaml_file = RFC_DIR / f'{filename}.yaml'
        self.json_file = RFC_DIR / f'{filename}.json'
        self.line_file = RFC_DIR / f'rfclines{self.n}.txt'
        if not self.json_file.exists():
            raise FileNotFoundError
        if not self.yaml_file.exists():
            raise FileNotFoundError
        self._info: Optional[RFCInfo] = None
        self._sections: Optional[List[RFCSection]] = sections
        self._lines: Optional[List[str]] = None

    @property
    def lines(self) -> List[str]:
        if self._lines:
            return self._lines
        if not self.line_file.exists():
            raise FileNotFoundError
        self._lines = self._load_lines()
        return self._lines

    @property
    def sections(self) -> List[RFCSection]:
        if self._sections:
            return self._sections
        self._sections = self._load_sections()
        return self._sections

    @property
    def info(self) -> RFCInfo:
        if self._info:
            return self._info
        self._info = self._load_info()
        return self._info

    def _load_sections(self) -> List[RFCSection]:
        with open(self.yaml_file) as f:
            dict_sections = yaml.load(f, Loader)
        return [from_dict(data_class=RFCSection, data=section) for section in dict_sections]

    def _load_info(self) -> RFCInfo:
        with open(self.json_file) as f:
            dict_info = json.load(f, object_hook=decode_rfc_info)
        return from_dict(data_class=RFCInfo, data=dict_info)

    def _load_lines(self) -> List[str]:
        with open(self.line_file) as f:
            self._lines = f.readlines()
        return self._lines

    def dump(self):
        with open(self.yaml_file, "w") as f:
            yaml.dump(self.sections, f, Dumper)

    def get_text(self) -> str:
        texts: List[str] = []
        for section in self.sections:
            texts.append(section.get_text())
        one_line_text = ''.join(texts)
        # TODO: what should we do if there is no non-trivial sections...?
        if one_line_text == '':
            return self.get_text_all()
        return ''.join(texts)

    def get_text_all(self) -> str:
        ret: List[str] = []
        for section in self.sections:
            ret.append(section.get_text_all())
        return ''.join(ret)

    def get_structure(self) -> StrTree:
        return [section.get_tree() for section in self.sections]

    def print_structure(self):
        print(self.info.title)
        for section in self.sections:
            section.print_structure(indent=2)


def is_trivial_section(title: str) -> bool:
    trivial_sections = [
        r'__initial_text__',
        r'[Ss]tatus [Oo]f [Tt]his [Mm]emo',
        r'[Cc]opyright',
        r'[Tt]able [Oo]f [Cc]ontents?',
        r"[Aa]uthor('s|s')? [Aa]ddress(es)?",
        r'[Ii]ntellectual [Pp]roperty',
        r'[Aa]cknowledge?ments?$',
        r'[Rr]eferences?$',
        r'IANA Considerations?$',
        r'Security Considerations?$',
        r'Table of Figures',
        r'Abstract',
        r'Example',
    ]
    for trivial_section in trivial_sections:
        if re.search(trivial_section, title):
            return True
    return False


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
    if 'page_count' in dct:
        dct['page_count'] = int(dct['page_count'])
    return dct


@dataclass
class RFCInfo:
    draft: Optional[str]
    doc_id: str
    title: str
    authors: List[str]
    format: List[RFCFormat]
    page_count: int
    pub_status: RFCStatus
    status: RFCStatus
    source: str
    abstract: Optional[str]
    pub_date: str
    keywords: List[str]
    obsoletes: List[str]
    obsoleted_by: List[str]
    updates: List[str]
    updated_by: List[str]
    see_also: List[str]
    doi: Optional[str]
    errata_url: Optional[str]


@dataclass
class RFCSection:
    title: str
    contents: List[Union[RFCSection, str]]

    def get_text(self) -> str:
        ret = []
        if is_trivial_section(self.title):
            return ''
        for content in self.contents:
            if type(content) == str:
                ret.append(content)
            else:
                ret.append(content.get_text())
        return ''.join(ret)

    def get_text_all(self) -> str:
        ret = []
        for content in self.contents:
            if type(content) == str:
                ret.append(content)
            else:
                ret.append(content.get_text_all())
        return ''.join(ret)

    def get_tree(self) -> StrTree:
        return [self.title, [content.get_tree() for content in self.contents if type(content) == RFCSection]]

    def print_structure(self, indent=0):
        for content in self.contents:
            if isinstance(content, str):
                continue
            print(f"{' ' * indent}{content.title}")
            content.print_structure(indent+2)
