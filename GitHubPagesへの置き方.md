# GitHub Pages への置き方（バトルシップ スマホ版）

英単語例文暗記のスマホ版（`gyokusen/eigo-android`）と**同じ流れ**です。

> **先に確認**：GitHub Free では **public（公開）リポジトリでないと Pages は使えません**。
> 中身はゲームだけで、職場の情報は入っていません。
> `images` の絵は元の Excel 版（rubberduck-vba/Battleship）に入っていた素材です。
> 公開の場所に置くことになるので、気になる場合は［画像］表示の素材を外して上げてください
> （外しても［標準］表示で遊べます）。

## 0. 入れ物の名前は別にしてあります

同じ `gyokusen.github.io` に置くほかのアプリとぶつからないよう、

- 記録と設定（localStorage）の名前 … `battleship_android_prefs` / `battleship_android_stats`
- オフライン用の控え（sw.js の CACHE） … `bsa-v1`（英単語は `eiw-v1`、作業時間管理は `wta-v2`）

にしてあります。localStorage も IndexedDB も**サイト単位**で分かれ、`/battleship-android/` では分かれません。

## 1. リポジトリを作る

1. GitHub で **New repository**
2. 名前：`battleship-android`
3. **Public** を選ぶ（README などは付けない＝空のまま）
4. Create repository

## 2. 上げる（コミットはこちらで作ってあります）

Git Bash で：

```
cd /c/Users/Public/クロード/T22_バトルシップ/android
git remote add origin https://github.com/gyokusen/battleship-android.git
git push -u origin main
```

上がるもの：`index.html` / `manifest.webmanifest` / `sw.js` / `icon/` 3枚 / `images/` 17枚 /
この手引き・手引書 / `uitest_battleship_android.py` / `.gitignore`

## 3. Pages を有効にする

リポジトリの **Settings → Pages** → Source：**Deploy from a branch** → Branch：**main** / **(root)** → Save。
1〜2分で https://gyokusen.github.io/battleship-android/ が開けるようになります。

## 4. スマホに入れる

スマホの Chrome で上のURLを開き、メニュー →［ホーム画面に追加］（または［アプリをインストール］）。

## 版を上げるとき

- `index.html` だけを直したときは CACHE を変えなくてよい（画面は毎回取りに行く）
- `images` やアイコン・manifest を変えたときは sw.js の CACHE を `bsa-v2` のように上げる
- 回帰テスト：`python uitest_battleship_android.py`（Playwright が要る。クラウド作業場で動かしている）
