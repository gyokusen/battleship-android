/* バトルシップ スマホ版 — オフラインでも動くようにするための入れ物。
   版を上げたいときは CACHE の名前だけ変える（例 bsa-v1 → bsa-v2）。
   古い入れ物は activate のときに片づける。

   ★ 名前は作業時間管理（wta-*）・英単語例文暗記（eiw-*）と別にしてある。
     同じ gyokusen.github.io に置くので、名前がぶつかると片方の更新でもう片方の控えが消える。 */
const CACHE = "bsa-v1";
const FILES = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon/icon-192.png",
  "./icon/icon-512.png",
  "./icon/icon-maskable-512.png",
  "./images/Battleship.gif",
  "./images/Battleship32H.gif", "./images/Battleship32V.gif",
  "./images/Carrier32H.gif",    "./images/Carrier32V.gif",
  "./images/Cruiser32H.gif",    "./images/Cruiser32V.gif",
  "./images/Destroyer32H.gif",  "./images/Destroyer32V.gif",
  "./images/Submarine32H.gif",  "./images/Submarine32V.gif",
  "./images/Hit.gif", "./images/Miss.gif",
  "./images/hit.png", "./images/miss.png", "./images/sunk.png",
  "./images/warship.jpg"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* 画面のファイルは「まず取りに行って、だめなら控えを出す」（英単語例文暗記と同じ）。
   GitHub Pages は HTML を10分キャッシュさせるので、画面そのものは no-store で毎回聞きに行く。 */
function isDoc(req) {
  return req.mode === "navigate" || req.destination === "document";
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const go = isDoc(req) ? fetch(req.url, {cache: "no-store"}) : fetch(req);
  e.respondWith(
    go
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(req).then((r) => r || caches.match("./index.html")))
  );
});
