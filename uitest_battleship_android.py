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
    check("版が出る", pg.inner_text("#ver") == "v1.2.0", pg.inner_text("#ver"))
    check("最初は［新しく始める］だけ", pg.locator("#actsIn button").count() == 1)
    w = pg.evaluate("document.querySelector('#bigSlot .c').getBoundingClientRect().width")
    check("大きい盤のマスが指で押せる大きさ（28px 以上）", w >= 28, w)
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

    print("[並びと大きさ（v1.0.1）]")
    heads = pg.evaluate("[...document.querySelectorAll('#fleets .fleet h3')].map(e=>e.textContent)")
    check("右の欄は相手の艦が上", heads == ["撃沈した相手の艦", "自分の艦隊"], heads)
    for vw, vh in ((412, 915), (360, 740), (393, 852)):
        pg.set_viewport_size({"width": vw, "height": vh})
        pg.wait_for_timeout(80)
        pg.evaluate("scrollTo(0,0)")
        r = pg.evaluate("""()=>{const f=document.querySelector('#fleets').getBoundingClientRect();
            const a=document.getElementById('acts').getBoundingClientRect();
            const c=document.querySelector('#bigSlot .c').getBoundingClientRect().width;
            return {bottom:Math.round(f.bottom), acts:Math.round(a.top), cell:Math.round(c),
                    wide:document.documentElement.scrollWidth<=innerWidth};}""")
        check("%dx%d：相手の艦の欄が操作帯に隠れない（マス %dpx）" % (vw, vh, r["cell"]),
              r["bottom"] <= r["acts"] and r["wide"] and r["cell"] >= 22, r)
    pg.set_viewport_size({"width": 412, "height": 915})
    pg.wait_for_timeout(80)

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

    print("[過去の対戦（v1.1.0）]")
    final = pg.evaluate("""()=>[1,2].map(id=>{const g=G.grids[id];let s='';for(let y=1;y<=10;y++)for(let x=1;x<=10;x++){
        const sh=g.shipAt(x,y);s+=g.st(x,y)===4?(sh&&g.isSunk(sh)?'S':'H'):g.st(x,y)===3?'m':(sh?'o':'.');}return s;})""")
    total = pg.evaluate("G.shots[1]+G.shots[2]")
    games = pg.evaluate("JSON.parse(localStorage.getItem('battleship_android_games'))")
    check("1局の記録が残る（配置10隻・手順）", len(games) == 1 and len(games[0]["shots"]) == total
          and len(games[0]["ships"]["1"]) == 5 and len(games[0]["ships"]["2"]) == 5, (len(games), total))
    pg.tap("#bSet"); pg.tap("#bHistory"); pg.wait_for_timeout(150)
    check("⚙から一覧が開く（1局）", pg.is_visible("#mReplay") and pg.locator("#rpList li[data-i]").count() == 1)
    pg.tap('#rpList li[data-i="0"]'); pg.wait_for_timeout(150)
    check("0手目は両方の艦が見える", pg.locator("#mReplay .rp-g b.sh").count() == 34)
    pg.tap("[data-rp=last]")
    rp = pg.evaluate("""()=>[1,2].map(id=>{let s='';for(let y=1;y<=10;y++)for(let x=1;x<=10;x++){
        const c=document.getElementById('rp'+id+'_'+x+'_'+y).className;
        s+=c.includes('sk')?'S':c.includes('ht')?'H':c.includes('ms')?'m':c.includes('sh')?'o':'.';}return s;})""")
    check("再生の最後が実際の最後と1マスも違わない", rp == final)
    check("手数の表示", pg.inner_text("#rpCap").startswith("%d / %d" % (total, total)), pg.inner_text("#rpCap"))
    pg.tap("[data-rp=first]"); pg.tap("[data-rp=next]")
    check("1手ずつ進める", pg.inner_text("#rpCap").startswith("1 / "))
    rw = pg.evaluate("document.querySelector('#mReplay .rp').getBoundingClientRect().width")
    check("再生の窓がスマホの幅に収まる", rw <= 412 and pg.evaluate("document.documentElement.scrollWidth<=innerWidth"), rw)
    pg.screenshot(path=str(OUT / "android_replay.png"))
    check("速さの既定は ふつう（1秒）", pg.input_value("#rpSpeed") == "1000")
    pg.select_option("#rpSpeed", "500"); pg.tap("[data-rp=first]"); pg.tap("#rpPlay")
    pg.wait_for_timeout(1300); n1 = pg.evaluate("RP.n")
    check("速め（0.5秒）で1.3秒に2〜3手", 2 <= n1 <= 3, n1)
    pg.select_option("#rpSpeed", "2000"); n2 = pg.evaluate("RP.n"); pg.wait_for_timeout(1300)
    check("再生中に ゆっくり（2秒）へ変えると止まらずに遅くなる", pg.evaluate("RP.n") == n2 and pg.evaluate("!!RP.timer"), (n2, pg.evaluate("RP.n")))
    pg.wait_for_timeout(900)
    check("…2秒たつと1手進む", pg.evaluate("RP.n") == n2 + 1)
    pg.tap("#rpPlay")
    check("選んだ速さを覚える", pg.evaluate("localStorage.getItem('battleship_replay_speed')") == "2000")
    pg.tap("#rpClose")
    check("閉じる", not pg.is_visible("#mReplay"))

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

    print("[ヒント（v1.2.0）]")
    eid = pg.evaluate("aiId()")
    check("既定は切（塗らない）", pg.locator("#grid%d .c.heat" % eid).count() == 0)
    pg.tap("#bSet"); pg.tap("#segHint button[data-v='1']"); pg.tap("#bClose")
    check("⚙で入にすると相手の盤を塗る", pg.locator("#grid%d .c.heat" % eid).count() == 100)
    check("いちばん濃いマスに枠", pg.locator("#grid%d .c.best" % eid).count() >= 1)
    check("自分の盤は塗らない", pg.locator("#grid%d .c.heat" % (3 - eid)).count() == 0)
    bx = pg.evaluate("(()=>{const e=document.querySelector('#grid%d .c.best');return [+e.dataset.x,+e.dataset.y]})()" % eid)
    pg.tap("#c%d_%d_%d" % (eid, bx[0], bx[1]))
    check("狙ったマスは黄色が見える（塗りより上）", "aim" in pg.get_attribute("#c%d_%d_%d" % (eid, bx[0], bx[1]), "class"))
    check("覚える", pg.evaluate("JSON.parse(localStorage.getItem('battleship_android_prefs')).hint") is True)
    pg.screenshot(path=str(OUT / "android_hint.png"))
    pg.tap("#bSet"); pg.tap("#segHint button[data-v='0']"); pg.tap("#bClose")
    check("切にすると消える", pg.locator("#grid%d .c.heat" % eid).count() == 0)
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
    check("過去の対戦が2局（新しい順）", len(pg.evaluate("JSON.parse(localStorage.getItem('battleship_android_games'))")) == 2)
    pg.tap("#bSet")
    pg.tap("#bClear")
    check("戦績を消せる", pg.evaluate("localStorage.getItem('battleship_android_stats')") == "{}")
    check("過去の対戦も消える", pg.evaluate("localStorage.getItem('battleship_android_games')") == "[]")
    games2 = None

    print("[広い画面]")
    pg.set_viewport_size({"width": 1000, "height": 900})
    wd = pg.evaluate("document.getElementById('app').getBoundingClientRect().width")
    check("広い画面では560pxで中央", wd == 560, wd)

    check("画面のエラー 0件", not errs, errs)
    check("読めなかったファイル 0件", not bad, bad)
    b.close()

print("\n%d 項目中 %d 通過%s" % (ok + ng, ok, "" if not ng else "（%d 件 NG）" % ng))
sys.exit(1 if ng else 0)
