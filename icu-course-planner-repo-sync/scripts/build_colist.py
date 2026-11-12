"""
CourseList.aspx から収集した「科目コード → 掲載メジャー名」の対応表(icu-course-major-map.json)から、
アプリが読み込む colist.js を作るスクリプト。

考え方:
    メジャーの一覧に掲載されている科目のうち、科目番号の頭3文字がそのメジャーと異なるものを、
    そのメジャーの「Co-Listing科目」とする。卒業研究の共通コード STH391 は除く。

使い方:
    python3 scripts/build_colist.py icu-course-major-map.json
    → リポジトリ直下の colist.js が更新される
"""
import re
import sys
import json
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python3 scripts/build_colist.py icu-course-major-map.json")
    root = Path(__file__).resolve().parent.parent
    majors = dict((n, p) for p, n in re.findall(r'"prefix": "([A-Z]{3})", "name": "([^"]+)"', (root / "majors.js").read_text(encoding="utf-8")))
    course_map = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    colist = {p: [] for p in majors.values()}
    unknown = set()
    for code, names in course_map.items():
        if code == "STH391":
            continue
        for name in names:
            prefix = majors.get(name)
            if prefix is None:
                unknown.add(name)
            elif not code.startswith(prefix):
                colist[prefix].append(code)
    colist = {p: sorted(set(v)) for p, v in sorted(colist.items())}

    out = ("// 自動生成ファイル。scripts/build_colist.py で再生成できます。\n"
           "// COLIST[メジャー] = そのメジャーの一覧に掲載されている、他メジャー開講(科目番号の頭3文字が異なる)の科目\n"
           f"const COLIST = {json.dumps(colist, ensure_ascii=False)};\n")
    (root / "colist.js").write_text(out, encoding="utf-8")
    for p, v in colist.items():
        print(f"{p}: {len(v)}件")
    if unknown:
        print("\nアプリに未登録のメジャー(無視しました):", "、".join(sorted(unknown)))
    print(f"\ncolist.js を作成しました({len(colist)}メジャー)。")


if __name__ == "__main__":
    main()
