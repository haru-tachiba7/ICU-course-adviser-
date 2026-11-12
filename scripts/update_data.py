"""
複数年度の科目検索結果(保存HTML)から、data.js(指定年度の開講)と past.js(過去の開講・開講なしの年度)を更新する。

使い方:
    1. SearchCourseAndSyllabus.aspx で、年度を「(過去の年度) 〜 (今年度)」にし、表示件数を「ALL」にして保存する
    2. 実行する
           python3 scripts/update_data.py saved.html --year 2026 --handbook icu-all-major-listings.json
       --handbook は、CourseList.aspx から集めた科目の一覧(省略可)。
       指定すると、「今年度の開講がない科目」を、「その年度は開講されない科目」として登録する。

登録のしかた:
    - data.js の科目に、今年度の開講がない場合は offerings を空にし、not_offered: true を付ける
    - past.js の NOT_OFFERED[科目番号] に、検索した年度のうち、開講のなかった年度を入れる
    - これまでに取り込んだ授業概要(desc)は、科目番号が同じなら引き継ぐ
"""
import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_search_results import parse_html, hundred_level, FIXED_CATEGORY_PREFIX_MAP, REQUIREMENT_CATEGORIES


def load_old(root):
    src = (root / "data.js").read_text(encoding="utf-8")
    return {c["course_no"]: c for c in json.loads(re.search(r"const COURSES = (\[.*?\]);\nconst CATEGORIES", src, re.S).group(1))}


def credit_text(text):
    return re.sub(r"単位$", "", (text or "").strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--year", required=True)
    ap.add_argument("--handbook")
    a = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    old = load_old(root)
    found = parse_html(Path(a.html))
    searched = sorted({o["year"] for c in found for o in c["offerings"]})
    by_no = {c["course_no"]: c for c in found}

    courses, past = {}, defaultdict(list)
    for cno, c in by_no.items():
        cur = [o for o in c["offerings"] if o["year"] == a.year]
        if cur:
            courses[cno] = dict(c, offerings=cur, desc=(old.get(cno) or {}).get("desc"))
        for o in c["offerings"]:
            if o["year"] != a.year:
                past[cno].append(o)

    registered = 0
    if a.handbook:
        hb = json.loads(Path(a.handbook).read_text(encoding="utf-8"))["courses"]
        for h in hb:
            code = h["code"]
            if code in courses or code.startswith("Q") or code == "STH391":
                continue
            prefix = "".join(ch for ch in code if ch.isalpha())
            fixed = FIXED_CATEGORY_PREFIX_MAP.get(prefix)
            base = by_no.get(code) or old.get(code) or {}
            courses[code] = {
                "course_no": code, "title_ja": base.get("title_ja") or h["title"].replace("\u3000", " "),
                "credit": base.get("credit") or credit_text(h["creditsText"]), "prefix": prefix,
                "fixed_category": fixed, "level": None if fixed else hundred_level(code),
                "desc": (old.get(code) or {}).get("desc"), "offerings": [], "not_offered": True,
            }
            registered += 1

    not_offered = {}
    for cno in courses:
        have = {o["year"] for o in by_no.get(cno, {}).get("offerings", [])}
        missing = [y for y in searched if y not in have]
        if missing:
            not_offered[cno] = sorted(missing, reverse=True)
    for cno in past:
        past[cno].sort(key=lambda o: (-int(o["year"]), o["term"]))

    listing = sorted(courses.values(), key=lambda c: c["course_no"])
    (root / "data.js").write_text(
        "// 自動生成ファイル。scripts/update_data.py(または parse_search_results.py)で再生成できます。\n"
        f"const COURSES = {json.dumps(listing, ensure_ascii=False)};\n"
        f"const CATEGORIES = {json.dumps(REQUIREMENT_CATEGORIES, ensure_ascii=False)};\n", encoding="utf-8")
    past_out = {c: v for c, v in sorted(past.items()) if c in courses}
    (root / "past.js").write_text(
        "// 自動生成ファイル。scripts/update_data.py で再生成できます。\n"
        "// PAST[科目番号] = 過去の年度の開講 / NOT_OFFERED[科目番号] = 開講されなかった年度\n"
        f"const PAST = {json.dumps(past_out, ensure_ascii=False)};\n"
        f"const NOT_OFFERED = {json.dumps(not_offered, ensure_ascii=False)};\n", encoding="utf-8")

    offered = sum(1 for c in listing if not c.get("not_offered"))
    print(f"検索した年度: {', '.join(searched)} / data.js の年度: {a.year}")
    print(f"科目 {len(listing)} 件(開講あり {offered} 件、開講なしとして登録 {registered} 件)")
    print(f"開講 {sum(len(c['offerings']) for c in listing)} 件 / 過去の開講 {sum(len(v) for v in past_out.values())} 件 / 開講のなかった年度がある科目 {len(not_offered)} 件")
    gone = sorted(set(old) - set(courses))
    new = sorted(set(courses) - set(old))
    print(f"以前の一覧にあって、なくなった科目: {len(gone)} 件 {gone[:10]}")
    print(f"新しく入った科目: {len(new)} 件")


if __name__ == "__main__":
    main()
