"""
過去の年度の開講情報(開講言語・担当・シラバス)を、past.js にまとめるスクリプト。

使い方:
    1. https://campus.icu.ac.jp/public/ehandbook/SearchCourseAndSyllabus.aspx を開く
    2. 年度を過去の年度(例: 2025)にし、表示件数を「ALL」にして、ページを保存する
       (年度ごとに繰り返す。例: 2025, 2024, 2023)
    3. 保存したHTMLを指定して、実行する
           python3 scripts/parse_past_years.py saved_2025.html saved_2024.html saved_2023.html
       → リポジトリ直下の past.js が作られる

past.js の形式:
    PAST[科目番号] = [{ year, term, instructor, schedule, language, regno, syllabus_url }, ...]
    (data.js にある科目だけを入れる。data.js と同じ年度の開講は入れない)

依存パッケージ: beautifulsoup4, lxml
"""
import re
import sys
import json
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_search_results import parse_html


def main():
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python3 scripts/parse_past_years.py saved_2025.html [saved_2024.html ...]")
    root = Path(__file__).resolve().parent.parent
    src = (root / "data.js").read_text(encoding="utf-8")
    courses = json.loads(re.search(r"const COURSES = (\[.*?\]);\nconst CATEGORIES", src, re.S).group(1))
    current = {c["course_no"]: c for c in courses}
    current_years = {o["year"] for c in courses for o in c["offerings"]}

    past = defaultdict(list)
    seen = set()
    skipped = Counter()
    for path_str in sys.argv[1:]:
        for c in parse_html(Path(path_str)):
            if c["course_no"] not in current:
                skipped[path_str] += 1
                continue
            for o in c["offerings"]:
                if o["year"] in current_years:
                    continue
                key = (c["course_no"], o["year"], o["term"], o["regno"] or (o["schedule"], o["instructor"]))
                if key in seen:
                    continue
                seen.add(key)
                past[c["course_no"]].append(o)
    for cno in past:
        past[cno].sort(key=lambda o: (-int(o["year"]), o["term"]))
    years = Counter(o["year"] for v in past.values() for o in v)
    changed = sum(1 for cno, v in past.items()
                  if len({o["language"] for o in v} | {o["language"] for o in current[cno]["offerings"]}) > 1)

    out = ("// 自動生成ファイル。scripts/parse_past_years.py で再生成できます。\n"
           "// PAST[科目番号] = 過去の年度の開講(開講言語・担当・シラバス)\n"
           f"const PAST = {json.dumps(dict(sorted(past.items())), ensure_ascii=False)};\n")
    (root / "past.js").write_text(out, encoding="utf-8")
    for y, n in sorted(years.items(), reverse=True):
        print(f"{y}年度: {n}件の開講")
    print(f"対象の科目: {len(past)}件 / 開講言語が年度で異なる科目: {changed}件")
    if skipped:
        print("現在の科目一覧にない科目(無視):", sum(skipped.values()), "件")
    print("past.js を作成しました。")


if __name__ == "__main__":
    main()
