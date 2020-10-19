from __future__ import annotations

import json
import pathlib
import re
from enum import Enum
from typing import Optional, List, Union, TypedDict

import yaml

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
            return yaml.load(f, yaml.SafeLoader)

    def _load_info(self) -> RFCInfo:
        with open(self.json_file) as f:
            return json.load(f)

    def dump(self):
        with open(self.yaml_file, "w") as f:
            yaml.dump(self.sections, f)

    def get_all_text(self):
        ret: List[str] = []
        for section in self.sections:
            ret.append(get_section_text(section))
        return ''.join(ret)


def get_section_text(section: RFCSection):
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


class RFCFormat(Enum):
    ASCII = 'ASCII'
    HTML = 'HTML'


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


def represent_section(dumper, instance):
    return dumper.represent_mapping('tag:yaml.org,2002:map', instance.items())


yaml.add_representer(dict, represent_section)
