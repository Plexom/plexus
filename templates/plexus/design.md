---
mockup: plexus/design/mockup.html
updated: <YYYY-MM-DD>
---

# Design

<!-- template:
How the product looks and moves — the words behind the mockup. Tasks refer to screens by
their ids, the implementing agent gets the screen and the visual language verbatim, and
verification compares what runs with what is written here. The mockup is the picture;
where the two disagree, this file is corrected first.
-->

## Direction

<The mood — what it should feel like, what it resembles.>

## Screens

<!-- template:
Every screen the person sees, with what is on it and the states it can be in. A state
nobody drew is a state the code will improvise.
-->

| id | screen | what is on it | states | features |
|---|---|---|---|---|
| screen-01 | <name> | <what the person sees and can do> | <first run, normal, empty, error, …> | <feature-01> |

## Visual language

<!-- template:
Exact values, taken from the mockup: the code uses these names, so "the right blue" is
never guessed.
-->

### Colour

| token | value | where it is used |
|---|---|---|
| `<--name>` | <#hex> | <what it colours> |

### Type

| role | font | size / weight |
|---|---|---|
| <heading> | <family, fallbacks> | <size, weight> |

### Space and shape

<The spacing step, corner radii, borders, shadows or glow.>

### Motion

| what moves | how | duration, curve |
|---|---|---|
| <what> | <how it moves> | <ms, easing> |

## Accessibility

<Contrast of text against its background, keyboard use, what happens when the system asks
for reduced motion.>

## Decided, and why

<The choices made at this stage with the reason for each — what was tried in the mockup
and dropped, so it is not proposed again.>
