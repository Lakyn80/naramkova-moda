// frontend/src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// ✅ cookie lišta + volitelné skripty po souhlasu
import CookieBanner from "./components/CookieBanner";
import { setupOptionalScripts } from "./lib/loaders.js";
setupOptionalScripts();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
    {/* cookie lišta je globálně, mimo router */}
    <CookieBanner />
  </React.StrictMode>
);

/* ===== Emotikony (ASCII) -> Emoji (Unicode) + Selektivní Twemoji parse ===== */

// 1) Mapování běžných ASCII emotikon na Unicode emoji
function emoticonToEmoji(text) {
  const rules = [
    { re: /(:-\)|:\))/g, ch: "🙂" },     // :-) :)
    { re: /(:-\(|:\()/g, ch: "🙁" },     // :-( :(
    { re: /(:-D|:D)/g, ch: "😃" },       // :-D :D
    { re: /(;-\)|;\))/g, ch: "😉" },     // ;-) ;)
    { re: /(:-P|:P|:-p|:p)/g, ch: "😛" },// :-P :P
    { re: /(:-O|:O|:-o|:o)/g, ch: "😮" },// :-O :O
    { re: /(B-\)|B\))/g, ch: "😎" },     // B-) B)
    { re: /(:-\||:\|)/g, ch: "😐" },     // :-| :|
    { re: /(:-\/|:\/)/g, ch: "😕" },     // :-/ :/
    { re: /(:-\*|:\*)/g, ch: "😘" },     // :-* :*
    { re: /(:-x|:x)/g, ch: "😶" },       // :-x :x
    { re: /<3/g, ch: "❤️" },             // <3
  ];
  let out = text;
  for (const { re, ch } of rules) out = out.replace(re, ch);
  return out;
}

// 2) Pomocné funkce – detekce „zakázané“ zóny a převod textových uzlů
function hasNoEmojiAncestor(node) {
  let p = node && node.parentNode;
  while (p) {
    if (p.nodeType === 1 && (p.hasAttribute("data-no-emoji") || p.classList?.contains("no-emoji"))) {
      return true;
    }
    p = p.parentNode;
  }
  return false;
}

function convertEmoticonsInNode(root) {
  if (!root) return;
  const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "PRE", "NOSCRIPT", "KBD", "SAMP", "IMG"]);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !/[;:B<]/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
      if (hasNoEmojiAncestor(node)) return NodeFilter.FILTER_REJECT;
      let p = node.parentNode;
      while (p) {
        if (p.nodeType === 1 && SKIP_TAGS.has(p.tagName)) return NodeFilter.FILTER_REJECT;
        p = p.parentNode;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  let n;
  while ((n = walker.nextNode())) nodes.push(n);
  for (const t of nodes) {
    const replaced = emoticonToEmoji(t.nodeValue);
    if (replaced !== t.nodeValue) t.nodeValue = replaced;
  }
}

// 3) Selektivní Twemoji – zpracuj jen elementy, které nejsou uvnitř [data-no-emoji]
function parseTwemojiSelective(root) {
  if (!window.twemoji || !root) return;
  const parents = new Set();

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue) return NodeFilter.FILTER_REJECT;
      // rychlý test na přítomnost emoji znaků
      if (!/[\u231A-\uD83E\uDDFF\u2600-\u27BF]/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
      if (hasNoEmojiAncestor(node)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });

  let n;
  while ((n = walker.nextNode())) {
    const el = n.parentElement;
    if (el) parents.add(el);
  }

  parents.forEach((el) =>
    window.twemoji.parse(el, {
      folder: "svg",
      ext: ".svg",
      className: "emoji",
    })
  );
}

// 4) Hlavní zpracování
function processEmoji(root = document.body) {
  convertEmoticonsInNode(root);
  parseTwemojiSelective(root);
}

// Po prvním renderu
processEmoji(document.body);

// Sleduj dynamické změny (React navigace, AJAX, atd.)
try {
  if (window.__EMOJI_OBSERVER__) window.__EMOJI_OBSERVER__.disconnect();
  const observer = new MutationObserver((mutations) => {
    const containers = new Set();
    for (const m of mutations) {
      if (m.type === "childList") {
        if (m.target && m.target.nodeType === 1 && !m.target.closest("[data-no-emoji], .no-emoji")) containers.add(m.target);
        for (const node of m.addedNodes) {
          if (node.nodeType === 1 && !node.closest?.("[data-no-emoji], .no-emoji")) containers.add(node);
          else if (node.nodeType === 3 && node.parentNode && !node.parentNode.closest?.("[data-no-emoji], .no-emoji")) {
            containers.add(node.parentNode);
          }
        }
      } else if (m.type === "characterData" && m.target.parentNode && !m.target.parentNode.closest?.("[data-no-emoji], .no-emoji")) {
        containers.add(m.target.parentNode);
      }
    }
    containers.forEach((el) => processEmoji(el));
  });
  observer.observe(document.body, { childList: true, characterData: true, subtree: true });
  window.__EMOJI_OBSERVER__ = observer;
} catch {
  /* noop */
}
