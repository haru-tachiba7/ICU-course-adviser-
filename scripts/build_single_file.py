"""
リポジトリの index.html + data.js + cap_rules.js を1つの自己完結HTMLに結合する。
Claudeのアーティファクト(claude.ai上でのプレビュー)公開用。
GitHub Pagesで公開する場合はこのスクリプトは不要(index.htmlをそのまま使う)。
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
index_html = (root / "index.html").read_text(encoding="utf-8")
data_js = (root / "data.js").read_text(encoding="utf-8")
cap_rules_js = (root / "cap_rules.js").read_text(encoding="utf-8")
majors_js = (root / "majors.js").read_text(encoding="utf-8")

merged = index_html.replace(
    '<script src="data.js"></script>\n<script src="cap_rules.js"></script>\n<script src="majors.js"></script>',
    f'<script>\n{data_js}</script>\n<script>\n{cap_rules_js}</script>\n<script>\n{majors_js}</script>'
)

out = root / "dist_single_file.html"
out.write_text(merged, encoding="utf-8")
print(f"wrote {out} ({len(merged.encode('utf-8'))} bytes)")
