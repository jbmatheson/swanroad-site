title: Playing without looking
date: 2026-11-14
description: What VoiceOver says about a square, and the other settings the game listens to.
published: true

A board game on a phone is mostly a picture, and a picture is the hardest thing to make work for someone who cannot see it. Swan Road was built to be played with VoiceOver from the first version, and this post is about what that took.

## What a square says

Every square on the board is its own element. Touch one and VoiceOver reads a sentence built from what is there:

> Row 3, column 4, pearl, drifting up, Light’s shore, pulled 3 up, 1 left.

The parts come in a fixed order so a regular player learns to listen for the one they need. The position first. Then what is on the square: a pearl, a Light anchor, a Dark anchor, or empty. For a pearl, what it will do when the turn ends: *drifting up*, or *held* when the pulls cancel or another pearl blocks the way. If a shore runs through that row, whose shore it is. Last, the pulls on the pearl, by strength and direction.

While you have a move pending but not yet confirmed, the pearls that would change say so: *this move drifts it left*. That is the spoken version of the arrows sighted players see before they confirm.

The tide bar has a spoken label too: *Tide*, or *Tide up: shores 3 deep* once it has risen.

## Type

The text scales with the Dynamic Type setting, including the board’s captions and the rules, up into the accessibility sizes. It stops growing at the size where the board would no longer fit on the screen, so the board keeps its squares. The splash screen caps its own type at the largest standard size, since it is decorative and a tap skips it.

## Motion

With Reduce Motion on, the pulsing highlight on a suggested square becomes a steady one, the puzzle animations hold still, and the opening screen shortens its fades and skips the small drop of the pearl. Nothing you need is conveyed by motion alone; the arrows and the spoken labels carry the same information.

## Contrast and colour

With Increase Contrast on, secondary text brightens; in the Night look, from sixty percent of the ink colour to eighty-five. In every look, the colours were chosen so that secondary text clears a 4.5 to 1 contrast against its background.

Colour never carries meaning on its own. The two shores are told apart by position, by the names in the spoken labels, and in the Nautical chart look by hatching: Light’s shore is hatched one way and Dark’s is cross-hatched.

## What it cost

Less than you would think, because most of it is the same work as making the game explain itself to anyone. The spoken label for a square is the drift preview in words. The tide bar’s label is the tide bar in words. Once the game can say what it is doing, saying it to VoiceOver is one more line.
