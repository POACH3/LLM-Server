// Status badge for the chat page, at the bottom left of the chat area, to the
// right of the left pane (on a phone, just above the chat box): shows everyone whether the server
// is free, occupied, or reserved by the owner. For the owner it is also a
// switch: clicking it reserves the server or releases it.
//
// Open WebUI loads /static/loader.js on every page and ships it empty for
// additions like this one. llm-start copies this file into place after Open
// WebUI has started (Open WebUI empties that folder at every start).
//
// The state comes from the relay, at the address /llm-status. For everyone
// but the owner the badge only reads it and never blocks a click: taps pass
// straight through. If the state cannot be read (for example at the Mac
// itself, where /llm-status does not exist), the badge stays hidden.
//
// The switch: the badge asks Open WebUI who is signed in on this page. Only
// for an admin does it become clickable. A click sends the request to the
// relay at /llm-reserve together with the page's sign-in token, and the
// relay checks that token with Open WebUI before it changes anything, so
// making the badge clickable by hand gets a guest nowhere.
(function () {
  "use strict";

  var STATUS_ADDRESS = "/llm-status";
  var RESERVE_ADDRESS = "/llm-reserve";
  var WHO_AM_I_ADDRESS = "/api/v1/auths/";  // Open WebUI's "who is signed in"
  var OWNER_ROLE = "admin";
  // How often to ask for the state. Short, so that a brief reply to someone
  // else is still caught as "occupied" before it has finished.
  var CHECK_EVERY_MS = 2000;
  var WHO_AM_I_EVERY_MS = 60000;

  // What each state looks like: the words shown, the dot's colour, and what
  // a click does for the owner.
  var LOOKS = {
    "free":     { text: "server free",              colour: "#22a559", action: "reserve" },
    "in use":   { text: "server occupied",          colour: "#d98a00", action: "reserve" },
    "reserved": { text: "server reserved by owner", colour: "#d64545", action: "release" }
  };

  var state = null;
  var isOwner = false;

  var badge = document.createElement("div");
  var dot = document.createElement("span");
  var label = document.createElement("span");
  var action = document.createElement("span");
  badge.id = "llm-status-badge";
  badge.setAttribute("role", "status");
  badge.style.cssText =
    "position:fixed;bottom:8px;right:8px;z-index:2147483000;" +
    "display:none;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;" +
    "font:600 12px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;" +
    "color:#fff;background:rgba(30,32,38,.82);box-shadow:0 1px 6px rgba(0,0,0,.25);" +
    "pointer-events:none;user-select:none;white-space:nowrap;";
  dot.style.cssText = "width:8px;height:8px;border-radius:50%;display:inline-block;";
  action.style.cssText = "display:none;font-weight:500;opacity:.8;text-decoration:underline;";
  badge.appendChild(dot);
  badge.appendChild(label);
  badge.appendChild(action);

  // On a phone the chat box reaches almost to the bottom of the screen, so
  // there the badge is made smaller and sits just above the chat box, at its
  // left-hand end. "message-input-container" is the name Open WebUI gives
  // the chat box; if it cannot be found, a typical height is used.
  var narrow = window.matchMedia("(max-width: 600px)");
  function fit() {
    if (narrow.matches) {
      var above = 96;
      var box = document.getElementById("message-input-container") ||
                document.getElementById("chat-input-container");
      if (box) {
        var top = box.getBoundingClientRect().top;
        if (top > 60 && top < window.innerHeight) above = Math.round(window.innerHeight - top) + 6;
      }
      badge.style.bottom = above + "px";
      badge.style.right = "auto";
      badge.style.left = "12px";
      badge.style.padding = "1px 8px";
      badge.style.fontSize = "10px";
      dot.style.width = dot.style.height = "6px";
    } else {
      // On a wider screen: the bottom left of the chat area. When the pane
      // on the left is open the badge sits just to the right of it, and when
      // it is closed, in the corner. "sidebar" is Open WebUI's name for it.
      var left = 8;
      var pane = document.getElementById("sidebar");
      if (pane) {
        var edge = pane.getBoundingClientRect();
        var open = edge.width > 0 && edge.right > 0 && edge.left < window.innerWidth;
        if (open && edge.right < window.innerWidth * 0.7) left = Math.round(edge.right) + 8;
      }
      badge.style.bottom = "8px";
      badge.style.right = "auto";
      badge.style.left = left + "px";
      badge.style.padding = "3px 10px";
      badge.style.fontSize = "12px";
      dot.style.width = dot.style.height = "8px";
    }
  }

  function show(newState) {
    var look = LOOKS[newState];
    state = look ? newState : null;
    if (!look) {
      badge.style.display = "none";
      return;
    }
    dot.style.background = look.colour;
    label.textContent = look.text;
    // The owner also sees what a click will do, and can click.
    action.textContent = look.action;
    action.style.display = isOwner ? "inline" : "none";
    badge.style.pointerEvents = isOwner ? "auto" : "none";
    badge.style.cursor = isOwner ? "pointer" : "default";
    badge.style.display = "inline-flex";
  }

  function check() {
    if (document.hidden) return;  // no need to ask while the page is not on screen
    fetch(STATUS_ADDRESS, { cache: "no-store", credentials: "omit" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (answer) { show(answer && answer.state); })
      .catch(function () { show(null); });
  }

  function token() {
    try { return window.localStorage.token || ""; } catch (e) { return ""; }
  }

  // Is the person signed in on this page the owner?
  function whoAmI() {
    if (document.hidden) return;
    var t = token();
    if (!t) { isOwner = false; show(state); return; }
    fetch(WHO_AM_I_ADDRESS, { cache: "no-store", headers: { "Authorization": "Bearer " + t } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (user) { isOwner = !!user && user.role === OWNER_ROLE; show(state); })
      .catch(function () { isOwner = false; show(state); });
  }

  function flip() {
    if (!isOwner || !state) return;
    var reserve = state !== "reserved";
    var question = reserve
      ? "Reserve the server? New messages from other people will be refused until you release it."
      : "Release the server, so other people can use it again?";
    if (!window.confirm(question)) return;
    fetch(RESERVE_ADDRESS, {
      method: "POST", cache: "no-store", credentials: "omit",
      headers: {
        "Content-Type": "application/json",
        "X-LLM-Reserve": "1",
        "Authorization": "Bearer " + token()
      },
      body: JSON.stringify({ on: reserve })
    })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (answer) {
        if (answer && answer.state) show(answer.state);
        else window.alert("That did not work. Check that you are still signed in as the owner.");
      })
      .catch(function () { window.alert("That did not work. The server could not be reached."); });
  }

  function start() {
    document.body.appendChild(badge);
    badge.addEventListener("click", flip);
    fit();
    window.addEventListener("resize", fit);
    setInterval(fit, 300);  // the chat box grows, and the left pane opens and closes
    check();
    whoAmI();
    setInterval(check, CHECK_EVERY_MS);
    setInterval(whoAmI, WHO_AM_I_EVERY_MS);
    document.addEventListener("visibilitychange", function () { check(); whoAmI(); });
  }

  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start);
})();
