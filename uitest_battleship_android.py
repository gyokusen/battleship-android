# -*- coding: utf-8 -*-
"""バトルシップ スマホ版の回帰テスト（Playwright・412×915・タッチ）

    python uitest_battleship_android.py

  配置 → 対戦 → 勝敗まで1局、［画像］表示、音、⚙、戦績の保存を確かめる。
"""
import os, pathlib, sys
from collections import Counter
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
URL = (HERE / "index.html").as_uri()
OUT = pathlib.Path(os.environ.get("SHOT_DIR", HERE))
ok = ng = 0


def check(name, cond, detail=""):
    global ok, ng
    if cond:
        ok += 1
        print("  OK  " + name)
    else:
        ng += 1
        print("  NG  " + name + ("  … " + str(detail) if detail else ""))


def play_out(pg):
    """自分の番が来るたびに、まだ撃っていないマスを狙って撃つ。決着まで。"""
    for _ in range(200):
        if pg.evaluate("G.phase") != "play":
            return
        pg.wait_for_function("G.phase!=='play' || (G.turn===G.human && !G.busy)", timeout=10000)
        if pg.evaluate("G.phase") != "play":
            return
        x, y = pg.evaluate("""()=>{const g=G.grids[aiId()];
            for(let y=1;y<=10;y++)for(let x=1;x<=10;x++) if(g.st(x,y)===-1) return [x,y];}""")
        pg.tap(f"#c{pg.evaluate('aiId()')}_{x}_{y}")
        pg.tap("#actsIn button[data-a=fire]")


with sync_playwright() as p:
    b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": 412, "height": 915}, is_mobile=True, has_touch=True,
                        device_scale_factor=2)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    bad = []
    pg.on("requestfailed", lambda r: bad.append(r.url))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_timeout(300)

    print("[起動]")
    check("版が出る", pg.inner_text("#ver") == "v1.0.0", pg.inner_text("#ver"))
    check("最初は［新しく始める］だけ", pg.locator("#actsIn button").count() == 1)
    w = pg.evaluate("document.querySelector('#bigSlot .c').getBoundingClientRect().width")
    check("大きい盤のマスが指で押せる大きさ（36px 以上）", w >= 36, w)
    check("横にはみ出さない", pg.evaluate("document.documentElement.scrollWidth<=innerWidth"))

    print("[⚙]")
    pg.tap("#bSet")
    check("⚙が開く", pg.is_visible("#mSet .sheet"))
    pg.select_option("#selAi", "merciless")
    pg.select_option("#selDelay", "0")
    pg.tap("#segGrid button[data-v='1']")
    check("戦績の欄に3つの相手", pg.inner_text("#statsBox").count("勝") == 3)
    pg.evaluate("CFG.view_ms=30")
    pg.tap("#bNew2")
    check("⚙が閉じて配置が始まる", not pg.is_visible("#mSet .sheet") and pg.evaluate("G.phase") == "place")
    check("大きい盤は自分の盤", pg.evaluate("document.querySelector('#bigSlot .grid').id") == "grid1")

    print("[配置]")
    check("仮置き前は［確定］が押せない", pg.is_disabled("#actsIn button[data-a=ok]"))
    pg.tap("#c1_2_2")
    check("タップで空母を仮置き（5マス）", pg.locator("#grid1 .c.pv").count() == 5)
    pg.tap("#actsIn button[data-a=ok]")
    check("確定で1隻", pg.evaluate("G.grids[1].ships.length") == 1)
    pg.tap("#c1_10_1")
    check("J1 横ははみ出して赤", pg.locator("#grid1 .c.pv.ng").count() > 0)
    check("はみ出しは［確定］が押せない", pg.is_disabled("#actsIn button[data-a=ok]"))
    pg.tap("#actsIn button[data-a=rot]")
    check("［回転］で縦になり置ける", pg.evaluate("G.preview.dir") == "V" and pg.locator("#grid1 .c.pv.ng").count() == 0)
    pg.tap("#actsIn button[data-a=ok]")
    check("2隻目", pg.evaluate("G.grids[1].ships.length") == 2)
    check("［置き直す］が出る", pg.locator("#actsIn button[data-a=reset]").count() == 1)
    pg.tap("#actsIn button[data-a=auto]")
    check("おまかせで5隻そろい対戦へ", pg.evaluate("G.grids[1].ships.length") == 5 and pg.evaluate("G.phase") == "play")
    check("自分の番は大きい盤が相手の盤", pg.evaluate("document.querySelector('#bigSlot .grid').id") == "grid2")

    print("[攻撃]")
    check("狙う前は［撃つ］が押せない", pg.is_disabled("#actsIn button[data-a=fire]"))
    pg.tap("#c2_5_5")
    check("タップで狙う（黄色）", pg.locator("#grid2 .c.aim").count() == 1)
    check("ボタンに E5 を撃つ", "E5" in pg.inner_text("#actsIn"))
    check("狙っただけでは撃たない", pg.evaluate("G.shots[1]") == 0)
    pg.tap("#c2_6_5")
    check("別のマスを狙い直せる", pg.evaluate("G.aim.x") == 6)
    pg.tap("#actsIn button[data-a=fire]")
    check("［撃つ］で1発", pg.evaluate("G.shots[1]") == 1)
    pg.wait_for_function("G.turn===G.human && !G.busy", timeout=5000)
    check("相手が撃ち返した", pg.evaluate("G.shots[2]") == 1)
    check("自分の番に戻ると相手の盤が大きい", pg.evaluate("document.querySelector('#bigSlot .grid').id") == "grid2")
    pg.tap("#c2_6_5")
    check("撃ったマスは狙えない", pg.evaluate("G.aim") is None)
    pg.screenshot(path=str(OUT / "android_play_std.png"))

    play_out(pg)
    pg.wait_for_timeout(1600)
    print("[勝敗]")
    check("決着した", pg.evaluate("G.phase") == "over")
    st = pg.evaluate("JSON.parse(localStorage.getItem('battleship_android_stats'))")
    check("戦績が1件残る", sum(v["win"] + v["lose"] for v in st.values()) == 1, st)
    check("［もう一度］が出る", pg.locator("#actsIn button[data-a=new]").count() == 1)
    names = Counter(l["name"] for l in pg.evaluate("SND.log"))
    check("音：はずれ・命中・撃沈・勝敗が鳴った",
          names["miss"] > 0 and names["hit"] > 0 and names["sunk"] > 0 and (names["win"] + names["lose"]) == 1, names)
    check("相手の音は小さめ", any(l["quiet"] for l in pg.evaluate("SND.log")))
    pg.screenshot(path=str(OUT / "android_over_std.png"))

    print("[画像表示]")
    pg.tap("#bSet")
    pg.tap("#segTheme button[data-v='img']")
    pg.tap("#segSound button[data-v='0']")
    pg.tap("#bClose")
    check("画像表示になる", pg.evaluate("document.body.classList.contains('theme-img')"))
    pg.tap("#actsIn button[data-a=new]")
    pg.tap("#actsIn button[data-a=auto]")
    pg.wait_for_timeout(100)
    bg = pg.evaluate("document.getElementById('grid1').querySelector('.c.ship').style.background")
    check("自分の艦に艦の絵", "32" in bg and ".gif" in bg, bg)
    n0 = len(pg.evaluate("SND.log"))
    x, y = pg.evaluate("""()=>{const g=G.grids[aiId()];for(let y=1;y<=10;y++)for(let x=1;x<=10;x++) if(g.st(x,y)===-1) return [x,y];}""")
    pg.tap(f"#c2_{x}_{y}")
    pg.tap("#actsIn button[data-a=fire]")
    pg.wait_for_timeout(120)
    pg.screenshot(path=str(OUT / "android_play_img.png"))
    check("音：切では鳴らない", len(pg.evaluate("SND.log")) == n0)
    play_out(pg)
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "android_over_img.png"))

    print("[開き直し]")
    pg.reload()
    pg.wait_for_timeout(300)
    check("表示・音・間の設定が残る",
          pg.evaluate("CFG.theme") == "img" and pg.evaluate("CFG.sound") is False and pg.evaluate("CFG.ai_delay_ms") == 0)
    st = pg.evaluate("JSON.parse(localStorage.getItem('battleship_android_stats'))")
    check("戦績が2件残る", sum(v["win"] + v["lose"] for v in st.values()) == 2, st)
    pg.tap("#bSet")
    pg.tap("#bClear")
    check("戦績を消せる", pg.evaluate("localStorage.getItem('battleship_android_stats')") == "{}")

    print("[広い画面]")
    pg.set_viewport_size({"width": 1000, "height": 900})
    wd = pg.evaluate("document.getElementById('app').getBoundingClientRect().width")
    check("広い画面では560pxで中央", wd == 560, wd)

    check("画面のエラー 0件", not errs, errs)
    check("読めなかったファイル 0件", not bad, bad)
    b.close()

print("\n%d 項目中 %d 通過%s" % (ok + ng, ok, "" if not ng else "（%d 件 NG）" % ng))
sys.exit(1 if ng else 0)
