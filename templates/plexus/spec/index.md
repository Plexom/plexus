# <The product's name>

<!-- template:
The spec's front page: what the product is, what it is made of, and what holds across all
of it. Each part of the product has its own file beside this one — for a game, the play,
the scoring, the records; for a company system, orders, billing, reports. A stage reads
this page and the parts its work touches, never the whole folder, so a spec of any size
stays readable. Headings and text are written in the language of the conversation; ids
and scope words stay as they are — scripts find items by them.

Each thing the product does is an item in its part, ending with its tag: the id, then its
scope — `MVP` for the first version, `release`, `later`, or `dropped` when the user gave it
up. Ids run across the whole spec, never per part. Status is never written here: a
feature is done when an accepted iteration lists it under `delivers`. The same id in the
middle of a sentence is a reference, not a definition.
-->

## What we are building

<What it is and who it is for, in two or three plain sentences. The look and feel in one
line, if it has an interface.>

## Parts

| part | file | what it covers |
|---|---|---|
| <the part's name, in its own words> | [<file>.md](<file>.md) | <one line> |

## What always matters

<!-- template:
What must never break, whatever is being built — speed, size, dependencies, security,
personal data, availability, the data kept and where it goes. Verification checks every one
of them on every iteration, because any change can break any of them.
-->

| id | what must always hold | how it is checked |
|---|---|---|
| constraint-01 | <what must always hold, in the user's sense of it> | <a test, a measurement, a look> |

## What we deliberately do not build

<What was cut, one line each. It is what keeps the scope from creeping.>

## Terms

<!-- template:
The words the spec uses and the names the code uses, as pairs, so one notion never gets
three names. A term enters on its second use.
-->

| term | in code | meaning |
|---|---|---|
| <term> | `<identifier>` | <what it means in this product> |
