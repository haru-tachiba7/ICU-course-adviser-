"""
ICU「SearchCourseAndSyllabus.aspx」を Results: ALL 表示にしてブラウザで保存した
HTMLファイルから、科目カタログと開講情報を抽出し、data.js を再生成するスクリプト。

使い方:
    1. https://campus.icu.ac.jp/public/ehandbook/SearchCourseAndSyllabus.aspx を開く
    2. 表示件数を「ALL」に切り替える(必要なら年度・学期で絞り込む)
    3. ページを「ウェブページ、完全」などの形式で保存する
    4. 保存したHTMLをこのリポジトリのどこかに置き、下記コマンドを実行する

       python3 scripts/parse_search_results.py path/to/saved.html

    → ルートディレクトリの data.js が再生成される。

依存パッケージ: beautifulsoup4, lxml
    pip install beautifulsoup4 lxml
"""

import re
import sys
import json
from pathlib import Path
from collections import defaultdict

from bs4 import BeautifulSoup

# 科目番号の接頭辞から、機械的に判定できる卒業要件区分(語学・一般教育・保健体育・卒業研究)。
CATEGORY_PREFIX_MAP = {
    "ELA": "英語(ELA)",
    "JLP": "日本語(JLP)",
    "GEH": "一般教育",
    "GEL": "一般教育",
    "GEN": "一般教育",
    "GES": "一般教育",
    "GEX": "一般教育",
    "HPE": "保健体育",
    "STH": "卒業研究",
}

# メジャーとして選択している科目番号の接頭辞。
MAJOR_PREFIX = "ISC"


def hundred_level(course_no: str):
    """科目番号の百の位を返す(例: ISC103 -> 1, EDU201 -> 2)。数字がなければNone。"""
    m = re.search(r"\d+", course_no)
    if not m:
        return None
    return int(m.group()[0])


def classify_category(course_no: str, prefix: str):
    """CATEGORY_PREFIX_MAP に無い科目に、卒業要件上の「専門科目」ルールを適用する。
    基礎科目 = 100番台、専攻科目 = 200番台以上(ただし選択メジャーの科目のみ)、
    それ以外(他メジャーの200番台以上)は選択科目。
    """
    if prefix in CATEGORY_PREFIX_MAP:
        return CATEGORY_PREFIX_MAP[prefix]
    lvl = hundred_level(course_no)
    if lvl is None:
        return None
    if prefix == MAJOR_PREFIX:
        return "基礎科目" if lvl == 1 else "専攻科目"
    return "基礎科目" if lvl == 1 else "選択科目"

# 卒業要件(必要単位)。ELA/JLPの必要単位は個人のストリームによって変わるため、
# アプリ側で後から編集できるようになっている(ここではデフォルト値のみ)。
REQUIREMENT_CATEGORIES = [
    {"id": "ela", "name": "英語(ELA)", "required_credits": 0},
    {"id": "jlp", "name": "日本語(JLP)", "required_credits": 22},
    {"id": "ge", "name": "一般教育", "required_credits": 18},
    {"id": "hpe", "name": "保健体育", "required_credits": 2},
    {"id": "foundation", "name": "基礎科目", "required_credits": 18},
    {"id": "major", "name": "専攻科目", "required_credits": 21},
    {"id": "thesis", "name": "卒業研究", "required_credits": 9},
    {"id": "elective", "name": "選択科目", "required_credits": 40},
]


def parse_html(path: Path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id=lambda x: x and "grv_course" in x)
    if table is None:
        raise SystemExit("科目一覧のテーブルが見つかりませんでした。保存形式を確認してください。")

    catalog = {}
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue
        year, term = tds[0].get_text(strip=True), tds[1].get_text(strip=True)
        a = tds[2].find("a")
        cno = a.get_text(strip=True) if a else tds[2].get_text(strip=True)
        href = a["href"] if a else None
        regno = None
        if href:
            m = re.search(r"regno=(\d+)&year=(\d+)&term=(\d+)", href)
            if m:
                regno = m.group(1)
        title = tds[3].get_text(strip=True)
        schedule = tds[4].get_text(strip=True)
        instructor = tds[5].get_text(strip=True)
        credit = tds[6].get_text(strip=True)
        lang = tds[7].get_text(strip=True)

        prefix = "".join(ch for ch in cno if ch.isalpha())
        if cno not in catalog:
            catalog[cno] = {
                "course_no": cno,
                "title_ja": title,
                "credit": credit,
                "category": classify_category(cno, prefix),
                "isc_relevance": "高" if prefix == MAJOR_PREFIX else None,
                "interest_level": None,
                "offerings": [],
            }
        catalog[cno]["offerings"].append({
            "year": year, "term": term, "instructor": instructor,
            "schedule": schedule, "language": lang,
            "regno": regno, "syllabus_url": href,
        })

    return list(catalog.values())


def main():
    if len(sys.argv) != 2:
        raise SystemExit("使い方: python3 scripts/parse_search_results.py path/to/saved.html")

    src = Path(sys.argv[1])
    courses = parse_html(src)

    counts = defaultdict(int)
    for c in courses:
        counts[c["category"]] += 1
    print(f"抽出した科目数: {len(courses)}")
    print("区分ごとの内訳:", dict(counts))

    out_path = Path(__file__).resolve().parent.parent / "data.js"
    data_js = (
        "// 自動生成ファイル。scripts/parse_search_results.py で再生成できます。\n"
        f"const COURSES = {json.dumps(courses, ensure_ascii=False)};\n"
        f"const CATEGORIES = {json.dumps(REQUIREMENT_CATEGORIES, ensure_ascii=False)};\n"
    )
    out_path.write_text(data_js, encoding="utf-8")
    print(f"data.js を更新しました: {out_path}")


if __name__ == "__main__":
    main()
