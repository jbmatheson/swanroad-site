/* Swan Road: today's puzzle, played in the browser.

   The rules here are the standard 7×7 game as SwanroadKit's Game.swift plays it, and the day's puzzle is chosen the
   way the app's PuzzleStore.daily(on:) chooses it, so the page and the app show the same puzzle on the same day.
   tools/check_daily.py replays every puzzle in the book through these rules and compares each move with the
   simulator; run it whenever this file or the book changes.

   The page plays today's puzzle and nothing else: no archive, no hints, no streak. Those are the app's. */
(function (root) {
  "use strict";

  // ---- The rules ----

  var N = 7, SIZE = N * N, RANGE = 3, NO_DRIFT_TURNS = 4, TIDE = [[40, 1], [50, 2]];
  var EMPTY = 0, ORB = 1, LIGHT = 2, DARK = 3;

  /** Rows within this many of a shore row count as shore on the given turn. */
  function tideDepth(turn) {
    var depth = 0;
    for (var i = 0; i < TIDE.length; i++) if (turn >= TIDE[i][0] && TIDE[i][1] > depth) depth = TIDE[i][1];
    return depth;
  }

  /** The simulators' text form: P12 places, S3-10 steps, L5 lifts. */
  function parse(token) {
    var kind = token.charAt(0), body = token.slice(1), m;
    if (kind === "P" && /^\d+$/.test(body)) return { kind: "P", to: +body };
    if (kind === "L" && /^\d+$/.test(body)) return { kind: "L", from: +body };
    if (kind === "S" && (m = /^(\d+)-(\d+)$/.exec(body))) return { kind: "S", from: +m[1], to: +m[2] };
    return null;
  }

  function tokenOf(a) {
    return a.kind === "P" ? "P" + a.to : a.kind === "L" ? "L" + a.from : "S" + a.from + "-" + a.to;
  }

  function stateOf(p) {
    return { cells: p.cells.split("").map(Number), supply: p.supply.slice(), score: p.score.slice(), toMove: p.toMove, turn: p.turn };
  }

  function copy(s) {
    return { cells: s.cells.slice(), supply: s.supply.slice(), score: s.score.slice(), toMove: s.toMove, turn: s.turn };
  }

  /** Every move the board allows, as tokens. */
  function legal(s) {
    var mine = LIGHT + s.toMove, out = [], i, dr, dc;
    if (s.supply[s.toMove] > 0) {
      for (i = 0; i < SIZE; i++) if (s.cells[i] === EMPTY) out.push("P" + i);
    }
    for (i = 0; i < SIZE; i++) {
      if (s.cells[i] !== mine) continue;
      var row = Math.floor(i / N), col = i % N;
      for (dr = -1; dr <= 1; dr++) {
        for (dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          var rr = row + dr, cc = col + dc;
          if (rr < 0 || rr >= N || cc < 0 || cc >= N) continue;
          if (s.cells[rr * N + cc] === EMPTY) out.push("S" + i + "-" + (rr * N + cc));
        }
      }
      out.push("L" + i);
    }
    return out;
  }

  /** The position right after a move, before the drift and before the turn passes. */
  function played(s, a) {
    var t = copy(s), p = s.toMove;
    if (a.kind === "P") {
      t.cells[a.to] = LIGHT + p;
      t.supply[p] -= 1;
    } else if (a.kind === "S") {
      t.cells[a.to] = t.cells[a.from];
      t.cells[a.from] = EMPTY;
    } else {
      t.cells[a.from] = EMPTY;
      t.supply[p] += 1;
    }
    return t;
  }

  /** The four pulls (up, down, left, right) on the pearl at i. The nearest anchor in each direction pulls 3, 2 or 1
      by its distance; a pearl in between blocks it. Both sides' anchors pull alike. */
  function pulls(cells, i) {
    var row = Math.floor(i / N), col = i % N, pull = [0, 0, 0, 0];
    var dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    for (var d = 0; d < 4; d++) {
      for (var k = 1; k <= RANGE; k++) {
        var rr = row + dirs[d][0] * k, cc = col + dirs[d][1] * k;
        if (rr < 0 || rr >= N || cc < 0 || cc >= N) break;
        var v = cells[rr * N + cc];
        if (v === EMPTY) continue;
        if (v === LIGHT || v === DARK) pull[d] = RANGE + 1 - k;
        break;
      }
    }
    return pull;
  }

  /** Where each pearl heads, with cancellations: a pearl stays if another pearl started on its square or two head
      for the same one. Pearls with no net pull are left out. */
  function orbMoves(cells) {
    var isStart = [], destCount = [], intents = [], i;
    for (i = 0; i < SIZE; i++) { isStart.push(false); destCount.push(0); }
    for (i = 0; i < SIZE; i++) {
      if (cells[i] !== ORB) continue;
      isStart[i] = true;
      var row = Math.floor(i / N), col = i % N, pull = pulls(cells, i);
      var vert = pull[0] - pull[1], horiz = pull[3] - pull[2], dest = -1;
      if (Math.abs(vert) > Math.abs(horiz)) dest = (row + (vert > 0 ? -1 : 1)) * N + col;
      else if (Math.abs(horiz) > Math.abs(vert)) dest = row * N + col + (horiz > 0 ? 1 : -1);
      if (dest >= 0) { intents.push({ from: i, to: dest }); destCount[dest] += 1; }
    }
    return intents.map(function (m) {
      return { from: m.from, to: m.to, moves: !isStart[m.to] && destCount[m.to] === 1 };
    });
  }

  function collect(t, depth) {
    for (var i = 0; i < SIZE; i++) {
      if (t.cells[i] !== ORB) continue;
      var row = Math.floor(i / N);
      if (row <= depth) { t.cells[i] = EMPTY; t.score[0] += 1; }
      else if (row + depth >= N - 1) { t.cells[i] = EMPTY; t.score[1] += 1; }
    }
  }

  /** Plays a move: the anchor, the drift, the pearls that reach a shore. `drift` lists the pearls that moved. */
  function apply(s, a) {
    var t = played(s, a), moves = [];
    if (s.turn >= NO_DRIFT_TURNS) {
      moves = orbMoves(t.cells).filter(function (m) { return m.moves; });
      moves.forEach(function (m) { t.cells[m.from] = EMPTY; });
      moves.forEach(function (m) {
        // A pearl that drifts onto an anchor sends it back to its owner's hand.
        if (t.cells[m.to] === LIGHT) t.supply[0] += 1;
        else if (t.cells[m.to] === DARK) t.supply[1] += 1;
        t.cells[m.to] = ORB;
      });
      collect(t, tideDepth(s.turn));
    }
    // The tide rises as the turn ends: a pearl already on a new shore row is collected before anyone moves again.
    if (tideDepth(s.turn + 1) > tideDepth(s.turn)) collect(t, tideDepth(s.turn + 1));
    t.turn = s.turn + 1;
    t.toMove = t.turn % 2;
    return { state: t, drift: moves };
  }

  /** Replays a puzzle's whole solution through the rules, as the app does before it lists a puzzle. */
  function isSound(p) {
    function check(s, node) {
      var keys = Object.keys(node);
      for (var k = 0; k < keys.length; k++) {
        var a = parse(keys[k]), child = node[keys[k]];
        if (!a || legal(s).indexOf(keys[k]) < 0) return false;
        var after = apply(s, a).state, collected = after.score[p.toMove] > s.score[p.toMove];
        if (!child) {
          if (!collected) return false;
          continue;
        }
        var reply = parse(child.reply);
        if (collected || !reply || legal(after).indexOf(child.reply) < 0) return false;
        var next = apply(after, reply).state;
        if (next.score[p.toMove] > after.score[p.toMove]) return false;
        if (!check(next, child.then)) return false;
      }
      return keys.length > 0;
    }
    return check(stateOf(p), p.tree);
  }

  // ---- Which puzzle is today's ----

  /** The first day the daily puzzle mixes the lengths; the app's PuzzleStore.firstMixedDay. */
  var FIRST_MIXED_DAY = 20746;

  /** Days since 1970 in the visitor's time zone, so the day turns over at local midnight, as in the app. */
  function dayNumber(date) {
    return Math.floor((date.getTime() / 1000 - date.getTimezoneOffset() * 60) / 86400);
  }

  function gcd(a, b) { return b === 0 ? a : gcd(b, a % b); }

  /** The position in the book of the puzzle for a day: the same walk as the app's PuzzleStore.daily(on:). */
  function dailyIndex(day, count) {
    if (day < FIRST_MIXED_DAY) return ((day % count) + count) % count;
    var step = 29;
    while (gcd(step, count) !== 1) step += 1;
    return ((day - FIRST_MIXED_DAY) * step) % count;
  }

  // ---- Who is sent to the app ----

  /** On an iPhone or iPad, the page plays this many daily puzzles in one browser; after that it shows the day's
      position and sends the visitor to the app, where the daily puzzle is free. 0 turns the limit off.
      Other devices cannot install the app, so they are never limited. */
  var WEB_DAYS_ON_IOS = 3;

  /** `memory` maps a solved day's number to the wrong tries it took. */
  function isGated(memory, today, onIOS) {
    if (!onIOS || WEB_DAYS_ON_IOS <= 0 || Object.prototype.hasOwnProperty.call(memory, today)) return false;
    return Object.keys(memory).length >= WEB_DAYS_ON_IOS;
  }

  function isIOS(nav) {
    return /iPhone|iPad|iPod/.test(nav.userAgent || "") || (nav.platform === "MacIntel" && nav.maxTouchPoints > 1);
  }

  // ---- Where the visitor came from ----

  /** A link to this page can say where it was posted, as /daily/?from=hn. The App Store link then carries that name
      as its campaign in place of the page's own, so the install is counted for the post. The name is lower-case
      letters, digits and hyphens, 30 at most; anything else is ignored, and so is a link with no campaign in it. */
  function withSource(href, search) {
    var from = /[?&]from=([a-z0-9-]{1,30})(?=&|$)/.exec(search || "");
    if (!from || !/[?&]ct=[^&]*/.test(href)) return href;
    return href.replace(/([?&]ct=)[^&]*/, "$1" + from[1]);
  }

  // ---- The page ----

  var NAMES = ["Light", "Dark"];
  var ANCHOR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="5.2" r="2"/><path d="M12 7.2V20M8.4 10.6h7.2M5 13a7 7 0 0 0 14 0"/></svg>';

  function square(i) { return "row " + (Math.floor(i / N) + 1) + ", column " + (i % N + 1); }

  /** The position as rows of emoji, the way the app pastes a board into a chat. */
  function grid(s) {
    var depth = tideDepth(s.turn), rows = [];
    for (var r = 0; r < N; r++) {
      var row = "";
      for (var c = 0; c < N; c++) {
        var v = s.cells[r * N + c];
        row += v === ORB ? "⚪" : v === LIGHT ? "🔶" : v === DARK ? "🔷" : (r <= depth ? "🟨" : r >= N - 1 - depth ? "⬛" : "🟦");
      }
      rows.push(row);
    }
    return rows.join("\n");
  }

  function start() {
    var doc = root.document;
    function $(id) { return doc.getElementById(id); }
    var data = $("book"), game = $("game"), board = $("board");
    if (!data || !game || !board) return;
    var book;
    try { book = JSON.parse(data.textContent); } catch (e) { return; }
    if (!book || !book.puzzles || !book.puzzles.length) return;

    var now = new Date(), today = dayNumber(now);
    var puzzle = book.puzzles[dailyIndex(today, book.puzzles.length)];
    var seat = puzzle.toMove, other = 1 - seat, mine = LIGHT + seat;
    var first = stateOf(puzzle);
    var reduced = !!(root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches);
    var T = reduced ? { place: 80, drift: 80, settle: 80, reply: 350, hold: 1600 }
                    : { place: 380, drift: 540, settle: 320, reply: 450, hold: 1500 };
    var dateText = now.toLocaleDateString("en-GB", { day: "numeric", month: "long" });
    var moves = puzzle.n === 1 ? "one move" : puzzle.n + " moves";
    var brief = NAMES[seat] + " to move. Force a pearl onto " + NAMES[seat] + "’s shore within " + moves + ", whatever " + NAMES[other] + " does."
      + (tideDepth(first.turn) > 0 ? " The tide has risen: each shore is " + (tideDepth(first.turn) + 1) + " rows deep." : "");

    // What this browser remembers: the days solved here and the wrong tries each took. Nothing is sent anywhere.
    var KEY = "swanroad.daily";
    var memory = {};
    try {
      var kept = JSON.parse(root.localStorage.getItem(KEY) || "{}");
      if (kept && typeof kept === "object") {
        Object.keys(kept).forEach(function (d) { if (/^\d+$/.test(d) && typeof kept[d] === "number") memory[d] = kept[d]; });
      }
    } catch (e) { /* private windows and blocked storage: the page plays without it */ }
    function remember() {
      var days = Object.keys(memory).sort(function (a, b) { return b - a; }).slice(0, 30), out = {};
      days.forEach(function (d) { out[d] = memory[d]; });
      memory = out;
      try { root.localStorage.setItem(KEY, JSON.stringify(memory)); } catch (e) { /* as above */ }
    }
    var solvedToday = Object.prototype.hasOwnProperty.call(memory, today);
    var gated = isGated(memory, today, isIOS(root.navigator));

    var state = copy(first), node = puzzle.tree, done = 0, tries = 0;
    var selection = -1, pending = null, pendingSince = 0, refused = -1, busy = false, run = 0;
    var phase = gated ? "gated" : solvedToday ? "solved" : "playing";

    var status = $("status"), log = $("log"), stuck = $("stuck"), after = $("after"), afterText = $("after-text");
    var resetBtn = $("reset"), liftBtn = $("lift"), cancelBtn = $("cancel"), confirmBtn = $("confirm"), shareBtn = $("share");

    // The board: 49 buttons under a layer of pieces, so pearls and anchors can slide.
    board.textContent = "";
    var cells = [], pieces = [];
    for (var i = 0; i < SIZE; i++) {
      var b = doc.createElement("button");
      b.type = "button";
      b.setAttribute("data-i", i);
      b.tabIndex = i === 0 ? 0 : -1;
      board.appendChild(b);
      cells.push(b);
    }
    var layer = doc.createElement("div");
    layer.className = "pieces";
    layer.setAttribute("aria-hidden", "true");
    board.appendChild(layer);

    function put(el, cell) {
      el.style.setProperty("--r", Math.floor(cell / N));
      el.style.setProperty("--c", cell % N);
    }
    function makePiece(kind, cell, extra) {
      var el = doc.createElement("div");
      el.className = "piece " + (kind === ORB ? "pearl" : kind === LIGHT ? "anchor light" : "anchor dark") + (extra ? " " + extra : "");
      el.innerHTML = kind === ORB ? '<span class="orb"></span>' : '<span class="tile">' + ANCHOR + "</span>";
      put(el, cell);
      layer.appendChild(el);
      return el;
    }
    function setBoard(list) {
      layer.textContent = "";
      pieces = [];
      for (var c = 0; c < SIZE; c++) if (list[c] !== EMPTY) pieces.push({ el: makePiece(list[c], c), kind: list[c], cell: c });
    }
    function pieceAt(cell, pearl) {
      for (var k = 0; k < pieces.length; k++) if (pieces[k].cell === cell && (pieces[k].kind === ORB) === pearl) return pieces[k];
      return null;
    }
    function fade(p) {
      if (!p) return;
      pieces.splice(pieces.indexOf(p), 1);
      p.el.classList.add("gone");
      root.setTimeout(function () { if (p.el.parentNode) p.el.parentNode.removeChild(p.el); }, 320);
    }
    function sleep(ms) { return new Promise(function (ok) { root.setTimeout(ok, ms); }); }

    /** Shows a move: the anchor first, then the pearls sliding, then the ones that reached a shore leaving. */
    function animate(before, a, res) {
      var id = run, kind = LIGHT + before.toMove;
      if (a.kind === "P") pieces.push({ el: makePiece(kind, a.to, "arriving"), kind: kind, cell: a.to });
      else if (a.kind === "S") { var p = pieceAt(a.from, false); if (p) { p.cell = a.to; put(p.el, a.to); } }
      else fade(pieceAt(a.from, false));
      return sleep(T.place).then(function () {
        if (id !== run) return;
        var pairs = res.drift.map(function (m) { return { pearl: pieceAt(m.from, true), bumped: pieceAt(m.to, false), to: m.to }; });
        pairs.forEach(function (x) {
          if (x.pearl) { x.pearl.cell = x.to; put(x.pearl.el, x.to); }
          fade(x.bumped);
        });
        return sleep(res.drift.length ? T.drift : 0);
      }).then(function () {
        if (id !== run) return;
        pieces.slice().forEach(function (p) { if (p.kind === ORB && res.state.cells[p.cell] !== ORB) fade(p); });
        return sleep(T.settle);
      }).then(function () {
        if (id === run) setBoard(res.state.cells);
      });
    }

    function say(text, tone) {
      status.textContent = text;
      status.className = "status" + (tone ? " " + tone : "");
    }

    /** One sentence per move for screen readers: what was played, where the pearls went, who collected. */
    function narrate(who, a, before, res) {
      var s = NAMES[who] + (a.kind === "P" ? " places an anchor at " + square(a.to)
        : a.kind === "S" ? " steps an anchor from " + square(a.from) + " to " + square(a.to)
        : " lifts the anchor at " + square(a.from)) + ".";
      if (!res.drift.length) s += " No pearl moves.";
      var placed = played(before, a).cells;
      res.drift.forEach(function (m) {
        s += " A pearl drifts from " + square(m.from) + " to " + square(m.to);
        if (placed[m.to] === LIGHT || placed[m.to] === DARK) s += ", and the anchor there goes back to " + NAMES[placed[m.to] - LIGHT] + "’s hand";
        s += ".";
      });
      for (var p = 0; p < 2; p++) {
        var got = res.state.score[p] - before.score[p];
        if (got > 0) s += " " + NAMES[p] + " collects " + (got === 1 ? "a pearl" : got + " pearls") + ".";
      }
      log.textContent = s;
    }

    function pendingSquare() { return !pending ? -1 : pending.kind === "L" ? pending.from : pending.to; }

    function bar(p) {
      var pearls = "";
      for (var k = 0; k < 3; k++) pearls += '<span class="' + (k < state.score[p] ? "got" : "") + '"></span>';
      $("bar" + p).innerHTML = '<span class="who"><span class="chip ' + (p === 0 ? "light" : "dark") + '">' + ANCHOR + "</span>" + NAMES[p]
        + (p === seat ? ' <span class="you">You</span>' : "") + "</span>"
        + '<span class="count">' + state.supply[p] + " in hand</span>"
        + '<span class="pearls" role="img" aria-label="' + state.score[p] + ' of 3 pearls collected">' + pearls + "</span>";
    }

    function paint() {
      var depth = tideDepth(state.turn), ps = pendingSquare();
      for (var c = 0; c < SIZE; c++) {
        var r = Math.floor(c / N), v = state.cells[c];
        var shore = r <= depth ? 0 : r >= N - 1 - depth ? 1 : -1;
        cells[c].className = "cell " + (shore === 0 ? "shore-light" : shore === 1 ? "shore-dark" : (r + c % N) % 2 === 0 ? "sea alt" : "sea")
          + (selection === c ? " selected" : "") + (ps === c ? " pending" : "") + (refused === c ? " refused" : "");
        var what = v === ORB ? "pearl" : v === LIGHT ? "Light anchor" : v === DARK ? "Dark anchor" : "empty";
        if (ps === c && pending.kind !== "L") what = "your anchor would land here";
        else if (ps === c) what += ", to be lifted";
        else if (selection === c) what += ", selected";
        cells[c].setAttribute("aria-label", square(c) + ": " + what + (shore >= 0 ? ", " + NAMES[shore] + "’s shore" : ""));
      }
      var ghosts = layer.querySelectorAll(".ghost");
      for (var g = 0; g < ghosts.length; g++) layer.removeChild(ghosts[g]);
      pieces.forEach(function (p) {
        p.el.classList.toggle("leaving", !!pending && pending.kind !== "P" && p.kind !== ORB && p.cell === pending.from);
      });
      if (pending && pending.kind !== "L") makePiece(mine, pending.to, "ghost");
      bar(0);
      bar(1);
      var playing = phase === "playing";
      $("controls").hidden = phase === "gated";
      liftBtn.hidden = cancelBtn.hidden = confirmBtn.hidden = !playing;
      liftBtn.disabled = busy || selection < 0 || (!!pending && pending.kind === "L");
      cancelBtn.disabled = busy || (!pending && selection < 0);
      confirmBtn.disabled = busy || !pending;
      resetBtn.textContent = phase === "solved" ? "Play it again" : "Reset";
      stuck.hidden = !(playing && tries >= 3);
      after.hidden = playing;
      shareBtn.hidden = !Object.prototype.hasOwnProperty.call(memory, today);
      board.classList.toggle("still", !playing);
    }

    function neighbours(a, b) {
      return a !== b && Math.abs(Math.floor(a / N) - Math.floor(b / N)) <= 1 && Math.abs(a % N - b % N) <= 1;
    }

    function tap(c) {
      if (busy || phase !== "playing") return;
      if (pending && c === pendingSquare()) {
        // A second tap on the move's square confirms it, as in the app; a double tap is one tap.
        if (Date.now() - pendingSince > 350) confirm();
        return;
      }
      pending = null;
      refused = -1;
      var v = state.cells[c];
      if (v === EMPTY) {
        if (selection >= 0 && neighbours(selection, c)) pending = { kind: "S", from: selection, to: c };
        else if (state.supply[seat] > 0) { selection = -1; pending = { kind: "P", to: c }; }
        else say(NAMES[seat] + " has no anchors in hand. Tap one of " + NAMES[seat] + "’s anchors to step it or lift it.");
      } else if (v === mine) {
        selection = selection === c ? -1 : c;
        if (selection >= 0) say("Tap a square next to the anchor to step there, or Lift to take it back in hand.");
        else say(brief);
      }
      if (pending) {
        pendingSince = Date.now();
        say("Confirm, or tap the square again. Tap another square to change the move.");
      }
      paint();
    }

    function lift() {
      if (busy || phase !== "playing" || selection < 0) return;
      pending = { kind: "L", from: selection };
      pendingSince = Date.now();
      say("Confirm to lift the anchor back into " + NAMES[seat] + "’s hand.");
      paint();
    }

    function cancel() {
      if (busy || phase !== "playing") return;
      pending = null;
      selection = -1;
      say(brief);
      paint();
    }

    function confirm() {
      if (busy || phase !== "playing" || !pending) return;
      var a = pending, token = tokenOf(a), before = state, res = apply(before, a), left = puzzle.n - done;
      pending = null;
      selection = -1;
      refused = -1;
      busy = true;
      var id = ++run;

      if (!Object.prototype.hasOwnProperty.call(node, token)) {
        // Not a winning move. The page plays it anyway so the drift can be seen, then takes it back.
        tries += 1;
        var home = res.state.score[seat] > before.score[seat];
        say("Not that one. " + (home ? "" : left <= 1 ? "No pearl comes home this turn."
          : "That does not force a pearl home within " + left + " moves."), "wrong");
        refused = a.kind === "L" ? a.from : a.to;
        if (!reduced) {
          board.classList.remove("jolt");
          void board.offsetWidth;
          board.classList.add("jolt");
        }
        paint();
        if (home) {
          busy = false;
          paint();
          return;
        }
        narrate(seat, a, before, res);
        animate(before, a, res).then(function () { return sleep(T.hold); }).then(function () {
          if (id !== run) return;
          setBoard(before.cells);
          refused = -1;
          busy = false;
          paint();
        });
        return;
      }

      var child = node[token];
      paint();
      narrate(seat, a, before, res);
      animate(before, a, res).then(function () {
        if (id !== run) return;
        state = res.state;
        done += 1;
        if (!child) {
          solved();
          return;
        }
        say("Good. " + NAMES[other] + " answers; keep going.");
        paint();
        return sleep(T.reply).then(function () {
          if (id !== run) return;
          var reply = parse(child.reply), mid = state, out = apply(mid, reply);
          narrate(other, reply, mid, out);
          return animate(mid, reply, out).then(function () {
            if (id !== run) return;
            state = out.state;
            node = child.then;
            busy = false;
            var togo = puzzle.n - done;
            say(NAMES[seat] + " to move. " + (togo === 1 ? "One move left." : togo + " moves left."));
            paint();
          });
        });
      });
    }

    function result() {
      var t = memory[today];
      return t === 0 ? "first try" : "in " + (t + 1) + " tries";
    }

    function solved() {
      busy = false;
      phase = "solved";
      if (!Object.prototype.hasOwnProperty.call(memory, today)) {
        memory[today] = tries;
        remember();
      }
      say("Solved, " + result() + ". The pearl is home.", "solved");
      paint();
    }

    function reset() {
      if (phase === "gated") return;
      run += 1;
      state = copy(first);
      node = puzzle.tree;
      done = 0;
      selection = -1;
      pending = null;
      refused = -1;
      busy = false;
      phase = "playing";
      setBoard(state.cells);
      say(brief);
      log.textContent = "";
      paint();
    }

    function share() {
      var text = "Swan Road puzzle, " + dateText + ": collect in " + puzzle.n + ", " + NAMES[seat] + " to move. Solved " + result() + ".\n"
        + grid(first) + "\nhttps://swanroad.app/daily";
      function copied() {
        shareBtn.textContent = "Copied";
        root.setTimeout(function () { shareBtn.textContent = "Share your result"; }, 1800);
      }
      function toClipboard() {
        if (root.navigator.clipboard && root.navigator.clipboard.writeText) root.navigator.clipboard.writeText(text).then(copied, function () {});
      }
      if (root.navigator.share) {
        root.navigator.share({ text: text }).catch(function (e) { if (!e || e.name !== "AbortError") toClipboard(); });
      } else toClipboard();
    }

    board.onclick = function (e) {
      var t = e.target;
      while (t && t !== board && !(t.getAttribute && t.getAttribute("data-i") !== null)) t = t.parentNode;
      if (t && t !== board) tap(+t.getAttribute("data-i"));
    };
    board.onkeydown = function (e) {
      var t = e.target;
      if (!t.getAttribute || t.getAttribute("data-i") === null) return;
      var c = +t.getAttribute("data-i"), r = Math.floor(c / N), col = c % N;
      if (e.key === "ArrowUp") r -= 1;
      else if (e.key === "ArrowDown") r += 1;
      else if (e.key === "ArrowLeft") col -= 1;
      else if (e.key === "ArrowRight") col += 1;
      else return;
      e.preventDefault();
      if (r < 0 || r >= N || col < 0 || col >= N) return;
      cells[c].tabIndex = -1;
      cells[r * N + col].tabIndex = 0;
      cells[r * N + col].focus();
    };
    resetBtn.onclick = reset;
    liftBtn.onclick = lift;
    cancelBtn.onclick = cancel;
    confirmBtn.onclick = confirm;
    shareBtn.onclick = share;

    var store = doc.querySelector('main a.btn[href*="apps.apple.com"]');
    if (store) store.setAttribute("href", withSource(store.getAttribute("href"), root.location.search));

    $("sub").textContent = dateText + " · Collect in " + puzzle.n + " · " + NAMES[seat] + " to move";
    setBoard(state.cells);
    if (phase === "gated") {
      var n = Object.keys(memory).length;
      say("You have solved " + n + " daily puzzles in this browser. Today’s is waiting in the app, where it is free.");
      afterText.textContent = "The app sets this puzzle every day, with a hint when you want one and a streak to keep. It is free, with no ads and no account.";
    } else if (phase === "solved") {
      say("You solved today’s puzzle " + result() + ". A new one arrives at midnight.", "solved");
    } else {
      say(brief);
    }
    paint();
    $("fallback").hidden = true;
    game.hidden = false;
  }

  var api = {
    N: N, tideDepth: tideDepth, parse: parse, tokenOf: tokenOf, stateOf: stateOf, legal: legal, played: played, pulls: pulls,
    orbMoves: orbMoves, apply: apply, isSound: isSound, dayNumber: dayNumber, dailyIndex: dailyIndex, isGated: isGated,
    isIOS: isIOS, grid: grid, withSource: withSource, start: start, FIRST_MIXED_DAY: FIRST_MIXED_DAY, WEB_DAYS_ON_IOS: WEB_DAYS_ON_IOS
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.SwanRoadPuzzle = api;

  if (root.document) {
    if (root.document.readyState === "loading") root.document.addEventListener("DOMContentLoaded", start);
    else start();
  }
})(typeof window !== "undefined" ? window : globalThis);
