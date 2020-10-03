"""
finds the reference letters that define the lanes for registration
"""

from collections import Counter, namedtuple
from pprint import pprint

Lane = namedtuple("lane", ("starts_at", "ends_at", "count"))

ticket_references = [
    "07DG-1",
    "0H3O-1",
    "0OK4-1",
    "1NVU-1",
    "234B-1",
    "2I8A-1",
    "2UPC-1",
    "2XHT-1",
    "3HVY-1",
    "3MZB-1",
    "45BH-1",
    "4GHW-1",
    "53QD-1",
    "540B-1",
    "5GXH-1",
    "61KC-1",
    "6U0R-1",
    "73QB-1",
    "7A4J-1",
    "7KFN-1",
    "8TJK-1",
    "986N-1",
    "9ZJV-2",
    "ABGP-1",
    "AEUV-1",
    "AFOF-1",
    "AOH2-1",
    "APG4-1",
    "AQ0D-1",
    "ASE8-1",
    "AUWG-1",
    "AYEY-1",
    "AYGL-1",
    "BAUO-1",
    "BDMB-1",
    "BE1E-1",
    "BE83-1",
    "BEMR-1",
    "BEYI-1",
    "BGKZ-1",
    "CCTT-1",
    "CEVQ-1",
    "CIHR-1",
    "CQKM-1",
    "DBWX-1",
    "DIX5-1",
    "DKND-1",
    "DKTP-1",
    "DLWG-1",
    "DTO3-1",
    "DURJ-1",
    "EBAO-1",
    "EH3S-1",
    "EHGW-1",
    "EIAQ-1",
    "EIDG-1",
    "EIL8-1",
    "ESW6-1",
    "ESXR-1",
    "EVDB-1",
    "F1FR-1",
    "FE2F-1",
    "FV8W-1",
    "GDSG-1",
    "HAK2-1",
    "HDLN-1",
    "HKVM-1",
    "I5DF-1",
    "I5JL-1",
    "IEIW-1",
    "IEQK-1",
    "IG8U-1",
    "INGY-1",
    "IXBD-1",
    "JCX7-1",
    "JDH5-1",
    "JDH5-2",
    "JDKB-1",
    "JDRH-1",
    "JF5R-1",
    "JJQ6-1",
    "K5YD-1",
    "KCBJ-1",
    "KJAP-1",
    "KPFW-1",
    "KR1H-1",
    "LHFN-1",
    "LRN4-1",
    "MACQ-1",
    "MJEP-1",
    "MLDZ-1",
    "NE5J-1",
    "NEUP-1",
    "O3RN-1",
    "OIB5-1",
    "OSDO-1",
    "OSM5-1",
    "OWCM-1",
    "P3ZU-1",
    "PKSS-1",
    "QHVB-1",
    "QPSA-1",
    "QQQC-1",
    "QVP1-1",
    "QXWQ-1",
    "R4FG-1",
    "RM8B-1",
    "RR2J-1",
    "RR47-1",
    "RSDX-1",
    "SFPH-1",
    "SOHM-1",
    "TFDB-1",
    "TMND-1",
    "TWCQ-1",
    "TWRI-1",
    "UKCC-1",
    "UQQN-1",
    "UTHY-1",
    "UXY6-1",
    "VDMT-1",
    "VHQF-1",
    "VVRV-1",
    "VZ1I-1",
    "WEG5-1",
    "WJX9-1",
    "WNMM-1",
    "WQ1O-1",
    "WVN0-1",
    "WYQB-1",
    "WYQB-2",
    "WZXI-1",
    "WZXI-2",
    "XBFB-1",
    "XE1Z-1",
    "XIZB-1",
    "XIZB-2",
    "XZUW-1",
    "Y1XM-1",
    "Y8J0-1",
    "YDYG-1",
    "YO57-1",
    "YYCV-1",
    "Z1W8-1",
    "Z2MS-1",
    "Z2MS-2",
    "Z4RG-1",
    "Z7IG-1",
    "ZBXD-1",
    "ZBXD-2",
    "ZLDL-1",
    "ZMDP-1",
]

ticket_references = [
"ABCD-1", "ADCG-1", "AGDF-1", "ARTH-1", "AOUI-2", "ALKJH-2", "AWER-2", "ADER-2"
]
ticket_references = [
"ABCD-1", "ADCG-1", "AGDF-1", "BFDL-1", "BDFL-2", "CASL-1", "FERG-1", "MORE-2"
]

print(sorted(ticket_references))
lanes = 2

count = Counter([r[:1] for r in ticket_references])
estimate = len(ticket_references) / lanes
print(len(ticket_references))
print(estimate)


lanes = []
count_in_current_lane = 0
current_starts_at = ""
for letter in sorted(count):
    if count_in_current_lane == 0:
        current_starts_at = letter
    count_in_current_lane += count[letter]
    if count_in_current_lane > estimate:
        lanes.append(Lane(current_starts_at, letter, count_in_current_lane))
        count_in_current_lane = 0
else:
    lanes.append(Lane(current_starts_at, letter, count_in_current_lane))


pprint(lanes)
