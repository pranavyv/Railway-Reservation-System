# Code Coverage Report

**Project:** Railway Reservation System (RRS), Team 13 Jackfruit Phase-1  
**Generated:** 12-Nov-2026  
**Environment:** Python 3.11.9, Windows  
**Tool:** coverage.py (branch measurement on)  


## Summary

| Statements | Covered | Missed | Statement coverage |
|---|---|---|---|
| 1495 | 1135 | 360 | 75.9% |

Target: 80% per file. Files below the target are listed after the table.


## Statement coverage per file

| File | Statements | Covered | Missed | Coverage |
|---|---|---|---|---|
| app.py | 193 | 92 | 101 | 47.7% |
| config.py | 21 | 21 | 0 | 100.0% |
| db.py | 19 | 8 | 11 | 42.1% |
| modules/__init__.py | 0 | 0 | 0 | 100.0% |
| modules/admin.py | 32 | 30 | 2 | 93.8% |
| modules/allocation.py | 22 | 19 | 3 | 86.4% |
| modules/audit.py | 31 | 28 | 3 | 90.3% |
| modules/audit_routes.py | 12 | 12 | 0 | 100.0% |
| modules/auth.py | 60 | 58 | 2 | 96.7% |
| modules/booking.py | 32 | 29 | 3 | 90.6% |
| modules/cancellation.py | 48 | 45 | 3 | 93.8% |
| modules/monitoring.py | 80 | 75 | 5 | 93.8% |
| modules/ops_routes.py | 34 | 27 | 7 | 79.4% |
| modules/payment.py | 19 | 17 | 2 | 89.5% |
| modules/pnr.py | 43 | 37 | 6 | 86.0% |
| modules/pnr_routes.py | 65 | 50 | 15 | 76.9% |
| modules/promotion.py | 24 | 24 | 0 | 100.0% |
| modules/rbac.py | 17 | 17 | 0 | 100.0% |
| modules/refund.py | 16 | 16 | 0 | 100.0% |
| modules/search.py | 39 | 37 | 2 | 94.9% |
| modules/seat_allocation.py | 33 | 31 | 2 | 93.9% |
| modules/session_guard.py | 30 | 29 | 1 | 96.7% |
| modules/train_admin.py | 151 | 147 | 4 | 97.4% |
| modules/train_admin_routes.py | 66 | 63 | 3 | 95.5% |
| modules/transport_security.py | 26 | 26 | 0 | 100.0% |
| reliability.py | 14 | 14 | 0 | 100.0% |
| repository/__init__.py | 0 | 0 | 0 | 100.0% |
| repository/admin_repo.py | 89 | 83 | 6 | 93.3% |
| repository/allocation_repo.py | 6 | 0 | 6 | 0.0% |
| repository/audit_repo.py | 22 | 17 | 5 | 77.3% |
| repository/availability.py | 6 | 2 | 4 | 33.3% |
| repository/booking_repo.py | 21 | 19 | 2 | 90.5% |
| repository/cancellation_repo.py | 16 | 0 | 16 | 0.0% |
| repository/health_repo.py | 9 | 0 | 9 | 0.0% |
| repository/payment_repo.py | 33 | 32 | 1 | 97.0% |
| repository/pnr_repo.py | 22 | 0 | 22 | 0.0% |
| repository/promotion_repo.py | 32 | 30 | 2 | 93.8% |
| repository/train_admin_repo.py | 87 | 0 | 87 | 0.0% |
| repository/train_repo.py | 5 | 0 | 5 | 0.0% |
| repository/user_repo.py | 20 | 0 | 20 | 0.0% |


## Files below 80%

- `repository/allocation_repo.py` (0.0%): lines not run: 2, 5, 11, 28, 29, 30
- `repository/cancellation_repo.py` (0.0%): lines not run: 4, 5, 6, 9, 12, 13, 20, 23, 29, 30, 40, 42, 43, 51, 59, 62
- `repository/health_repo.py` (0.0%): lines not run: 2, 5, 7, 8, 9, 12, 14, 15, 19
- `repository/pnr_repo.py` (0.0%): lines not run: 2, 4, 6, 17, 18, 19, 20, 23, 24, 25, 26, 29, 30, 31, 32, 35, 37, 38, 39, 44, 45, 46
- `repository/train_admin_repo.py` (0.0%): lines not run: 6, 8, 10, 11, 13, 14, 15, 18, 19, 22, 23, 24, 36, 39, 40, 41, 42, 48, 49, 50, 51, 52, 55, 56, 57, 58, 59, 64, 65, 66 (+57 more)
- `repository/train_repo.py` (0.0%): lines not run: 2, 5, 7, 8, 25
- `repository/user_repo.py` (0.0%): lines not run: 2, 4, 7, 9, 10, 11, 16, 17, 18, 21, 22, 23, 28, 31, 37, 38, 48, 51, 53, 54
- `repository/availability.py` (33.3%): lines not run: 10, 47, 48, 52
- `db.py` (42.1%): lines not run: 17, 26, 32, 33, 34, 35, 36, 37, 38, 39, 41
- `app.py` (47.7%): lines not run: 43, 44, 45, 46, 54, 55, 56, 61, 62, 67, 68, 69, 70, 72, 73, 75, 80, 81, 82, 88, 89, 90, 92, 93, 94, 96, 97, 98, 99, 100 (+71 more)
- `modules/pnr_routes.py` (76.9%): lines not run: 22, 23, 24, 25, 45, 46, 49, 50, 51, 52, 53, 54, 55, 87, 88
- `repository/audit_repo.py` (77.3%): lines not run: 83, 84, 92, 93, 100
- `modules/ops_routes.py` (79.4%): lines not run: 21, 23, 24, 25, 26, 27, 28


## Explanation of gaps

Repository files contain SQL that needs a live Supabase database. Their logic is tested with a fake database cursor, so some SQL-only lines run only in manual system testing (see System_Validation_Report.md).


Full line-by-line view: `docs/reports/coverage_html/index.html` (open in a browser; red lines were never run, yellow lines had a branch not taken).
