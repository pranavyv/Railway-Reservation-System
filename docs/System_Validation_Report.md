# System Validation Report

**Project:** Railway Reservation System (RRS), Team 13 Jackfruit Phase-1  
**Generated:** 12-Nov-2026  
**Environment:** Python 3.11.9, Windows  
**Environment:** local Flask app against the Supabase test database  
**Tester:** ______________   **Browser:** ______________  


End-to-end checks run in the browser against the real database (the part of the STP system-test level that unit tests cannot cover). Fill in the Actual and Result columns, and attach a screenshot name for anything that failed.

Rows marked PASS were observed on 12-Nov-2026 during the first run of the merged build.

| ID | Requirement | Scenario | Where | Expected | Actual | Result |
|---|---|---|---|---|---|---|
| SV-01 | RRS-F-001 | Register a new account | Register page, valid details | Account created, can log in |  | [ ] |
| SV-02 | RRS-F-002 | Log in with the correct password | Login page | Dashboard opens | Behaved as expected | PASS |
| SV-03 | RRS-F-003 | Five wrong passwords, then the right one | Login page | Lockout message; right password refused until the lock ends |  | [ ] |
| SV-04 | RRS-F-010 | Search Bengaluru to Chennai | Search page | Trains with classes, fares and times | Behaved as expected | PASS |
| SV-05 | RRS-F-011 | Search a route with no trains | Search page | 'No trains found' message |  | [ ] |
| SV-06 | RRS-F-020 | Open Seat Availability | Availability page | Counts match the booking state |  | [ ] |
| SV-07 | RRS-F-021 | Book a ticket | Press Book, fill the form | Provisional hold (10 minutes) and payment step | Behaved as expected | PASS |
| SV-08 | RRS-F-022 | Submit the booking form with missing fields | Booking form | Clear error, no booking created |  | [ ] |
| SV-09 | RRS-F-030 | Pay Now (SUCCESS) | Payment step | Booking Confirmed with a PNR | Behaved as expected | PASS |
| SV-10 | RRS-F-031 | Pay with FAILED, then TIMEOUT | Payment step | Booking cancelled, seat available again |  | [ ] |
| SV-11 | RRS-F-040 | Look up the PNR | PNR Status page | Details and a Confirmed badge | Behaved as expected | PASS |
| SV-12 | RRS-F-041/042 | Cancel the ticket | PNR page, Cancel ticket | Status Cancelled; refund shown and recorded |  | [ ] |
| SV-13 | RRS-F-050/051 | 1-seat class: book 3 tickets, cancel the first | Admin page to make the schedule; PNR page | 2nd becomes Confirmed with PNR, 3rd becomes RAC |  | [ ] |
| SV-14 | RRS-F-060 | Add a train and a schedule, then search for it | /admin/trains, Search | It appears in search at once |  | [ ] |
| SV-15 | RRS-F-061 | Open admin reports | /admin/reports | Figures match the bookings made |  | [ ] |
| SV-16 | PRJ-SR-003 | Passenger opens an admin page or API | /admin/reports, /api/admin/audit-log | Access refused (403) |  | [ ] |
| SV-17 | PRJ-SR-004 | Stay idle past the timeout, then click | Any page | Redirected to the login page |  | [ ] |
| SV-18 | PRJ-SR-006 | Cancel as admin, then read the audit log | /api/admin/audit-log | Entry with user and time |  | [ ] |
| SV-19 | PRJ-SR-001 | Open the site over http while REQUIRE_HTTPS=1 | run_https.py | Redirected to https |  | [ ] |
| SV-20 | RRS-NF-002 | Run the uptime probe, then read availability | /api/admin/availability | Availability at or above 99% |  | [ ] |
| SV-21 | RRS-NF-005 | Usability walkthrough with a new user | docs/TC-UX-01_usability_walkthrough.md | All tasks done without help |  | [ ] |


## Defects found

| # | Scenario | What happened | Severity | Fixed in |
|---|---|---|---|---|
|  |  |  |  |  |


## Conclusion

All scenarios passed: **YES / NO**   Open defects: ____   Signed: ______________
