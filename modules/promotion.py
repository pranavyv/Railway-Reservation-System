"""Waitlist / RAC promotion (RRS-F-051).

When a seat frees up, passengers move up in booking order (earliest first):

  * a free confirmed seat goes to the earliest RAC passenger
    (or, if nobody is in RAC, to the earliest waitlisted passenger);
  * RAC places that open up (including the one just vacated) are refilled from
    the waiting list, up to the RAC quota for the class.

The plan is computed from the CURRENT state of the schedule and class, not from
which booking was cancelled, so running it twice never promotes anyone twice.
"""
from modules.seat_allocation import CONFIRMED, RAC, WAITLISTED, rac_capacity


def plan_promotions(total_seats, held_seats, rac_ids, waitlist_ids):
    """Pure rule. Returns [(booking_id, old_status, new_status), ...] in order.

    rac_ids and waitlist_ids must already be sorted by booking order.
    held_seats counts CONFIRMED bookings plus unexpired PROVISIONAL holds.
    """
    free = max(int(total_seats) - int(held_seats), 0)
    rac = list(rac_ids)
    waiting = list(waitlist_ids)
    moves = []

    while free > 0 and rac:
        moves.append((rac.pop(0), RAC, CONFIRMED))
        free -= 1
    while free > 0 and waiting:
        moves.append((waiting.pop(0), WAITLISTED, CONFIRMED))
        free -= 1

    quota = rac_capacity(int(total_seats))
    while len(rac) < quota and waiting:
        booking_id = waiting.pop(0)
        moves.append((booking_id, WAITLISTED, RAC))
        rac.append(booking_id)

    return moves


def rebalance_after_cancel(booking_id, actor_user_id, repo=None):
    """Promote waiting passengers on the schedule/class of a cancelled booking.

    Returns the list of promotions applied, e.g.
    [{"booking_id": 7, "from": "RAC", "to": "CONFIRMED"}].
    """
    if repo is None:
        from repository import promotion_repo  # lazy import keeps tests database-free

        repo = promotion_repo
    from modules import pnr

    return repo.rebalance_seats(booking_id, actor_user_id, plan_promotions, pnr.generate_pnr)
