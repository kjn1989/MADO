/* MADO chat widget — JICA HP 組み込み用(第2段階の雛形・依存ライブラリなし)
 *
 * 使い方: ページ末尾に1行追加するだけ。
 *   <script src="https://<MADO_API_HOST>/widget/mado-widget.js"
 *           data-api="https://<MADO_API_HOST>/api/chat" defer></script>
 *
 * 仕様:
 * - 右下にフローティングの窓ボタン → クリックでチャットパネルが開く
 * - /api/chat (SSE) を fetch + ReadableStream で受信:
 *     meta(出典・関連動画) → token(回答断片) → done
 * - ブランド: ディープティール #0E5C63 / アンバー #F4A024 / ライトブルー #DCEFFB
 * - 常時表示クレジット: Powered by JICA official video archive
 */
(function () {
  "use strict";
  var API = (document.currentScript && document.currentScript.dataset.api) || "/api/chat";

  /* ---------- styles ---------- */
  var css = [
    ".mado-w-btn{position:fixed;right:20px;bottom:20px;z-index:99990;width:60px;height:60px;",
    "border-radius:16px;background:#0E5C63;border:none;cursor:pointer;box-shadow:0 6px 20px rgba(14,92,99,.35);",
    "display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:10px;transition:transform .15s}",
    ".mado-w-btn:hover{transform:scale(1.06)}",
    ".mado-w-btn span{background:#DCEFFB;border-radius:4px}",
    ".mado-w-btn span:nth-child(4){background:radial-gradient(circle at 50% 110%,#F4A024 0 60%,#DCEFFB 60%)}",
    ".mado-w-panel{position:fixed;right:20px;bottom:92px;z-index:99991;width:min(380px,calc(100vw - 32px));",
    "height:min(560px,calc(100vh - 130px));background:#FBFDFF;border-radius:18px;overflow:hidden;display:none;",
    "flex-direction:column;box-shadow:0 16px 48px rgba(10,68,74,.3);font-family:'Zen Kaku Gothic New','Hiragino Sans',sans-serif}",
    ".mado-w-panel.open{display:flex}",
    ".mado-w-head{background:#0E5C63;color:#fff;padding:12px 16px}",
    ".mado-w-head b{font-size:17px;letter-spacing:.12em}",
    ".mado-w-head b i{color:#F4A024;font-style:normal}",
    ".mado-w-head small{display:block;font-size:10px;opacity:.85;margin-top:2px}",
    ".mado-w-log{flex:1;overflow-y:auto;padding:12px;font-size:13px;line-height:1.7;color:#12343B}",
    ".mado-w-msg{margin-bottom:10px;padding:9px 12px;border-radius:12px;max-width:88%;white-space:pre-wrap;word-break:break-word}",
    ".mado-w-msg.user{background:#F4A024;color:#fff;margin-left:auto}",
    ".mado-w-msg.bot{background:#DCEFFB}",
    ".mado-w-src{display:flex;gap:8px;align-items:center;background:#fff;border:1px solid #DCEFFB;",
    "border-radius:10px;padding:6px;margin:6px 0;text-decoration:none;color:#12343B}",
    ".mado-w-src img{width:84px;border-radius:6px;flex:none}",
    ".mado-w-src div{font-size:11px;line-height:1.5}",
    ".mado-w-src b{display:block;font-size:11.5px;color:#0E5C63}",
    ".mado-w-form{display:flex;gap:8px;padding:10px;border-top:1px solid #DCEFFB;background:#fff}",
    ".mado-w-form input{flex:1;border:1.5px solid #DCEFFB;border-radius:999px;padding:9px 14px;font-size:13px;outline-color:#F4A024}",
    ".mado-w-form button{background:#0E5C63;color:#fff;border:none;border-radius:999px;padding:0 16px;cursor:pointer;font-weight:700}",
    ".mado-w-credit{font-size:9.5px;text-align:center;color:#0E5C63;background:#DCEFFB;padding:4px}",
  ].join("");
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  /* ---------- DOM ---------- */
  var btn = document.createElement("button");
  btn.className = "mado-w-btn";
  btn.setAttribute("aria-label", "MADOチャットを開く");
  btn.innerHTML = "<span></span><span></span><span></span><span></span>";

  var panel = document.createElement("div");
  panel.className = "mado-w-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "MADO チャット");
  panel.innerHTML =
    '<div class="mado-w-head"><b>MAD<i>O</i></b>' +
    "<small>Meet AI, Discover Opportunities — 世界の“知らなかった”に出会う窓</small></div>" +
    '<div class="mado-w-log" aria-live="polite"></div>' +
    '<form class="mado-w-form"><input type="text" placeholder="JICAの動画アーカイブに質問する" aria-label="質問">' +
    "<button type=\"submit\">送信</button></form>" +
    '<div class="mado-w-credit">Powered by JICA official video archive</div>';

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var log = panel.querySelector(".mado-w-log");
  var form = panel.querySelector("form");
  var input = panel.querySelector("input");

  btn.addEventListener("click", function () {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) input.focus();
  });

  function add(cls, text) {
    var d = document.createElement("div");
    d.className = "mado-w-msg " + cls;
    d.textContent = text || "";
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  }

  function addSources(meta) {
    (meta.sources || []).forEach(function (s) {
      var a = document.createElement("a");
      a.className = "mado-w-src";
      a.href = s.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML =
        '<img alt="" loading="lazy"><div><b></b><span></span></div>';
      a.querySelector("img").src = s.thumbnail;
      a.querySelector("b").textContent = s.title;
      a.querySelector("span").textContent =
        s.channel + (s.timestamp_label ? " ・ ▶ " + s.timestamp_label : "");
      log.appendChild(a);
    });
    log.scrollTop = log.scrollHeight;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    add("user", q);
    var bot = add("bot", "");

    fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, lang: "auto" }),
    })
      .then(function (res) {
        var reader = res.body.getReader();
        var dec = new TextDecoder();
        var buf = "";
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) return;
            buf += dec.decode(r.value, { stream: true });
            var blocks = buf.split("\n\n");
            buf = blocks.pop();
            blocks.forEach(function (block) {
              var ev = (block.match(/^event: (.+)$/m) || [])[1];
              var dm = block.match(/^data: (.+)$/m);
              if (!ev || !dm) return;
              var data = JSON.parse(dm[1]);
              if (ev === "token") {
                bot.textContent += data;
                log.scrollTop = log.scrollHeight;
              } else if (ev === "meta" && data.found) {
                addSources(data);
              }
            });
            return pump();
          });
        }
        return pump();
      })
      .catch(function () {
        bot.textContent = "接続エラーが発生しました。時間をおいて再度お試しください。";
      });
  });
})();
