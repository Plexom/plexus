# Base code smells

For the "Standards" axis of the review.

These apply even where the repository documents nothing. Each is a **flagged guess** ("this looks like …"), not a violation; a documented rule of the repository always outweighs it; anything the linter already checks is skipped.

- **An inarticulate name** — it does not say what it does or holds → rename it; if no honest name can be found, the intent is murky.
- **Duplication** — the same shape of logic in different places in the edit → extract it, call it from both.
- **Feature envy** — a method reaches into someone else's state more often than its own → move the method to the data.
- **A parameter clump** — the same fields travel together → this is asking to become its own type.
- **Primitive obsession** — a string or a number in place of a domain notion → give the notion its own type.
- **Repeated case analysis** — the same enumeration of variants in several places → polymorphism or a shared table.
- **Shotgun surgery** — one logical change forces edits scattered across files → gather what changes together.
- **Divergent change** — one module is edited for several unrelated reasons → split it.
- **Speculative generality** — abstractions and parameters for needs the requirements do not name → delete until a real need appears.
- **A message chain** — long navigation through someone else's internals → hide it behind a single method.
- **A middle man** — an entity that does almost nothing but delegate → remove it, call through directly.
