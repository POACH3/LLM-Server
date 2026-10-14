// Removes the "Open WebUI" name from the chat page's own text, and names the
// browser tab "Private LLM". The owner's choice (2026-10-14): no replacement
// name in the page, the OI icon kept in the tab only. Open WebUI's license
// allows this for deployments of 50 people or fewer in any 30 days.
//
// llm-start appends this file to the status badge's loader.js (Open WebUI
// loads /static/loader.js on every page). Nothing installed is changed; to
// undo, remove this file and the branding lines in llm-start, then restart.
//
// Only the page's own labels are touched. Chat messages, the chat list and
// anything being typed are skipped, so a conversation that mentions Open
// WebUI is shown exactly as written.
(function () {
  "use strict";

  var NAME = "Open WebUI";
  var TAB_TITLE = "Private LLM";

  // Phrases built around the name, and what they become without it. Checked
  // in order; anything left over loses the name alone.
  var PHRASES = [
    [/ \(Open WebUI\)/g, ""],
    [/\b(Sign(?:ing)? (?:in|up)) to Open WebUI\b/g, "$1"],
    [/\bGet started with Open WebUI\b/g, "Get started"],
    [/\bAbout Open WebUI\b/g, "About"],
    [/\bOpen WebUI /g, ""],
    [/ ?Open WebUI\b/g, ""]
  ];

  // Where people's own words appear: never rewritten.
  var SKIP = "#messages-container, .messages-container, .markdown-prose, .ProseMirror, " +
             "textarea, input, [contenteditable], pre, code, a[href^='/c/']";

  function clean(text) {
    var startedWithName = text.trimStart().indexOf(NAME) === 0;
    for (var i = 0; i < PHRASES.length; i++) {
      text = text.replace(PHRASES[i][0], PHRASES[i][1]);
    }
    // "Open WebUI can query it" becomes "Can query it", not "can query it".
    if (startedWithName) text = text.replace(/^(\s*)(\S)/, function (m, space, first) {
      return space + first.toUpperCase();
    });
    return text;
  }

  function fixNode(node) {
    if (node.nodeType !== 3 || node.nodeValue.indexOf(NAME) < 0) return;
    var parent = node.parentElement;
    if (!parent || parent.closest(SKIP)) return;
    node.nodeValue = clean(node.nodeValue);
  }

  function fixTree(root) {
    if (root.nodeType === 3) return fixNode(root);
    if (root.nodeType !== 1 || root.closest(SKIP)) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) fixNode(node);
    // Labels shown on hover, and image descriptions.
    ["title", "alt", "aria-label", "placeholder"].forEach(function (attr) {
      root.querySelectorAll("[" + attr + "*='" + NAME + "']").forEach(function (el) {
        if (!el.closest(SKIP)) el.setAttribute(attr, clean(el.getAttribute(attr)));
      });
    });
  }

  function fixTitle() {
    // Open WebUI sets "Open WebUI" alone, or "<chat title> • Open WebUI";
    // only the name at the end is replaced, never a chat's own title.
    var title = document.title;
    var fixed = title === NAME || title === "" ? TAB_TITLE
              : title.replace(/ ?\(Open WebUI\)$/, "").replace(/Open WebUI$/, TAB_TITLE);
    if (fixed !== title) document.title = fixed;
  }

  function start() {
    fixTree(document.body);
    fixTitle();
    new MutationObserver(function (changes) {
      changes.forEach(function (change) {
        if (change.type === "characterData") fixNode(change.target);
        change.addedNodes.forEach(fixTree);
      });
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
    new MutationObserver(fixTitle).observe(document.head, { childList: true, subtree: true, characterData: true });
  }

  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start);
})();
