// src/utils/emojify.js
// Převod běžných emotikon na emoji (bez kolize s URL apod.).
export function emojify(input) {
  if (input == null) return "";
  let text = String(input);

  const rules = [
    { re: /(^|[\s(])(:-?\))/g, to: "$1🙂" },   // :) :-)
    { re: /(^|[\s(])(:-?\()/g, to: "$1🙁" },   // :( :-(
    { re: /(^|[\s(])(:-?D)/g,  to: "$1😃" },   // :D :-D
    { re: /(^|[\s(]);-?\)/g,   to: "$1😉" },   // ;) ;-)
    { re: /(^|[\s(])(:-?p)/gi, to: "$1😛" },   // :P :-P
    { re: /(^|[\s(])(:-?[oO])/g, to: "$1😮" }, // :O :-O
    { re: /(^|[\s(])(:-?\*)/g, to: "$1😘" },   // :* :-*
    { re: /(^|[\s(]):'\(/g,   to: "$1😢" },   // :'(
    { re: /(^|[\s(])(8-?\))/g, to: "$1😎" },  // 8) 8-)
    { re: /<3/g,               to: "❤️" }     // <3
    // Záměrně neřešíme ":/" kvůli http(s)://
  ];

  for (const r of rules) text = text.replace(r.re, r.to);
  return text;
}
