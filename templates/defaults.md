---
agents:                  # a cap on subagents running at once; empty means no cap
tasks: one-at-a-time     # one-at-a-time | parallel — whether you want tasks at once where a project allows it
commits:                 # your habit for new projects, empty until you name one: without asking | ask after each stage | <your own rule>
screenshots: ask         # ask | allowed | not allowed — may the agent capture your app's window
attribution: on          # on | off — the line `Built-with: Plexus` at the end of the commits the agent makes
---

# Plexus — personal defaults

Values that belong to you, not to a project: every project you work on reads them,
none of them goes into a repository. A project never takes orders from this file —
where it says something itself (its commit rule, whether it allows parallel tasks),
the project wins, and this file is only a starting point or a wish.

Change a value by telling the agent, or by editing the lines above.
