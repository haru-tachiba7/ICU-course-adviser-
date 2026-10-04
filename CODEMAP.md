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
  level: 1,                   // fixed_categoryがnullのときだけ意味を持つ。科目番号の百の位(1/2/3/...)
  desc: "...",                 // 授業概要(CourseList.aspxから取り込み済み。739件全件にあり)
  offerings: [                // 2026年度の開講情報(複数学期分)
    { year, term, instructor, schedule, language, regno, syllabus_url }
  ]
}
```

**区分(基礎科目/専攻科目/選択科目)はここには入っていない。** 選択中の履修形態・メジャー・
第二メジャー/マイナーによって変わるため、`index.html`内の`courseCategory(course)`関数が
その場で判定する(下記4章参照)。ELA/JLP/一般教育/保健体育/卒業研究の5つだけは`fixed_category`に
固定の区分名が直接入っている。

`level`は「100番台=1」で固定ではなく、**科目番号の百の位をそのまま**入れている(200番台=2、
300番台=3)。ダブルメジャーの「300番台を最低3単位」ルールはこの値で`level >= 3`を判定している。

### data.js — `CATEGORIES`(配列、8件・「メジャーのみ」のデフォルト値)

```js
{ id: "ela", name: "英語(ELA)", required_credits: 0 }
```

**これはあくまで規定値であり、アプリが実際に使う区分一覧ではない。** 履修形態(メジャーのみ/
ダブルメジャー/メジャー・マイナー)によって区分の本数・必要単位が変わるため、index.html側の
`buildCategoriesForMode(mode)`がその都度組み立てた`ACTIVE_CATEGORIES`を使う(下記4-2参照)。
`required_credits`はさらに、ユーザーが数字をクリックして変更した場合は`localStorage`の
`icu_planner_category_overrides_v1`に上書き値が保存される(data.js自体は変更されない)。

### cap_rules.js — `CAP_RULES`(配列、2件・履修形態によらず共通のものだけ)

```js
{ id: "ge_excess_to_elective", category_id: "ge", type: "excess_cap",
  max_credits: 9, description: "..." }
```

`type`は`excess_cap`(その区分の必修を超えた分のうち、最大何単位まで選択科目に算入できるか)のみ。
基礎科目の「メジャーから最低6単位」ルールと、ダブルメジャーの「300番台を最低3単位」ルールは、
履修形態によって本数・対象メジャーが変わるため、このファイルではなく index.html の
`renderCapRules`関数が毎回動的に組み立てる(下記4-3参照)。

### majors.js — `MAJORS`(配列、30件)・`ELA_STREAMS`(配列、4件)

```js
{ prefix: "ECO", name: "経済学" }
{ id: "stream3", label: "Stream 3", ela_credits: 22,
  elective_credits: { single: 40, double: 10, minor: 25 } }
```

`elective_credits`は履修形態ごとに値が違う(ディプロマ・ポリシー及び卒業要件 p.9掲載の表)ため、
オブジェクトになっている。

---

## 3. index.html — CSS(デザイン)部分

`:root`にCSS変数で色を定義。ライトモードがデフォルト値、`@media (prefers-color-scheme: dark)`と
`:root[data-theme="dark"]`の2箇所でダークモード用の値に上書きしている(どちらも同じ値)。

主なクラス:

- `.ledger` / `.cat-row` / `.bar-track` … 左側の卒業要件充足状況(進捗バー)
- `.cap-rules` … 単位上限・下限ルールの表示(進捗バーの下)
- `.browser` / `.add-mode` / `table.courses` … 右側の科目検索・一覧
- `.title-btn` / `.detail-row` … 科目タイトルをクリックして開く詳細(概要・開講情報)
- `.enrolled` / `.erow` / `.chip` … 履修リスト(自分のデータ)
- `.toast` … 追加直後に出る「取り消し」通知
- `.tutorial-highlight` / `.tutorial-card` … 初回チュートリアルのスポットライト・説明カード

---

## 4. index.html — JS部分(関数ごとの役割)

### 4-1. 状態の読み書き(localStorageまわり)

| localStorageのキー | 何を保存するか | 読み書き関数 |
|---|---|---|
| `icu_planner_enrollments_v1` | 履修リスト(追加した科目の配列) | `loadEnrollments` / `saveEnrollments` |
| `icu_planner_category_overrides_v1` | 必要単位の上書き値(区分id → 数値) | `loadOverrides` / `saveOverrides` |
| `icu_planner_major_v1` | 選択中のメジャー(接頭辞) | `loadMajor` / `saveMajor` |
| `icu_planner_mode_v1` | 履修形態('single'/'double'/'minor') | `loadMode` / `saveMode` |
| `icu_planner_secondary_major_v1` | 第二メジャー/マイナー(接頭辞。履修形態がsingle以外のときだけ使う) | `loadSecondary` / `saveSecondary` |
| `icu_planner_ela_stream_v1` | 選択中のELAストリーム | `loadElaStream` / `saveElaStream` |
| `icu_planner_add_status_v1` | 「追加時の状態」の選択 | `loadAddStatus` / `saveAddStatus` |
| `icu_planner_tutorial_done_v1` | チュートリアルを最後まで見た/スキップしたか | `isTutorialDone` / (`startTutorial`〜`endTutorial`内で設定) |

履修リストの1件(enrollment)の形:

```js
{ id: "e_...", course_no: "ISC103", title_ja: "...", credit: "3",
  category_id: "major", status: "履修済", term_label: "" }
```

### 4-2. 参照用の下ごしらえ(定数・ヘルパー関数)

- `majorByPrefix` … `MAJORS`を接頭辞で引けるようにしたオブジェクト
- `courseByNo` … `COURSES`を科目番号で引けるようにしたオブジェクト(300番台チェックなどで使用)
- `buildCategoriesForMode(mode)` … **区分一覧の組み立て本体**。'single'/'double'/'minor'を受け取り、
  その履修形態での`CATEGORIES`相当の配列を毎回新しく作って返す(専攻科目が1本か2本か、
  必要単位がいくつかなど)
- `rebuildCategories()` … `buildCategoriesForMode(currentMode)`を呼び、結果を`ACTIVE_CATEGORIES`
  `catById` `catByName`(グローバル変数、`let`で再代入可能)に反映する。**履修形態を切り替えるたびに
  呼び直す必要がある**(`renderModeSelect`のchangeハンドラ内で呼んでいる)
- `applyStreamOverride()` … 選択中のELAストリーム(`currentElaStream`)と履修形態(`currentMode`)から、
  英語(ELA)・選択科目の必要単位を`categoryOverrides`に書き込む。ELAストリームを変更したときと、
  履修形態を変更したとき(ストリーム選択済みの場合のみ)の両方から呼ばれる
- `parseCredit(raw)` … `"3"`, `"(6)"`, `"3/(9)"`, `"1/3"`のような単位表記を数値にする
- `displayCredit(raw)` … 一覧表示用(`1/3`はそのまま文字列で見せる)
- `fmtNum(n)` … 小数点誤差を丸めて表示用文字列にする
- `courseCategory(course)` … **区分判定の本体**。引数なしで、モジュール内の`currentMode` /
  `currentMajor` / `currentSecondary`を直接見て判定する。
  `fixed_category`があればそれを返す。`prefix`が`currentMajor`と一致すれば基礎科目/専攻科目(メジャー)、
  `currentMode`が'single'以外で`currentSecondary`と一致すれば基礎科目/専攻科目(メジャー2またはマイナー)、
  どちらにも一致しなければ基礎科目/選択科目。返す文字列は`catById[...].name`から取るので、
  区分名は`buildCategoriesForMode`の定義と自動的に一致する
- `fmtTerms(offerings)` … 開講学期を「春/秋」のような文字列にする
- `setOverride(id, val, defaultVal)` … 必要単位の上書きを保存(規定値と同じならoverrideを消す)
- `buildDetailRow(course)` … 科目タイトルをクリックしたときの詳細行(概要・開講情報・シラバスリンク)を組み立てる

### 4-3. 描画関数(render〜)

| 関数 | 何を描画するか | 呼ばれるタイミング |
|---|---|---|
| `renderModeSelect` | ヘッダーの「履修形態」選択肢 | 初期化時のみ(changeハンドラ内で`rebuildCategories`等を呼ぶ) |
| `renderPrimaryLabel` | 「メジャー」ラベルの接尾辞(ダブルメジャー時だけ「1(卒業研究を行う)」) | 履修形態が変わるたび |
| `renderMajorSelect` | ヘッダーのメジュー選択肢 | 初期化時のみ(中身は固定) |
| `renderSecondarySelect` | ヘッダーの「メジャー2/マイナー」選択肢の中身 | 初期化時のみ(選択肢自体はMAJORS全件で固定) |
| `renderSecondaryVisibility` | 「メジャー2/マイナー」欄の表示・非表示とラベル文言 | 履修形態が変わるたび |
| `renderElaStreamSelect` | ヘッダーのELAストリーム選択肢 | 初期化時のみ |
| `renderCategoryFilter` | 科目一覧の「区分」絞り込み選択肢 | 初期化時 + 履修形態が変わるたび(区分構成が変わるため) |
| `renderPrefixFilter` | 科目一覧の「メジャー」絞り込み選択肢 | 初期化時のみ |
| `renderAddStatusSeg` | 「追加時の状態」ボタン群 | 状態切替時 |
| `renderLedger` | 左側の卒業要件充足状況(進捗バー・数字) | 履修リストや履修形態・メジャーが変わるたび |
| `renderCapRules` | 単位上限・下限ルールの実数値(基礎科目の最低6単位・300番台最低3単位を含む) | `renderLedger`の最後で呼ばれる |
| `renderCourseTable` | 右側の科目一覧(検索・絞り込み後、最大80件) | 検索・絞り込み・追加・削除・履修形態変更のたび |
| `renderEnrolled` | 履修リスト本体(新しい順) | 追加・削除・状態変更のたび |

`renderLedger`が一番重要。`enrollments`を区分ごとに集計して(履修済=earned、それ以外=planned、
取りやめは除外)、`ACTIVE_CATEGORIES`(`buildCategoriesForMode`が現在の履修形態から組み立てたもの)の
`required_credits`(またはoverride)と比較して進捗バー・残り単位数を出す。

履修形態を切り替えたときの処理順序(`renderModeSelect`のchangeハンドラ)は重要で、
`rebuildCategories()` → `applyStreamOverride()` → ラベル・フィルタ・一覧の再描画、という順になっている。
先に`ACTIVE_CATEGORIES`を新しい履修形態のものに更新してからでないと、以降の描画が古い区分構成を参照してしまう。

### 4-4. 追加・削除・状態変更

- `addCourse(cno)` … 科目一覧の「＋」ボタンから呼ばれる。区分は`courseCategory`で自動判定、
  状態は`addStatus`(追加時の状態)を使ってその場で`enrollments`に追加し、トーストを出す
- `showToast(message, onUndo)` / `hideToast()` … 追加直後の取り消し通知(6秒で自動的に消える)
- `renderEnrolled`内の`setStatus(value)` … 履修リストの状態を変更(チップ or プルダウン)。
  `STATUS_MAIN`(履修済/履修中/予定/検討中)はボタン、それ以外(仮予定/確定/取りやめ)はプルダウン

### 4-5. イベントリスナー(ファイル末尾)

```js
courseBody      … 「＋」ボタン・科目タイトルのクリックを検知して addCourse / 詳細行の開閉を行う
addStatusSeg    … 追加時の状態ボタンのクリック
modeSelect      … 履修形態の変更(renderModeSelect内でattach)
majorSelect     … メジャーの変更(renderMajorSelect内でattach)
secondarySelect … メジャー2/マイナーの変更(renderSecondarySelect内でattach)
elaStreamSelect … ELAストリームの変更(renderElaStreamSelect内でattach)
searchBox       … 入力のたび renderCourseTable
catFilter       … 変更のたび renderCourseTable
prefixFilter    … 変更のたび renderCourseTable
tutorialBtn     … クリックで startTutorial (いつでもチュートリアルを開き直せる)
```

最後に初期描画を1回ずつ呼んで終わり(`renderAddStatusSeg` 〜 `renderLedger`、履修形態・第二メジャー関連を含む)。

### 4-6. チュートリアル(初回案内)

初めてサイトを開いた人向けに、5ステップのスポットライト式ガイドを表示する機能。

- `TUTORIAL_STEPS` … 各ステップの`{ selector, title, body }`の配列。`selector`はハイライトする
  実際のCSSセレクタ(`.major-select`, `.ledger`, `#capRules`, `#addStatusSeg`, `.controls`)
- `isTutorialDone()` / `markTutorialDone()` … `localStorage`の`icu_planner_tutorial_done_v1`を読み書き
- `buildTutorialOverlay()` … ハイライト枠(`.tutorial-highlight`)と説明カード(`.tutorial-card`)のDOM要素を1回だけ作る
- `startTutorial()` … ステップ0から表示開始。`document.body`に要素を追加する
- `showTutorialStep()` / `positionTutorial()` … 現在のステップの対象要素を`scrollIntoView`し、
  ハイライト枠と説明カードの位置・内容を更新する
- `endTutorial()` … 要素をDOMから外し、`markTutorialDone()`を呼ぶ(スキップ・最終ステップ完了の両方で使う)
- ページ読み込み後`setTimeout`で`isTutorialDone()===false`なら自動的に`startTutorial()`を呼ぶ
- ハイライトの「スポットライト」効果は、`.tutorial-highlight`要素自身に
  `box-shadow: 0 0 0 4000px rgba(...)`を付けて画面全体を覆う手法。要素自体は透明なので、
  対象の矩形だけが周囲より明るく浮かび上がる(別に暗幕レイヤーを重ねると二重に暗くなるため使わない)。

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
7. **科目詳細の展開表示・概要の取り込み** — 科目タイトルをクリックすると開講情報・公式シラバスへの
   リンクを表示(`buildDetailRow`)。CourseList.aspxから739科目全件の概要(`desc`)を取り込み
8. **初回チュートリアル** — 5ステップのスポットライト式ガイドを追加(4-6参照)
9. **ダブルメジャー・メジャー/マイナー対応** — 履修形態を切り替えられるようにし、
   区分一覧(`buildCategoriesForMode`)・区分判定(`courseCategory`)・単位上限ルール(`renderCapRules`)
   をすべて履修形態に応じて動的に組み立てる方式へ作り替え

---

## 6. 既知の制約・未対応の項目

- JLPの必要単位は公式資料の変動(最小12単位など)を反映しておらず、手動編集に頼っている
- シラバス詳細のうち評価方法・授業内容(週別シラバス)は未取り込み(`syllabus_url`はあるが中身は未取得。
  概要`desc`のみ取り込み済み)
- 興味度に基づく推薦ロジックは未実装
- Co-Listing科目(他メジャーの科目を自分のメジャーの基礎科目/専攻科目として計上できる特例)は未対応
- 区分分類は「100番台/200番台」の機械的判定のみで、例外(メジャー決定前後の振り分け直しなど)は反映していない
- ダブルメジャーで同じメジャーをメジャー1・メジャー2の両方に選んでも警告が出ない(想定外の組み合わせ)
- 専攻科目(メジャー2)の「300番台を最低3単位」以外のメジャー固有の特例(メジャーによって異なる
  追加要件があれば)は未反映。現状は全メジャー共通のルールのみ実装
