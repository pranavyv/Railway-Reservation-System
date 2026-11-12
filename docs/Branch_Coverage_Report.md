# Branch Coverage Report

**Project:** Railway Reservation System (RRS), Team 13 Jackfruit Phase-1  
**Generated:** 12-Nov-2026  
**Environment:** Python 3.11.9, Windows  
**Tool:** coverage.py (branch measurement on)  


## Summary

| Branches | Taken both ways | Branch coverage |
|---|---|---|
| 406 | 309 | 76.1% |

A branch is one outcome of a decision (for example the `if` taken and the `if` skipped). Each decision has at least two.


## Branch coverage per file

| File | Branches | Covered | Partial lines | Branch % |
|---|---|---|---|---|
| app.py | 32 | 1 | 1 | 3.1% |
| db.py | 2 | 0 | 0 | 0.0% |
| modules/admin.py | 12 | 11 | 1 | 91.7% |
| modules/allocation.py | 8 | 7 | 1 | 87.5% |
| modules/audit.py | 10 | 8 | 2 | 80.0% |
| modules/auth.py | 24 | 23 | 1 | 95.8% |
| modules/booking.py | 18 | 16 | 2 | 88.9% |
| modules/cancellation.py | 14 | 12 | 2 | 85.7% |
| modules/monitoring.py | 16 | 11 | 5 | 68.8% |
| modules/ops_routes.py | 4 | 4 | 0 | 100.0% |
| modules/payment.py | 10 | 9 | 1 | 90.0% |
| modules/pnr.py | 24 | 19 | 3 | 79.2% |
| modules/pnr_routes.py | 16 | 13 | 1 | 81.2% |
| modules/promotion.py | 8 | 8 | 0 | 100.0% |
| modules/rbac.py | 8 | 8 | 0 | 100.0% |
| modules/refund.py | 4 | 4 | 0 | 100.0% |
| modules/search.py | 16 | 15 | 1 | 93.8% |
| modules/seat_allocation.py | 14 | 13 | 1 | 92.9% |
| modules/session_guard.py | 10 | 9 | 1 | 90.0% |
| modules/train_admin.py | 62 | 58 | 4 | 93.5% |
| modules/train_admin_routes.py | 10 | 7 | 3 | 70.0% |
| modules/transport_security.py | 8 | 8 | 0 | 100.0% |
| reliability.py | 4 | 3 | 1 | 75.0% |
| repository/admin_repo.py | 16 | 13 | 3 | 81.2% |
| repository/audit_repo.py | 2 | 2 | 0 | 100.0% |
| repository/booking_repo.py | 6 | 4 | 2 | 66.7% |
| repository/cancellation_repo.py | 2 | 0 | 0 | 0.0% |
| repository/payment_repo.py | 16 | 15 | 1 | 93.8% |
| repository/promotion_repo.py | 10 | 8 | 2 | 80.0% |
| repository/train_admin_repo.py | 20 | 0 | 0 | 0.0% |


## Branches never taken (lowest files first)

- `db.py` (0.0%): line->target 35->36, 35->41
- `repository/cancellation_repo.py` (0.0%): line->target 42->43, 42->59
- `repository/train_admin_repo.py` (0.0%): line->target 65->66, 65->67, 77->78, 77->79, 85->86, 85->89, 98->99, 98->100, 105->106, 105->111, 122->123, 122->124, 124->125, 124->143, 131->132, 131->136, 150->151, 150->152, 153->154, 153->155
- `app.py` (3.1%): line->target 42->43, 43->44, 43->45, 54->55, 54->56, 61->62, 61->75, 67->68, 67->72, 68->69, 68->70, 80->81, 80->109, 92->93, 92->96, 104->105, 104->107, 134->135, 134->141, 138->139, 138->141, 165->166, 165->170, 170->171, 170->175 (+6 more)
- `repository/booking_repo.py` (66.7%): line->target 35->36, 83->84
- `modules/monitoring.py` (68.8%): line->target 51->53, 66->68, 75->76, 105->106, 112->113
- `modules/train_admin_routes.py` (70.0%): line->target 63->64, 78->79, 87->88
- `reliability.py` (75.0%): line->target 11->exit
- `modules/pnr.py` (79.2%): line->target 13->15, 40->47, 42->44, 45->40, 45->46
- `modules/audit.py` (80.0%): line->target 16->18, 30->31


## Explanation of gaps

Repository files contain SQL that needs a live Supabase database. Their logic is tested with a fake database cursor, so some SQL-only lines run only in manual system testing (see System_Validation_Report.md).


Full line-by-line view: `docs/reports/coverage_html/index.html` (open in a browser; red lines were never run, yellow lines had a branch not taken).
