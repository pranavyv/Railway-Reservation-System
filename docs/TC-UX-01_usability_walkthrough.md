# TC-UX-01: Usability walkthrough (RRS-NF-005)

**Requirement:** a usable interface with clear labels and sensible defaults, needing no manual
configuration to get started. **Pass:** a first-time user finishes every task below without help.

**Automated part:** `tests/test_usability.py` (labels, landmarks, defaults, status-colour contrast).
**Manual part:** this walkthrough, done once with someone who has not used the app (not a team member).

| Tester | Date | Device and browser |
|---|---|---|
| | | |

## Tasks (read the task aloud, then stay silent and watch)

| # | Task given to the tester | Done without help? (Y/N) | Time (min) | Where they hesitated |
|---|---|---|---|---|
| 1 | Create an account | | | |
| 2 | Log in | | | |
| 3 | Find trains from Bengaluru to Chennai for tomorrow | | | |
| 4 | Book one ticket and pay | | | |
| 5 | Find out whether your booking is Confirmed, RAC or Waitlisted | | | |
| 6 | Cancel the ticket and say how much money comes back | | | |
| 7 | (Admin tester) Add a train, then add a schedule for it | | | |

## Accessibility checks (one person, five minutes)

| Check | Pass? |
|---|---|
| Whole booking flow works with the keyboard only (Tab, Shift+Tab, Enter) | |
| First Tab press on any page shows "Skip to main content" | |
| Page is still usable at 200% browser zoom (no sideways scrolling for the form) | |
| Booking status can be told apart in greyscale (symbol and word, not only colour) | |
| Error messages say what to fix, next to the field | |

## Result

All tasks done without help and all checks passed: **PASS / FAIL**  (signed: ________)

Fixes made after the walkthrough:
