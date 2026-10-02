# CODEMAP — 履修台帳アプリの構成

自分でコードを書き換えるための、現状のリファレンス。ファイルごとに何が入っているか、
index.html内のJSがどんな役割ごとに分かれているかをまとめている。

---

## 1. ファイル一覧

```
index.html            アプリ本体。CSS(デザイン) + HTML(画面の骨組み) + JS(全ロジック)
data.js                科目カタログ(COURSES)・卒業要件の必要単位(CATEGORIES)
cap_rules.js           単位の上限・下限ルール(CAP_RULES)
majors.js              全30メジャー一覧(MAJORS)・ELAストリーム別必要単位(ELA_STREAMS)
README.md              使い方・データ更新方法
scripts/
  parse_search_results.py  ICU公式サイトの保存HTMLから data.js を再生成する
  build_single_file.py     index.html + 3つのdata系jsを1ファイルに結合する(Claudeアーティファクト公開用)
```

`index.html`は`<script src="data.js">`のように3つのjsファイルを**外部読み込み**している。
GitHub Pagesではこの4ファイルがそのまま動く。Claudeのアーティファクトに公開するときだけ、
`build_single_file.py`でこれらを1つのHTMLに埋め込んだ`dist_single_file.html`を作る
(このファイルはリポジトリにはコミットしない、使い捨てのビルド成果物)。

---

## 2. データファイルの中身

### data.js — `COURSES`(配列、739件)

科目1件ごとのオブジェクト。

```js
{
  course_no: "ISC103",       // 科目番号
  title_ja: "...",           // 科目タイトル(日本語)
  credit: "3",                // 単位(文字列。"(6)"や"1/3"などの表記ゆれがある → parseCredit()で解釈)
  prefix: "ISC",              // 科目番号の英字部分(接頭辞)
  fixed_category: null,       // ELA/JLP/一般教育/保健体育/卒業研究の場合はその名前の文字列。それ以外はnull
  level: 1,                   // fixed_categoryがnullのときだけ意味を持つ。100番台=1、200番台以上=2
  offerings: [                // 2026年度の開講情報(複数学期分)
    { year, term, instructor, schedule, language, regno, syllabus_url }
  ]
}
```

**区分(基礎科目/専攻科目/選択科目)はここには入っていない。** 選択中のメジューによって
変わるため、`index.html`内の`courseCategory(course, majorPrefix)`関数がその場で判定する
(下記4章参照)。ELA/JLP/一般教育/保健体育/卒業研究の5つだけは`fixed_category`にメジャーに
関係なく決まる区分名が直接入っている。

### data.js — `CATEGORIES`(配列、8件)

卒業要件の区分と必要単位数。

```js
{ id: "ela", name: "英語(ELA)", required_credits: 0 }
```

`id`はアプリ内部で使うキー(ela / jlp / ge / hpe / foundation / major / thesis / elective)。
`required_credits`はデフォルト値で、ユーザーが数字をクリックして変更した場合は
`localStorage`の`icu_planner_category_overrides_v1`に上書き値が保存される
(data.js自体は変更されない)。

### cap_rules.js — `CAP_RULES`(配列、3件)

```js
{ id: "ge_excess_to_elective", category_id: "ge", type: "excess_cap",
  max_credits: 9, description: "..." }

{ id: "foundation_min_from_major", category_id: "foundation", type: "minimum_within",
  min_credits: 6, description: "..." }
```

`type`が2種類ある。

- `excess_cap` … その区分の必修を超えた分のうち、最大何単位まで選択科目に算入できるか(一般教育・保健体育)
- `minimum_within` … その区分の必要単位のうち、選択中メジャーの科目から最低何単位必要か(基礎科目)

### majors.js — `MAJORS`(配列、30件)・`ELA_STREAMS`(配列、4件)

```js
{ prefix: "ECO", name: "経済学" }
{ id: "stream3", label: "Stream 3", ela_credits: 22, elective_credits: 40 }
```

---

## 3. index.html — CSS(デザイン)部分

`:root`にCSS変数で色を定義。ライトモードがデフォルト値、`@media (prefers-color-scheme: dark)`と
`:root[data-theme="dark"]`の2箇所でダークモード用の値に上書きしている(どちらも同じ値)。

主なクラス:

- `.ledger` / `.cat-row` / `.bar-track` … 左側の卒業要件充足状況(進捗バー)
- `.cap-rules` … 単位上限・下限ルールの表示(進捗バーの下)
- `.browser` / `.add-mode` / `table.courses` … 右側の科目検索・一覧
- `.enrolled` / `.erow` / `.chip` … 履修リスト(自分のデータ)
- `.toast` … 追加直後に出る「取り消し」通知

---

## 4. index.html — JS部分(関数ごとの役割)

### 4-1. 状態の読み書き(localStorageまわり)

| localStorageのキー | 何を保存するか | 読み書き関数 |
|---|---|---|
| `icu_planner_enrollments_v1` | 履修リスト(追加した科目の配列) | `loadEnrollments` / `saveEnrollments` |
| `icu_planner_category_overrides_v1` | 必要単位の上書き値(区分id → 数値) | `loadOverrides` / `saveOverrides` |
| `icu_planner_major_v1` | 選択中のメジャー(接頭辞) | `loadMajor` / `saveMajor` |
| `icu_planner_ela_stream_v1` | 選択中のELAストリーム | `loadElaStream` / `saveElaStream` |
| `icu_planner_add_status_v1` | 「追加時の状態」の選択 | `loadAddStatus` / `saveAddStatus` |

履修リストの1件(enrollment)の形:

```js
{ id: "e_...", course_no: "ISC103", title_ja: "...", credit: "3",
  category_id: "major", status: "履修済", term_label: "" }
```

### 4-2. 参照用の下ごしらえ(定数・ヘルパー関数)

- `catById` / `catByName` … `CATEGORIES`をid・名前で引けるようにしたオブジェクト
- `majorByPrefix` … `MAJORS`を接頭辞で引けるようにしたオブジェクト
- `parseCredit(raw)` … `"3"`, `"(6)"`, `"3/(9)"`, `"1/3"`のような単位表記を数値にする
- `displayCredit(raw)` … 一覧表示用(`1/3`はそのまま文字列で見せる)
- `fmtNum(n)` … 小数点誤差を丸めて表示用文字列にする
- `courseCategory(course, majorPrefix)` … **区分判定の本体**。
  `fixed_category`があればそれを返す。なければ`prefix`が選択中メジャーと一致するかで
  基礎科目(level=1)/専攻科目(level=2)、不一致なら基礎科目/選択科目、を返す
- `fmtTerms(offerings)` … 開講学期を「春/秋」のような文字列にする
- `setOverride(id, val, defaultVal)` … 必要単位の上書きを保存(規定値と同じならoverrideを消す)

### 4-3. 描画関数(render〜)

| 関数 | 何を描画するか | 呼ばれるタイミング |
|---|---|---|
| `renderMajorSelect` | ヘッダーのメジュー選択肢 | 初期化時のみ(中身は固定) |
| `renderElaStreamSelect` | ヘッダーのELAストリーム選択肢 | 初期化時のみ |
| `renderCategoryFilter` | 科目一覧の「区分」絞り込み選択肢 | 初期化時のみ |
| `renderPrefixFilter` | 科目一覧の「メジャー」絞り込み選択肢 | 初期化時のみ |
| `renderAddStatusSeg` | 「追加時の状態」ボタン群 | 状態切替時 |
| `renderLedger` | 左側の卒業要件充足状況(進捗バー・数字) | 履修リストやメジャーが変わるたび |
| `renderCapRules` | 単位上限・下限ルールの実数値 | `renderLedger`の最後で呼ばれる |
| `renderCourseTable` | 右側の科目一覧(検索・絞り込み後、最大80件) | 検索・絞り込み・追加・削除のたび |
| `renderEnrolled` | 履修リスト本体(新しい順) | 追加・削除・状態変更のたび |

`renderLedger`が一番重要。`enrollments`を区分ごとに集計して(履修済=earned、それ以外=planned、
取りやめは除外)、`CATEGORIES`の`required_credits`(またはoverride)と比較して進捗バー・残り単位数を出す。

### 4-4. 追加・削除・状態変更

- `addCourse(cno)` … 科目一覧の「＋」ボタンから呼ばれる。区分は`courseCategory`で自動判定、
  状態は`addStatus`(追加時の状態)を使ってその場で`enrollments`に追加し、トーストを出す
- `showToast(message, onUndo)` / `hideToast()` … 追加直後の取り消し通知(6秒で自動的に消える)
- `renderEnrolled`内の`setStatus(value)` … 履修リストの状態を変更(チップ or プルダウン)。
  `STATUS_MAIN`(履修済/履修中/予定/検討中)はボタン、それ以外(仮予定/確定/取りやめ)はプルダウン

### 4-5. イベントリスナー(ファイル末尾)

```js
courseBody      … 「＋」ボタンのクリックを検知して addCourse を呼ぶ
addStatusSeg    … 追加時の状態ボタンのクリック
searchBox       … 入力のたび renderCourseTable
catFilter       … 変更のたび renderCourseTable
prefixFilter    … 変更のたび renderCourseTable
```

最後に初期描画を1回ずつ呼んで終わり(`renderAddStatusSeg` 〜 `renderLedger`)。

---

## 5. これまでの変更(コミット順)

1. **初回コミット** — スキーマ設計(Major/RequirementCategory/CourseCatalog/CourseOffering/
   Enrollment/TermPlan)、ICU公式サイトのHTML保存データから738科目を抽出、基本UIの土台
2. **区分自動分類・単位上限ルール追加** — 631件の未分類科目を「100番台=基礎科目、
   200番台以上=専攻科目(自メジャー)/選択科目(他メジャー)」で分類。`cap_rules.js`を新設
3. **全30メジャー対応・ELAストリーム選択** — 区分判定をメジャー非依存のデータ(`prefix`/`level`)
   +実行時計算(`courseCategory`)に作り替え。`majors.js`を新設
4. **単位表記の修正** — `"(6)"`や`"1/3"`のような表記を正しく数値化する`parseCredit`を追加
   (ELA・卒業研究・PEエクササイズの単位が0扱いになっていたバグを修正)
5. **追加操作のワンクリック化** — モーダルを廃止し、「追加時の状態」を選んでおいて即追加。
   取り消しトースト、履修リストでの状態変更(チップ/プルダウン)を追加
6. **余剰単位の実数値表示** — 一般教育・保健体育の「必修超過分のうち選択科目に算入できる単位数」を
   実際の履修データから計算して`renderCapRules`に表示するよう変更

---

## 6. 既知の制約・未対応の項目

- ダブルメジャー・メジャー/マイナーの単位数(専攻科目51単位など)は未対応。今は単一メジャー前提
- JLPの必要単位は公式資料の変動(最小12単位など)を反映しておらず、手動編集に頼っている
- シラバス詳細(評価方法・授業内容など)は未取り込み(`syllabus_url`はあるが中身は未取得)
- 興味度に基づく推薦ロジックは未実装
- Co-Listing科目(他メジャーの科目を自分のメジャーの基礎科目/専攻科目として計上できる特例)は未対応
- 631件の区分分類は「100番台/200番台」の機械的判定のみで、例外(メジャー決定前後の振り分け直しなど)は反映していない
