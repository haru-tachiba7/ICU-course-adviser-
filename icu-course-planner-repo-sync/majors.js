// 自動生成ファイル。
const MAJORS = [{"prefix": "AMS", "name": "アメリカ研究"}, {"prefix": "ANT", "name": "文化人類学"}, {"prefix": "ARC", "name": "美術・文化財研究"}, {"prefix": "AST", "name": "アジア研究"}, {"prefix": "BIO", "name": "生物学"}, {"prefix": "BUS", "name": "経営学"}, {"prefix": "CHM", "name": "化学"}, {"prefix": "DPS", "name": "開発研究"}, {"prefix": "ECO", "name": "経済学"}, {"prefix": "EDU", "name": "教育学"}, {"prefix": "ENV", "name": "環境研究"}, {"prefix": "GLS", "name": "グローバル研究"}, {"prefix": "GSS", "name": "ジェンダー・セクシュアリティ研究"}, {"prefix": "HST", "name": "歴史学"}, {"prefix": "IRL", "name": "国際関係学"}, {"prefix": "ISC", "name": "情報科学"}, {"prefix": "JPS", "name": "日本研究"}, {"prefix": "LAW", "name": "法学"}, {"prefix": "LED", "name": "言語教育"}, {"prefix": "LIT", "name": "文学"}, {"prefix": "LNG", "name": "言語学"}, {"prefix": "MCC", "name": "メディア・コミュニケーション・文化"}, {"prefix": "MTH", "name": "数学"}, {"prefix": "MUS", "name": "音楽"}, {"prefix": "PCS", "name": "平和研究"}, {"prefix": "PHR", "name": "哲学・宗教学"}, {"prefix": "PHY", "name": "物理学"}, {"prefix": "POL", "name": "政治学"}, {"prefix": "PPL", "name": "公共政策"}, {"prefix": "PSY", "name": "心理学"}, {"prefix": "SOC", "name": "社会学"}];
const ELA_STREAMS = [{"id": "stream1", "label": "Stream 1", "ela_credits": 6, "elective_credits": {"single": 56, "double": 26, "minor": 41}}, {"id": "stream2", "label": "Stream 2", "ela_credits": 10, "elective_credits": {"single": 52, "double": 22, "minor": 37}}, {"id": "stream3", "label": "Stream 3", "ela_credits": 22, "elective_credits": {"single": 40, "double": 10, "minor": 25}}, {"id": "stream4", "label": "Stream 4", "ela_credits": 25, "elective_credits": {"single": 37, "double": 7, "minor": 22}}];

// JLP(日本語教育プログラム)の配置レベル別の必要単位。
// 出典: 2026年度入学者 ディプロマ・ポリシー及び卒業要件(JLP履修対象生向け) p.7, p.10, p.12
// jlp_credits: JLPの必要単位 / ge_credits: 一般教育の必要単位 / elective_credits: 選択科目の必要単位(履修形態別)
const JLP_LEVELS = [
  {"id": "jlp_j1",     "label": "JLP J1",         "jlp_credits": 35, "ge_credits": 12, "elective_credits": {"single": 33, "double": 3,  "minor": 18}},
  {"id": "jlp_j2",     "label": "JLP J2",         "jlp_credits": 30, "ge_credits": 17, "elective_credits": {"single": 33, "double": 3,  "minor": 18}},
  {"id": "jlp_j3",     "label": "JLP J3",         "jlp_credits": 25, "ge_credits": 18, "elective_credits": {"single": 37, "double": 7,  "minor": 22}},
  {"id": "jlp_j4",     "label": "JLP J4",         "jlp_credits": 20, "ge_credits": 18, "elective_credits": {"single": 42, "double": 12, "minor": 27}},
  {"id": "jlp_intro",  "label": "JLP Intro to J", "jlp_credits": 17, "ge_credits": 18, "elective_credits": {"single": 45, "double": 15, "minor": 30}},
  {"id": "jlp_j5",     "label": "JLP J5",         "jlp_credits": 15, "ge_credits": 18, "elective_credits": {"single": 47, "double": 17, "minor": 32}},
  {"id": "jlp_sj1",    "label": "JLP SJ1+Kanji1", "jlp_credits": 14, "ge_credits": 18, "elective_credits": {"single": 48, "double": 18, "minor": 33}},
  {"id": "jlp_j6",     "label": "JLP J6",         "jlp_credits": 10, "ge_credits": 18, "elective_credits": {"single": 52, "double": 22, "minor": 37}},
  {"id": "jlp_sj2",    "label": "JLP SJ2+Kanji2", "jlp_credits": 9,  "ge_credits": 18, "elective_credits": {"single": 53, "double": 23, "minor": 38}},
  {"id": "jlp_j7",     "label": "JLP J7-A/J7-B",  "jlp_credits": 5,  "ge_credits": 18, "elective_credits": {"single": 57, "double": 27, "minor": 42}},
  {"id": "jlp_sj3",    "label": "JLP SJ3+Kanji3", "jlp_credits": 5,  "ge_credits": 18, "elective_credits": {"single": 57, "double": 27, "minor": 42}},
  {"id": "jlp_exempt", "label": "JLP 免除",       "jlp_credits": 0,  "ge_credits": 18, "elective_credits": {"single": 62, "double": 32, "minor": 47}}
];
