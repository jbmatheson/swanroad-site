title: How the computer plays
date: 2026-11-14
description: Four levels, one search, and why Medium looks as deep as Hard but settles for less.
published: true

The computer opponent in Swan Road is a plain alpha-beta search: look ahead a fixed number of turns, score the positions at the end, and pick the move that leads to the best one if the other side also plays well. No neural network. The interesting choices were how deep to look and what to do with the answer.

## Three copies of the rules

The rules exist three times. A Python version was the first, written to try variants quickly. A Rust version came next, fast enough to play a hundred games against itself in a minute, and it is the one the balance work ran on. The Swift version is the one in the app.

Three versions can disagree, and a disagreement would mean the app plays a different game from the one the balance work tested. So two checks run whenever the rules change: every Python game is replayed in Rust step by step, and the Swift search is compared with the Rust search on random positions until the values match exactly. Both must stay at zero mismatches.

## How deep

Depth is the lever. On an iPhone 16 Plus, looking six turns ahead on the 7×7 board takes between a quarter of a second and six tenths of a second per move. One turn deeper takes three to fifteen seconds. So Expert looks six ahead and stops there, and five ahead on the bigger 9×9 board, where each turn has more moves.

- **Easy** looks two ahead.
- **Medium** and **Hard** look four ahead.
- **Expert** looks six ahead.

## Why Medium is not just a shallower Hard

The first Medium looked two turns ahead and picked its best move. It was no stronger than Easy. Looking three ahead was closer to Hard than to Easy. There was no depth between them that felt like a middle.

What worked was depth with a loose hand. Medium looks as far ahead as Hard, then picks at random from its three best moves, as long as they are within a band of the best. The band is sixty points, which is about six rows of pearl drift and well short of a whole pearl. It makes Medium a player who sees what Hard sees and sometimes takes the second-best road. Easy does the same with its six best moves. Hard and Expert always take the best.

## The daily game

The daily game is the same board for everyone, with one try. For that to be fair, the computer has to make the same reply on every phone, and a time limit would not do it: a new phone searches more in a second than an old one. So the daily opponent stops at a fixed number of positions examined instead of a fixed time. On an iPhone 12, the longest reply stays under about eight seconds.

## How strong

The campaign climbs from a gentle first opponent to Expert, and the climb was measured, not guessed: each level played hundreds of games against the others, and the rating anchors in the app come from the gaps those games showed. A strong player beats Expert about one time in twenty. For a while the daily game cycled Expert in every third day, and those days ended most streaks, so the daily now alternates Medium and Hard. Expert is still there under Play, for the days you want to lose with dignity.
