title: The puzzle in your browser
date: 2026-11-17
description: Today’s puzzle now plays on the website: the same puzzle as the app, a fourth copy of the rules, and what the page leaves out on purpose.
published: true

A game with a new mechanic has a problem a screenshot cannot solve. Nobody knows what “the pearls drift” means until they have made one drift. From today the day’s puzzle [plays in a browser](/daily/), on a phone or at a desk, with nothing to install and no account.

## The same puzzle as the app

The app sets one puzzle a day: a position, a side to move, and one to four moves in which to force a pearl onto your shore whatever the other side answers. The book holds eighty of them, and the app walks through it in a fixed order that mixes the short puzzles with the long ones. The page takes the same walk. So the page and the app show the same puzzle on the same day, and in both the day turns over at midnight where you are.

## A wrong move is played out

In the app, a move that does not solve the puzzle is refused. The board jolts, a line of text says why, and nothing moves. That suits a player who already knows the game.

Someone meeting the page may never have seen a pearl drift. So the page plays the wrong move: the anchor lands, the pearls slide, the page says it was not the one, and the board goes back. The hope is that a few wrong moves show the rules better than a paragraph can. The tries are counted, and the count goes into the result you can share.

## A fourth copy of the rules

[The rules already existed three times](/devlog/how-the-computer-plays/): in Python, in Rust, and in Swift for the app. A browser runs none of those, so they were written once more, in JavaScript.

A fourth copy is a fourth chance to be wrong, and a puzzle page that drifted a pearl the wrong way would teach a game that does not exist. So before the page went up, every legal move from every position on every solution in the book was played twice, once by the JavaScript rules and once by the Python ones, and the boards were compared. That came to 15,233 moves and no differences.

Then the check was tested the way a smoke alarm is. Six faults were planted in the rules, one at a time. It caught five. The sixth removed the rule that a pearl may not drift onto a square where another pearl stood, and nothing changed, for a good reason: a pearl is never pulled toward the pearl beside it, because that pearl blocks the pull. The line guards against something the other rules already rule out.

## What the page leaves out

One puzzle a day, and only today’s. No hints, no streak, no archive. Those are in the app, along with everything a puzzle is not: an opponent who fights back, a friend across the table, the daily game and its leaderboard.

On an iPhone or iPad the page plays three daily puzzles and then points to the app, where the daily puzzle is free. A phone that can run the game should run the game. Anywhere else, the page never stops you.

The page remembers the days you solved in your own browser, so it can say so when you come back, and it sends nothing anywhere. The [privacy policy](/privacy/) has the details.
