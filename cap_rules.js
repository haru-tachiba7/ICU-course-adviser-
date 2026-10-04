// 自動生成ファイル。
// 基礎科目の「メジャーから最低6単位」ルールと、ダブルメジャーの「非卒業研究メジャーの専攻科目のうち
// 300番台を最低3単位」ルールは、履修形態(シングル/ダブル/マイナー)によって本数・対象が変わるため、
// ここではなく index.html の buildDynamicCapRules() で動的に生成する。
const CAP_RULES = [{"id": "ge_excess_to_elective", "category_id": "ge", "type": "excess_cap", "max_credits": 9, "description": "一般教育科目の必修(18単位)を超えた分は、最大9単位まで選択科目として計上できる"}, {"id": "hpe_excess_to_elective", "category_id": "hpe", "type": "excess_cap", "max_credits": 2, "description": "保健体育科目の必修(2単位)を超えた分(必修以外の講義・実技)は、最大2単位まで選択科目として計上できる"}];
