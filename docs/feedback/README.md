# Feedback

Notes from people who know this kind of system and know what its users need to see. Meetings are about every two weeks. Each source has its own folder. A session file records what they said and what happened to each point.

Names and other identifying details stay out of this tree.

## Sources

| Folder | Who | Latest session | Still open |
|--------|-----|----------------|------------|
| [bank-charity-intermediary](bank-charity-intermediary/profile.md) | Owner of a very small firm between digital banks and charities | [02-10-2026](bank-charity-intermediary/02-10-2026.md) | Languages the builder does not speak (in progress); calling a local run from his phone |

## Add a source

1. Create `docs/feedback/<role-slug>/`. The slug names the role, not the person.
2. Add `profile.md` in that folder: who they are in relation to the product, how often you meet, and that their name stays private.
3. Add one session file per meeting, named `DD-MM-YYYY.md`.
4. Add a row to the table above.

## Session file

```markdown
# DD Month YYYY

| | |
|---|---|
| **Source** | [profile](profile.md) |
| **Date** | DD Month YYYY |

## Points

### F1 — short title

What they asked for, in their terms.

**Disposition:** Accepted, declined, or open — and why, in one or two sentences.

**Resolution:** Link to the commit, feature note, ADR, or `later.md` entry when one exists. Leave this off while the point is still open.
```

Number points `F1`, `F2`, … inside that file. A later session can point at `02-10-2026.md` F3.

Write the points down on the day of the meeting. Fill in the disposition when you decide. Add the resolution link when the work has a home. An accepted change that sets architecture still becomes an ADR. Deferred engineering still goes in [`later.md`](../software-engineering/later.md). This folder stays the log of who asked and where it went.
