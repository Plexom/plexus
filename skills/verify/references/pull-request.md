# Delivery through a pull request

Read by `[stage7]verify` at acceptance when `delivery: pull-request` stands in
`config.md` — a team's way in; a person working alone never needs it.

Ask whether to push the branch and open the pull request; that answer
is the request to push. Its title is the iteration's id and name; its body — the problem,
the features it delivers with their names, the checklist with each outcome, and the
`Built-with` line by the commit signature rule. `gh pr create` when it is signed in,
otherwise the link the push prints. Then the checks: `gh pr checks` until they finish —
a failure is a finding of this verification, sorted by step 5, never merged over. The
merge itself is the user's or the team's, as the project merges anything; the iteration
is `accepted` when the user accepted the work, and the handover says the pull request is
waiting for its merge.
