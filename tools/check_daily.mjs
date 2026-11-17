// The second half of tools/check_daily.py, which writes the fixture this reads and runs it. Not run by hand.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const P = createRequire(import.meta.url)(join(root, "daily", "puzzle.js"));
const fixture = JSON.parse(readFileSync(process.argv[2], "utf8"));

let failed = 0;
function check(ok, what) {
  if (ok) return;
  failed += 1;
  if (failed <= 20) console.log("  FAIL " + what);
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// 1. The page carries the app's book.
const page = readFileSync(join(root, "daily", "index.html"), "utf8");
const found = /<script type="application\/json" id="book">(.*?)<\/script>/s.exec(page);
check(!!found, "daily/index.html has no book");
const book = found ? JSON.parse(found[1]) : { puzzles: [] };
const app = fixture.book.puzzles;
check(book.version === fixture.book.version, `book version ${book.version}, the app's is ${fixture.book.version}`);
check(book.puzzles.length === app.length, `the page has ${book.puzzles.length} puzzles, the app ${app.length}`);
book.puzzles.forEach((p, i) => {
  const a = app[i] || {};
  for (const k of ["id", "n", "toMove", "turn", "cells", "supply", "score", "tree"]) check(same(p[k], a[k]), `puzzle ${p.id}: ${k} differs from the app's book`);
});
console.log(`book: ${book.puzzles.length} puzzles, version ${book.version}`);

// 2. Every puzzle is sound under the page's rules. The app lists only sound puzzles and counts the day's puzzle
//    along that list, so one unsound puzzle here would shift every day after it.
const unsound = book.puzzles.filter(p => !P.isSound(p)).map(p => p.id);
check(unsound.length === 0, `unsound under the page's rules: ${unsound.join(", ")}`);
console.log(`sound: ${book.puzzles.length - unsound.length} of ${book.puzzles.length}`);

// 3. Every legal move from every position on a solution: the page's rules against the simulator's.
let moves = 0, early = 0;
for (const c of fixture.cases) {
  const s = { cells: c.state.cells.split("").map(Number), supply: c.state.supply, score: c.state.score, toMove: c.state.toMove, turn: c.state.turn };
  const want = Object.keys(c.results).sort(), got = P.legal(s).slice().sort();
  check(same(want, got), `puzzle ${c.id}, turn ${s.turn}: legal moves differ (${got.length} here, ${want.length} in the simulator)`);
  for (const token of want) {
    moves += 1;
    const a = P.parse(token);
    check(a && P.tokenOf(a) === token, `token ${token} does not survive a round trip`);
    if (!a) continue;
    const r = P.apply(s, a).state, w = c.results[token];
    check(r.cells.join("") === w.cells && same(r.supply, w.supply) && same(r.score, w.score) && r.toMove === w.toMove && r.turn === w.turn,
      `puzzle ${c.id}, turn ${s.turn}, ${token}: the position after it differs from the simulator's`);
    // What the page tells a solver: a move it refuses on the last turn brings no pearl home.
    const home = w.score[s.toMove] > s.score[s.toMove];
    if (home && !c.winning.includes(token)) {
      if (c.left <= 1) check(false, `puzzle ${c.id}, turn ${s.turn}, ${token}: collects on the last move but is not in the solution`);
      else early += 1;
    }
  }
}
console.log(`rules: ${fixture.cases.length} positions, ${moves} moves compared with the simulator`);
console.log(`moves outside a solution that collect a pearl before the last turn: ${early} (the page refuses these without showing them, as the app does)`);

// 4. Which puzzle a day gets: the page's walk against the app's, and every puzzle once in each cycle.
for (const [day, index] of Object.entries(fixture.days)) check(P.dailyIndex(+day, app.length) === index, `day ${day}: the page picks ${P.dailyIndex(+day, app.length)}, the app ${index}`);
const cycle = new Set();
for (let d = 0; d < app.length; d++) cycle.add(P.dailyIndex(P.FIRST_MIXED_DAY + d, app.length));
check(cycle.size === app.length, `a cycle of ${app.length} days shows only ${cycle.size} puzzles`);
console.log(`days: ${Object.keys(fixture.days).length} checked against the app's walk`);

// 5. The day turns over at local midnight. The app counts days as (seconds since 1970 + the zone's offset) / 86400.
const instants = ["2026-11-17T04:59:59Z", "2026-11-17T05:00:00Z", "2026-11-17T14:59:59Z", "2026-11-17T15:00:00Z", "2026-06-30T22:30:00Z", "2026-03-08T07:30:00Z"];
const zones = { "America/Toronto": [-5, -5, -5, -5, -4, -4], "Asia/Tokyo": [9, 9, 9, 9, 9, 9], "Europe/London": [0, 0, 0, 0, 1, 0], "Pacific/Auckland": [13, 13, 13, 13, 12, 13], "UTC": [0, 0, 0, 0, 0, 0] };
for (const [zone, offsets] of Object.entries(zones)) {
  process.env.TZ = zone;
  instants.forEach((iso, i) => {
    const date = new Date(iso), want = Math.floor((date.getTime() / 1000 + offsets[i] * 3600) / 86400);
    check(P.dayNumber(date) === want, `${iso} in ${zone}: day ${P.dayNumber(date)}, expected ${want}`);
  });
}
process.env.TZ = "UTC";
check(P.dayNumber(new Date("2026-11-17T12:00:00Z")) === 20774, "17 November 2026 is not day 20774");
console.log(`midnight: ${instants.length} instants in ${Object.keys(zones).length} time zones`);

// 6. Who is sent to the app: an iPhone or iPad after the allowed days, never on a day already solved, nobody else.
const cap = P.WEB_DAYS_ON_IOS, past = {};
for (let d = 1; d <= cap; d++) past[20774 - d] = 0;
const fewer = Object.fromEntries(Object.entries(past).slice(1));
check(cap <= 0 || P.isGated(past, 20774, true) === true, "an iPhone that used its days is not sent to the app");
check(P.isGated(fewer, 20774, true) === false, "an iPhone with a day left is sent to the app");
check(P.isGated({ ...past, 20774: 2 }, 20774, true) === false, "an iPhone that solved today is locked out of replaying it");
check(P.isGated({ ...past, 1: 0, 2: 0, 3: 0 }, 20774, false) === false, "a desktop browser is sent to the app");
check(P.isIOS({ userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)" }) && P.isIOS({ userAgent: "Mozilla/5.0 (Macintosh)", platform: "MacIntel", maxTouchPoints: 5 })
  && !P.isIOS({ userAgent: "Mozilla/5.0 (Macintosh)", platform: "MacIntel", maxTouchPoints: 0 }) && !P.isIOS({ userAgent: "Mozilla/5.0 (Linux; Android 15)" }), "iPhone and iPad detection");
console.log(`limit: ${cap} days in the browser on an iPhone or iPad`);

// 7. A link that says where it was posted: the App Store link takes that name, and nothing else gets in.
const camp = "https://apps.apple.com/app/apple-store/id6821428315?pt=123456&ct=webdaily&mt=8";
check(P.withSource(camp, "?from=hn") === camp.replace("ct=webdaily", "ct=hn"), "?from=hn does not name the campaign");
check(P.withSource(camp, "?x=1&from=r-blind&y=2") === camp.replace("ct=webdaily", "ct=r-blind"), "from among other parameters is not read");
for (const search of ["", "?from=", "?from=HN", "?from=a b", "?from=a%26pt%3D1", "?from=" + "a".repeat(31), "?notfrom=hn", "?from=hn%0A"]) {
  check(P.withSource(camp, search) === camp, `"${search}" changed the App Store link`);
}
check(P.withSource("https://apps.apple.com/app/id6821428315", "?from=hn") === "https://apps.apple.com/app/id6821428315", "a plain link gained a campaign");
console.log("source: ?from= names the campaign and rejects everything else");

// 8. The board the page shares is the board the numbered pages show.
for (const p of book.puzzles.filter(p => P.tideDepth(p.turn) === 0)) {
  const shown = /<div class="board"[^>]*>([^<]*)<\/div>/.exec(readFileSync(join(root, "p", String(p.id), "index.html"), "utf8"));
  check(shown && shown[1] === P.grid(P.stateOf(p)), `puzzle ${p.id}: the shared board differs from p/${p.id}`);
}

console.log(failed ? `\n${failed} check(s) failed` : "\nall checks passed");
process.exit(failed ? 1 : 0);
