import codecs
import pathlib
import re
from typing import List

from matplotlib import pyplot as plt
from tqdm import tqdm

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


def extract_sections(rfc_n: int, text: List[str]):
    # These RFCs aren't able to be extracted with this method
    k0 = [
        3, 6, 10, 13, 16, 18, 19, 23, 24, 25, 27, 28, 29, 30, 32, 34, 35, 40, 41, 43, 45, 47, 49, 50, 53, 56, 57, 58,
        59, 63, 64, 66, 67, 68, 70, 71, 73, 75, 77, 81, 85, 86, 87, 93, 96, 98, 99, 103, 104, 105, 106, 107, 111, 113,
        116, 117, 123, 124, 125, 127, 129, 131, 132, 134, 140, 142, 143, 146, 147, 148, 149, 150, 151, 152, 154, 155,
        156, 163, 167, 170, 172, 173, 176, 179, 180, 181, 185, 187, 191, 193, 194, 196, 197, 198, 200, 202, 204, 206,
        207, 210, 212, 214, 216, 218, 224, 225, 226, 227, 228, 230, 231, 232, 234, 235, 236, 240, 242, 251, 253, 254,
        263, 265, 266, 269, 271, 274, 280, 283, 285, 287, 293, 294, 297, 302, 303, 307, 308, 321, 322, 324, 326, 329,
        330, 331, 332, 334, 335, 339, 340, 342, 345, 346, 347, 348, 349, 354, 356, 359, 361, 362, 363, 365, 366, 367,
        370, 371, 372, 373, 376, 382, 384, 386, 387, 390, 391, 394, 395, 396, 398, 399, 400, 401, 402, 405, 406, 410,
        411, 412, 413, 416, 421, 422, 423, 425, 429, 431, 436, 440, 446, 447, 448, 449, 450, 451, 453, 455, 456, 457,
        459, 461, 462, 464, 470, 471, 472, 474, 476, 480, 483, 485, 486, 487, 488, 489, 490, 493, 495, 496, 497, 498,
        500, 504, 506, 508, 511, 512, 513, 521, 523, 526, 531, 533, 544, 548, 550, 551, 552, 556, 559, 567, 568, 569,
        570, 578, 580, 591, 601, 602, 604, 606, 607, 608, 609, 610, 611, 612, 614, 615, 616, 617, 618, 619, 620, 621,
        622, 623, 624, 625, 626, 627, 628, 630, 631, 632, 634, 635, 636, 637, 643, 644, 657, 660, 662, 663, 669, 672,
        674, 677, 683, 684, 685, 687, 689, 690, 692, 695, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708,
        713, 716, 717, 718, 720, 722, 725, 728, 729, 730, 733, 734, 737, 738, 742, 744, 745, 747, 751, 752, 756, 757,
        763, 766, 768, 769, 774, 775, 778, 781, 782, 783, 784, 789, 794, 799, 800, 802, 803, 813, 814, 815, 816, 817,
        818, 825, 826, 828, 829, 830, 832, 833, 834, 835, 836, 837, 838, 839, 842, 843, 844, 845, 846, 847, 848, 849,
        850, 855, 862, 863, 864, 865, 866, 867, 868, 869, 877, 886, 887, 889, 891, 892, 896, 904, 911, 945, 962,
    ]
    k1 = [
        1005, 1020, 1034, 1035, 1045, 1062, 1083, 1099, 1100, 1117, 1119, 1124, 1128, 1129, 1130, 1131, 1142, 1153,
        1194, 1196, 1199, 1228, 1245, 1246, 1247, 1250, 1275, 1276, 1277, 1278, 1279, 1280, 1288, 1292, 1296, 1299,
        1305, 1311, 1319, 1320, 1321, 1340, 1360, 1399, 1410, 1499, 1500, 1540, 1543, 1599, 1600, 1610, 1632, 1699,
        1700, 1720, 1751, 1760, 1780, 1799, 1800, 1837, 1873, 1878, 1880, 1891, 1899, 1913, 1915, 1920, 1936, 1938,
        1999,
    ]
    k2 = [
        2000, 2007, 2099, 2144, 2199, 2200, 2202, 2223, 2286, 2289, 2294, 2299, 2300, 2329, 2331, 2399, 2400, 2459,
        2499, 2500, 2599, 2600, 2626, 2699, 2700, 2708, 2799, 2800, 2822, 2849, 2897, 2899, 2900, 2999,
    ]
    k3 = [
        3000, 3055, 3079, 3083, 3099, 3144, 3149, 3199, 3299, 3300, 3309, 3383, 3499, 3515, 3599, 3600, 3602, 3659,
        3662, 3700, 3791, 3839, 3887, 3917, 3944,
    ]
    k4 = [4009, 4089, 4269, 4523, 4554, 4853, 4916, ]
    k5 = [5000, 5035, 5208, 5516, 5806, 5892, ]
    k6 = [6035, 6210, 6367, 6818, ]
    k7 = [7281, 7468, 7764, ]
    k8 = [8080, 8133]
    l1 = set(k0 + k1 + k2 + k3 + k4 + k5 + k6 + k7 + k8)
    if rfc_n in l1:
        return get_sections_l1(text)
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


def main():
    bad = []
    for i in tqdm(range(1, 9000)):
        try:
            text = preprocess(i)
            rfc = RFC(i, extract_sections(i, text))
            ratio = len(rfc.sections) / len(rfc.get_all_text().split('\n'))
            if ratio > 0.2:
                bad.append((i, ratio))
            rfc.dump()
        except FileNotFoundError:
            continue
    print(bad)
    # plt.hist(ratio)
    # plt.show()


if __name__ == '__main__':
    main()
