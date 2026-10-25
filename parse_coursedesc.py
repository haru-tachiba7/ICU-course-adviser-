"""
CourseList.aspx で特定のメジャー/カテゴリを選んだ状態でブラウザ保存したHTMLから、
科目の概要(desc)を抽出し、data.js の COURSES に反映するスクリプト。

使い方:
    1. https://campus.icu.ac.jp/public/ehandbook/CourseList.aspx を開く
    2. 左側のメジャー名(または全学共通科目のタブ)をクリック
    3. ページを保存する(「ウェブページ、完全」などの形式)
    4. 保存したHTMLを使って実行する

       python3 scripts/parse_coursedesc.py path/to/saved1.html path/to/saved2.html ...

    → 複数ファイルを一度に渡せる。data.js のCOURSESのうち、該当する科目番号の
      desc欄だけを更新する(他のデータはそのまま)。data.js に存在しない科目番号
      (2026年度に開講されていない科目など)はスキップし、一覧表示する。

依存パッケージ: beautifulsoup4, lxml
"""

import re
import sys
import json
from pathlib import Path

from bs4 import BeautifulSoup

CODE_PATTERN = re.compile(r'^([A-Z]{2,4}\d{3}[A-Z]?)\s+([A-Z](?:,[A-Z])*)$')


def extract_entries(html: str):
    """保存HTML内の全テーブルを走査し、(科目番号, タイトル+概要の結合テキスト)を集める。
    CourseList.aspxは選んだメジャー/カテゴリによってテーブルidが変わりうるため、
    特定のidに決め打ちせず、パターンに合う行をすべて拾う。
    """
    soup = BeautifulSoup(html, "lxml")
    entries = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr", recursive=False) or table.find_all("tr")
        i = 0
        while i < len(rows):
            tds = rows[i].find_all("td", recursive=False) or rows[i].find_all("td")
            if len(tds) == 2:
                code_lang = tds[0].get_text(" ", strip=True)
                m = CODE_PATTERN.match(code_lang)
                if m and i + 1 < len(rows):
                    next_tds = rows[i + 1].find_all("td", recursive=False) or rows[i + 1].find_all("td")
                    if len(next_tds) == 1:
                        text = next_tds[0].get_text(" ", strip=True)
                        entries.append((m.group(1), text))
                        i += 2
                        continue
            i += 1
    # 同じ科目番号が複数テーブルから重複して拾われることがあるため、科目番号で一意化
    dedup = {}
    for cno, text in entries:
        dedup[cno] = text
    return dedup


def main():
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python3 scripts/parse_coursedesc.py path/to/saved1.html [path/to/saved2.html ...]")

    root = Path(__file__).resolve().parent.parent
    data_js_path = root / "data.js"
    src = data_js_path.read_text(encoding="utf-8")
    m_courses = re.search(r"const COURSES = (\[.*?\]);\nconst CATEGORIES", src, re.S)
    m_categories = re.search(r"const CATEGORIES = (\[.*?\]);\s*$", src, re.S)
    courses = json.loads(m_courses.group(1))
    categories = json.loads(m_categories.group(1))
    by_no = {c["course_no"]: c for c in courses}

    total_updated = 0
    all_missing = []
    for path_str in sys.argv[1:]:
        path = Path(path_str)
        html = path.read_text(encoding="utf-8", errors="ignore")
        entries = extract_entries(html)
        updated, missing = 0, []
        for cno, text in entries.items():
            c = by_no.get(cno)
            if not c:
                missing.append(cno)
                continue
            title = c["title_ja"]
            desc = text[len(title):].strip() if text.startswith(title) else text
            c["desc"] = desc or None
            updated += 1
        print(f"{path.name}: 抽出 {len(entries)}件 / 反映 {updated}件 / 未収録 {len(missing)}件")
        if missing:
            print("  未収録の科目番号(2026年度に開講されていない可能性):", ", ".join(missing))
        total_updated += updated
        all_missing.extend(missing)

    data_js = (
        "// 自動生成ファイル。scripts/parse_search_results.py で再生成できます。\n"
        f"const COURSES = {json.dumps(courses, ensure_ascii=False)};\n"
        f"const CATEGORIES = {json.dumps(categories, ensure_ascii=False)};\n"
    )
    data_js_path.write_text(data_js, encoding="utf-8")
    print(f"\n合計 {total_updated}件の概要を反映しました。data.js を更新しました。")
    if all_missing:
        print(f"未収録の科目番号は合計 {len(all_missing)}件(2026年度オファリングに含まれない科目)")


if __name__ == "__main__":
    main()
