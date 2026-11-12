# Test Case Document (updated after Sprints 1 and 2)

**Project:** Railway Reservation System (RRS), Team 13 Jackfruit Phase-1  
**Generated:** 12-Nov-2026  
**Environment:** Python 3.11.9, Windows  
**Replaces:** the test case list in STP v1.0, section 13  


## Result summary

| STP test cases | Passing (automated) | Manual only | Failing |
|---|---|---|---|
| 27 | 27 | 0 | 0 |


## Test cases

| TC | Requirement | What must be true | Level | Automated tests | Result | Linked by |
|---|---|---|---|---|---|---|
| TC-Auth-01 | RRS-F-001 | Valid registration creates an account; duplicate email is rejected | Unit | 2 | Pass | tag |
| TC-Auth-02 | RRS-F-002 | Correct credentials grant access to the dashboard | Unit | 2 | Pass | tag |
| TC-Auth-03 | RRS-F-003 | After 5 failed logins further attempts are blocked temporarily | Unit | 8 | Pass | tag |
| TC-Search-01 | RRS-F-010 | Matching trains are returned with class and timing | Unit | 1 | Pass | tag |
| TC-Search-02 | RRS-F-011 | 'No trains found' message for an unmatched route or date | Unit | 1 | Pass | tag |
| TC-Book-01 | RRS-F-020 | Availability count matches the allocation state | Unit | 5 | Pass | file |
| TC-Book-02 | RRS-F-021 | Provisional booking is created and held for a limited time | Unit | 4 | Pass | file |
| TC-Book-03 | RRS-F-022 | Missing or invalid booking fields are flagged | Unit | 4 | Pass | file |
| TC-Pay-01 | RRS-F-030 | Booking becomes Confirmed only after a Success payment | Integration | 8 | Pass | file |
| TC-Pay-02 | RRS-F-031 | Failed or timed-out payment releases the seat | Integration | 17 | Pass | tag |
| TC-PNR-01 | RRS-F-040 | A confirmed booking returns a valid PNR; lookup shows the right status | Unit | 3 | Pass | tag |
| TC-Cancel-01 | RRS-F-041 | Confirmed cancellation sets Cancelled and releases the seat | Unit | 2 | Pass | tag |
| TC-Cancel-02 | RRS-F-042 | Refund amount matches the cancellation policy | Unit | 4 | Pass | tag |
| TC-Alloc-01 | RRS-F-050 | Assigned status matches current capacity | Unit | 3 | Pass | tag |
| TC-Alloc-02 | RRS-F-051 | A cancellation promotes the earliest eligible waiting booking | Integration | 16 | Pass | tag |
| TC-Admin-01 | RRS-F-060 | Schedule changes are reflected in search results | Unit | 24 | Pass | tag |
| TC-Admin-02 | RRS-F-061 | Report figures match the underlying booking data | Unit | 21 | Pass | tag |
| TC-Perf-01 | RRS-NF-001 | 90th percentile transaction time is 5 seconds or less | Performance | 2 | Pass | tag |
| TC-Sec-01 | RRS-NF-003 | No sensitive data is stored or exposed in plaintext | Security | 7 | Pass | tag |
| TC-Ops-01 | RRS-NF-004 | Timestamped audit logs can be retrieved for sample bookings | Integration | 5 | Pass | tag |
| TC-UX-01 | RRS-NF-005 | Labels, defaults and contrast pass; walkthrough done without help | Usability | 10 | Pass (automated); manual walkthrough pending | tag |
| TC-Sec-02 | PRJ-SR-001 | Connections without TLS are rejected; TLS 1.2 or newer only | Security | 7 | Pass | tag |
| TC-Sec-03 | PRJ-SR-002 | Passwords are stored only as salted hashes | Security | 1 | Pass | tag |
| TC-Sec-04 | PRJ-SR-003 | Direct API calls to admin endpoints are rejected for passengers | Security | 21 | Pass | tag |
| TC-Sec-05 | PRJ-SR-004 | Session ends after the idle timeout | Security | 7 | Pass | tag |
| TC-Sec-06 | PRJ-SR-005 | No raw card-like data is stored; only reference and status | Security | 1 | Pass | file |
| TC-Sec-07 | PRJ-SR-006 | An audit entry exists for every admin action | Security | 11 | Pass | tag |


`Linked by: tag` means the test names the TC id in its docstring or a comment. `file` means the whole test file was mapped to the TC; check it. Add the TC id to a test's docstring to link it exactly.


## Changes since the submitted Test Plan (STP v1.0)

- Database: the build uses Supabase PostgreSQL, not MySQL as written in the SRS, SAD and STP. Repository code is tested with a fake cursor; SQL is exercised in system validation.
- Mock payment: the outcome (Success, Failed, Timeout) is chosen on the booking page for demonstration, which is how the planned Success/Failure test scenarios are driven.
- Added in Sprint 2: lockout (TC-Auth-03), idle timeout (TC-Sec-05), admin-only checks (TC-Sec-04), audit trail (TC-Sec-07, TC-Ops-01), waitlist/RAC promotion (TC-Alloc-02), train and schedule admin (TC-Admin-01), TLS (TC-Sec-02), health and uptime (RRS-NF-002), usability checks (TC-UX-01).
- TC-Sec-02 runs a real TLS handshake and checks that TLS 1.1 is refused, instead of only reading config.
- TC-UX-01 is split into an automated part (labels, contrast, defaults) and a manual walkthrough (docs/TC-UX-01_usability_walkthrough.md).
- RRS-NF-002 (99% availability) is evidenced by the uptime probe log, not by a pytest test.
