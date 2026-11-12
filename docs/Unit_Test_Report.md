# Unit Test Report

**Project:** Railway Reservation System (RRS), Team 13 Jackfruit Phase-1  
**Generated:** 12-Nov-2026  
**Environment:** Python 3.11.9, Windows  
**Tool:** pytest  


## Summary

| Total | Passed | Failed | Errors | Skipped | Pass rate | Run time |
|---|---|---|---|---|---|---|
| 231 | 231 | 0 | 0 | 0 | 100.0% | 12.1s |


## Results by test file

| Test file | Tests | Passed | Failed | Skipped |
|---|---|---|---|---|
| test_admin.py | 11 | 11 | 0 | 0 |
| test_admin_routes.py | 10 | 10 | 0 | 0 |
| test_audit_repo.py | 9 | 9 | 0 | 0 |
| test_auth.py | 6 | 6 | 0 | 0 |
| test_availability.py | 5 | 5 | 0 | 0 |
| test_booking.py | 14 | 14 | 0 | 0 |
| test_booking_repo.py | 1 | 1 | 0 | 0 |
| test_cancellation.py | 8 | 8 | 0 | 0 |
| test_lockout.py | 8 | 8 | 0 | 0 |
| test_monitoring.py | 13 | 13 | 0 | 0 |
| test_payment.py | 15 | 15 | 0 | 0 |
| test_payment_repo.py | 9 | 9 | 0 | 0 |
| test_payment_security.py | 1 | 1 | 0 | 0 |
| test_performance.py | 2 | 2 | 0 | 0 |
| test_pnr.py | 10 | 10 | 0 | 0 |
| test_pnr_routes.py | 6 | 6 | 0 | 0 |
| test_promotion.py | 16 | 16 | 0 | 0 |
| test_rbac_audit.py | 11 | 11 | 0 | 0 |
| test_refund.py | 8 | 8 | 0 | 0 |
| test_search.py | 6 | 6 | 0 | 0 |
| test_seat_allocation.py | 7 | 7 | 0 | 0 |
| test_sensitive_data.py | 7 | 7 | 0 | 0 |
| test_session_timeout.py | 7 | 7 | 0 | 0 |
| test_train_admin.py | 14 | 14 | 0 | 0 |
| test_train_admin_routes.py | 10 | 10 | 0 | 0 |
| test_transport_security.py | 7 | 7 | 0 | 0 |
| test_usability.py | 10 | 10 | 0 | 0 |


## Failures

None. All executed tests passed.


## Every test


### test_admin.py

| Test | Result | Time (s) |
|---|---|---|
| test_parse_date_range_valid | passed | 0.008 |
| test_parse_date_range_optional | passed | 0.001 |
| test_parse_date_range_invalid_format | passed | 0.001 |
| test_parse_date_range_start_after_end | passed | 0.001 |
| test_generate_report_calls_repository | passed | 0.002 |
| test_generate_report_rejects_invalid_date_range | passed | 0.002 |
| test_get_booking_report_aggregation | passed | 0.010 |
| test_get_occupancy_report_aggregation | passed | 0.007 |
| test_get_revenue_report_aggregation | passed | 0.007 |
| test_empty_reports_handle_zeroes_gracefully | passed | 0.007 |
| test_get_audit_trail_validation | passed | 0.001 |


### test_admin_routes.py

| Test | Result | Time (s) |
|---|---|---|
| test_admin_reports_page_requires_login | passed | 0.019 |
| test_admin_reports_page_rejects_passenger | passed | 0.034 |
| test_admin_reports_page_accessible_by_admin | passed | 0.031 |
| test_admin_reports_api_requires_login | passed | 0.002 |
| test_admin_reports_api_rejects_passenger | passed | 0.004 |
| test_admin_reports_api_accessible_by_admin | passed | 0.005 |
| test_admin_audit_api_rejects_passenger | passed | 0.006 |
| test_admin_audit_api_accessible_by_admin | passed | 0.004 |
| test_create_booking_api_success | passed | 0.008 |
| test_create_booking_api_validation_error | passed | 0.005 |


### test_audit_repo.py

| Test | Result | Time (s) |
|---|---|---|
| test_write_audit_log | passed | 0.005 |
| test_get_booking_audit_logs | passed | 0.004 |
| test_all_six_required_lifecycle_actions_supported[BOOKING_CREATED] | passed | 0.004 |
| test_all_six_required_lifecycle_actions_supported[PAYMENT_SUCCESS] | passed | 0.003 |
| test_all_six_required_lifecycle_actions_supported[PAYMENT_FAILED] | passed | 0.003 |
| test_all_six_required_lifecycle_actions_supported[PAYMENT_TIMEOUT] | passed | 0.004 |
| test_all_six_required_lifecycle_actions_supported[BOOKING_CANCELLED] | passed | 0.003 |
| test_all_six_required_lifecycle_actions_supported[BOOKING_EXPIRED] | passed | 0.003 |
| test_get_recent_audit_logs_unfiltered_and_filtered | passed | 0.006 |


### test_auth.py

| Test | Result | Time (s) |
|---|---|---|
| test_valid_registration_creates_account | passed | 0.143 |
| test_duplicate_email_rejected | passed | 0.299 |
| test_invalid_registration_fields_rejected | passed | 0.001 |
| test_password_is_hashed_not_plaintext | passed | 0.145 |
| test_login_with_correct_credentials | passed | 0.299 |
| test_login_with_wrong_password_or_unknown_user | passed | 0.290 |


### test_availability.py

| Test | Result | Time (s) |
|---|---|---|
| test_available_seats | passed | 0.002 |
| test_fully_booked | passed | 0.002 |
| test_invalid_train_id | passed | 0.002 |
| test_invalid_class | passed | 0.001 |
| test_train_not_found | passed | 0.008 |


### test_booking.py

| Test | Result | Time (s) |
|---|---|---|
| test_valid_booking_creates_provisional_booking | passed | 0.002 |
| test_invalid_booking_details_are_rejected[user_id-0] | passed | 0.002 |
| test_invalid_booking_details_are_rejected[schedule_id-0] | passed | 0.002 |
| test_invalid_booking_details_are_rejected[passenger_name-] | passed | 0.002 |
| test_invalid_booking_details_are_rejected[passenger_name-   ] | passed | 0.003 |
| test_invalid_booking_details_are_rejected[passenger_age-abc] | passed | 0.002 |
| test_invalid_booking_details_are_rejected[passenger_age-0] | passed | 0.001 |
| test_invalid_booking_details_are_rejected[passenger_age-121] | passed | 0.002 |
| test_invalid_booking_details_are_rejected[passenger_gender-] | passed | 0.001 |
| test_invalid_booking_details_are_rejected[passenger_gender-Unknown] | passed | 0.002 |
| test_invalid_booking_details_are_rejected[class_code-1A] | passed | 0.001 |
| test_invalid_booking_details_are_rejected[berth_preference-Invalid] | passed | 0.001 |
| test_passenger_name_is_trimmed | passed | 0.002 |
| test_optional_berth_preference_can_be_empty | passed | 0.001 |


### test_booking_repo.py

| Test | Result | Time (s) |
|---|---|---|
| test_expired_bookings_generate_audit_events | passed | 0.008 |


### test_cancellation.py

| Test | Result | Time (s) |
|---|---|---|
| test_cancel_updates_status_and_records_refund | passed | 0.001 |
| test_refund_shrinks_close_to_departure | passed | 0.001 |
| test_preview_does_not_cancel | passed | 0.001 |
| test_confirmation_is_required | passed | 0.001 |
| test_cannot_cancel_someone_elses_ticket | passed | 0.001 |
| test_admin_can_cancel_any_ticket | passed | 0.001 |
| test_cannot_cancel_twice | passed | 0.002 |
| test_unknown_or_malformed_pnr | passed | 0.001 |


### test_lockout.py

| Test | Result | Time (s) |
|---|---|---|
| test_four_failures_do_not_lock | passed | 0.884 |
| test_fifth_failure_locks_account | passed | 0.895 |
| test_locked_account_refuses_even_correct_password | passed | 1.689 |
| test_lock_ends_after_lockout_period | passed | 1.821 |
| test_success_resets_failure_counter | passed | 1.485 |
| test_unknown_email_never_raises_locked | passed | 0.155 |
| test_minutes_left_rounds_up | passed | 0.001 |
| test_naive_datetime_from_db_is_treated_as_utc | passed | 0.147 |


### test_monitoring.py

| Test | Result | Time (s) |
|---|---|---|
| test_retry_succeeds_after_transient_failures_with_doubling_delay | passed | 0.002 |
| test_retry_gives_up_after_the_last_attempt | passed | 0.001 |
| test_retry_does_not_repeat_other_errors | passed | 0.001 |
| test_metrics_count_requests_and_server_errors | passed | 0.001 |
| test_empty_metrics_have_zero_error_rate | passed | 0.002 |
| test_availability_percentage_from_log | passed | 0.083 |
| test_availability_window_and_missing_or_damaged_log | passed | 0.023 |
| test_probe_once_reports_up_down_and_unreachable | passed | 1.572 |
| test_health_is_200_when_database_answers_and_503_otherwise_without_leaking | passed | 0.014 |
| test_db_ok_hides_exception_details | passed | 0.009 |
| test_availability_report_is_admin_only | passed | 0.013 |
| test_availability_report_contents | passed | 0.080 |
| test_availability_report_without_data_yet | passed | 0.007 |


### test_payment.py

| Test | Result | Time (s) |
|---|---|---|
| test_successful_payment | passed | 0.003 |
| test_rac_booking_gets_no_pnr | passed | 0.004 |
| test_unsuccessful_payment[FAILED] | passed | 0.003 |
| test_unsuccessful_payment[TIMEOUT] | passed | 0.002 |
| test_transaction_reference_generated | passed | 0.001 |
| test_invalid_user_id[0] | passed | 0.002 |
| test_invalid_user_id[-1] | passed | 0.002 |
| test_invalid_user_id[1] | passed | 0.002 |
| test_invalid_user_id[True] | passed | 0.002 |
| test_invalid_booking_id[0] | passed | 0.001 |
| test_invalid_booking_id[-1] | passed | 0.002 |
| test_invalid_booking_id[1] | passed | 0.002 |
| test_invalid_booking_id[True] | passed | 0.003 |
| test_invalid_payment_outcome | passed | 0.002 |
| test_payment_outcome_is_case_insensitive | passed | 0.004 |


### test_payment_repo.py

| Test | Result | Time (s) |
|---|---|---|
| test_successful_payment_confirms_booking_and_records_audit | passed | 0.007 |
| test_failed_payment_releases_seat_and_records_audit | passed | 0.006 |
| test_timeout_payment_releases_seat_and_records_audit | passed | 0.006 |
| test_expired_hold_forces_timeout_status | passed | 0.013 |
| test_duplicate_payment_rejected | passed | 0.017 |
| test_payment_rejected_when_not_provisional | passed | 0.013 |
| test_payment_rejected_when_booking_not_found | passed | 0.012 |
| test_invalid_status_and_txn_ref_rejected | passed | 0.002 |
| test_get_booking_for_user | passed | 0.007 |


### test_payment_security.py

| Test | Result | Time (s) |
|---|---|---|
| test_payments_table_does_not_store_card_details | passed | 0.004 |


### test_performance.py

| Test | Result | Time (s) |
|---|---|---|
| test_booking_transaction_performance_90th_percentile | passed | 0.137 |
| test_payment_failure_workflow_performance | passed | 0.004 |


### test_pnr.py

| Test | Result | Time (s) |
|---|---|---|
| test_generated_pnr_is_ten_digits | passed | 0.001 |
| test_generate_retries_until_unique | passed | 0.001 |
| test_generate_gives_up_after_attempts | passed | 0.001 |
| test_confirmed_booking_gets_a_pnr | passed | 0.003 |
| test_assign_is_idempotent | passed | 0.001 |
| test_unconfirmed_or_missing_booking_gets_no_pnr | passed | 0.002 |
| test_lookup_returns_correct_status | passed | 0.001 |
| test_lookup_unknown_pnr_returns_none | passed | 0.002 |
| test_lookup_rejects_malformed_pnr | passed | 0.001 |
| test_only_owner_or_admin_can_look_up | passed | 0.001 |


### test_pnr_routes.py

| Test | Result | Time (s) |
|---|---|---|
| test_api_requires_login | passed | 0.013 |
| test_pnr_status_hides_internal_user_id | passed | 0.010 |
| test_pnr_status_not_found_and_bad_input | passed | 0.018 |
| test_cancel_success_and_errors | passed | 0.033 |
| test_cancel_without_confirm_flag_is_rejected_by_service | passed | 0.009 |
| test_allocation_status_endpoint | passed | 0.025 |


### test_promotion.py

| Test | Result | Time (s) |
|---|---|---|
| test_free_seat_goes_to_earliest_rac_then_waitlist_refills_rac | passed | 0.001 |
| test_nothing_changes_when_no_seat_is_free_and_rac_is_full | passed | 0.001 |
| test_booking_order_is_respected | passed | 0.001 |
| test_waitlisted_gets_seat_directly_when_nobody_is_in_rac | passed | 0.001 |
| test_two_free_seats_promote_two_rac_passengers | passed | 0.001 |
| test_rac_cancellation_pulls_waitlist_into_rac | passed | 0.002 |
| test_rac_quota_is_never_exceeded | passed | 0.001 |
| test_empty_queues_and_overbooked_inputs_are_safe | passed | 0.002 |
| test_plan_is_idempotent_once_applied | passed | 0.001 |
| test_rebalance_after_cancel_hands_planner_and_pnr_maker_to_repo | passed | 0.001 |
| test_repo_promotes_rac_to_confirmed_with_pnr_and_waitlist_to_rac | passed | 0.017 |
| test_repo_second_run_promotes_nobody_again | passed | 0.005 |
| test_repo_booking_order_uses_created_at_then_id | passed | 0.002 |
| test_repo_unknown_booking_or_no_free_seat_changes_nothing | passed | 0.003 |
| test_repo_unexpired_provisional_hold_keeps_the_seat | passed | 0.002 |
| test_cancel_booking_calls_rebalance_and_survives_its_failure | passed | 0.011 |


### test_rbac_audit.py

| Test | Result | Time (s) |
|---|---|---|
| test_anonymous_gets_401_on_admin_api | passed | 0.010 |
| test_passenger_direct_api_call_gets_403 | passed | 0.009 |
| test_admin_is_allowed | passed | 0.009 |
| test_unknown_or_blank_role_is_refused | passed | 0.039 |
| test_html_admin_page_never_leaks_to_passenger | passed | 0.021 |
| test_audit_log_endpoint_is_admin_only | passed | 0.016 |
| test_log_action_records_user_action_and_details | passed | 0.001 |
| test_log_action_requires_user_and_action | passed | 0.001 |
| test_details_are_redacted | passed | 0.001 |
| test_recent_entries_newest_first_and_limit_clamped | passed | 0.001 |
| test_audit_log_endpoint_returns_entries_to_admin | passed | 0.022 |


### test_refund.py

| Test | Result | Time (s) |
|---|---|---|
| test_percent_by_time_left | passed | 0.001 |
| test_threshold_boundaries_are_inclusive | passed | 0.002 |
| test_no_refund_after_departure | passed | 0.001 |
| test_default_policy_used_when_table_empty | passed | 0.001 |
| test_amount_matches_policy | passed | 0.001 |
| test_amount_is_rounded_to_paise | passed | 0.001 |
| test_zero_refund_amount | passed | 0.001 |
| test_hours_before_departure | passed | 0.003 |


### test_search.py

| Test | Result | Time (s) |
|---|---|---|
| test_matching_trains_returned_with_class_and_timing | passed | 0.001 |
| test_no_match_returns_empty_list | passed | 0.001 |
| test_missing_fields_rejected_without_querying | passed | 0.003 |
| test_same_source_and_destination_rejected | passed | 0.001 |
| test_past_and_malformed_dates_rejected | passed | 0.002 |
| test_today_is_allowed | passed | 0.001 |


### test_seat_allocation.py

| Test | Result | Time (s) |
|---|---|---|
| test_rac_capacity_is_ten_percent_rounded_up | passed | 0.002 |
| test_confirmed_while_seats_are_free | passed | 0.001 |
| test_rac_when_full_and_rac_quota_open | passed | 0.001 |
| test_waitlisted_when_full_and_rac_quota_full | passed | 0.001 |
| test_assign_status_uses_repo_counts | passed | 0.001 |
| test_assign_status_unknown_schedule_returns_none | passed | 0.001 |
| test_assign_status_validates_input | passed | 0.001 |


### test_sensitive_data.py

| Test | Result | Time (s) |
|---|---|---|
| test_users_table_stores_only_a_password_hash | passed | 0.002 |
| test_no_table_has_card_or_secret_columns | passed | 0.003 |
| test_registration_hashes_with_a_salted_algorithm | passed | 0.297 |
| test_session_cookie_never_contains_password_or_hash | passed | 0.006 |
| test_app_login_route_stores_only_safe_keys | passed | 0.015 |
| test_application_code_never_logs_credentials | passed | 0.025 |
| test_session_cookie_flags_are_hardened | passed | 0.001 |


### test_session_timeout.py

| Test | Result | Time (s) |
|---|---|---|
| test_is_expired_boundaries | passed | 0.001 |
| test_active_session_passes_and_is_refreshed | passed | 0.010 |
| test_idle_api_call_gets_401_and_session_is_cleared | passed | 0.008 |
| test_old_token_stays_dead_after_expiry | passed | 0.014 |
| test_idle_page_request_redirects_to_login | passed | 0.008 |
| test_session_without_timestamp_is_stamped_then_times_out | passed | 0.010 |
| test_anonymous_requests_are_untouched | passed | 0.006 |


### test_train_admin.py

| Test | Result | Time (s) |
|---|---|---|
| test_valid_train_is_cleaned | passed | 0.002 |
| test_train_rejects_bad_fields | passed | 0.001 |
| test_partial_update_checks_only_supplied_fields | passed | 0.001 |
| test_classes_validation | passed | 0.001 |
| test_travel_date_validation | passed | 0.001 |
| test_add_train_records_actor_and_returns_view | passed | 0.001 |
| test_invalid_train_never_reaches_the_repository | passed | 0.001 |
| test_duplicate_train_becomes_conflict | passed | 0.002 |
| test_update_and_remove_train_not_found | passed | 0.001 |
| test_update_train_passes_only_changed_fields_and_audit_details | passed | 0.001 |
| test_add_schedule_cleans_classes_and_date | passed | 0.001 |
| test_schedule_clash_and_missing_train | passed | 0.001 |
| test_remove_schedule_with_bookings_is_a_conflict | passed | 0.001 |
| test_list_trains_groups_rows_into_trains_schedules_classes | passed | 0.001 |


### test_train_admin_routes.py

| Test | Result | Time (s) |
|---|---|---|
| test_every_endpoint_rejects_anonymous_and_passengers | passed | 0.156 |
| test_passenger_cannot_change_anything | passed | 0.010 |
| test_admin_adds_train | passed | 0.026 |
| test_validation_error_is_400_with_messages | passed | 0.014 |
| test_form_posts_are_refused_to_block_csrf | passed | 0.017 |
| test_duplicate_is_409_and_missing_is_404 | passed | 0.031 |
| test_update_and_remove_train | passed | 0.014 |
| test_schedule_endpoints | passed | 0.020 |
| test_list_endpoint_returns_trains | passed | 0.014 |
| test_page_is_admin_only | passed | 0.038 |


### test_transport_security.py

| Test | Result | Time (s) |
|---|---|---|
| test_plain_http_page_is_redirected_to_https | passed | 0.005 |
| test_plain_http_api_and_posts_are_rejected | passed | 0.006 |
| test_https_requests_work_and_get_hsts | passed | 0.008 |
| test_rule_is_off_by_default_for_local_development | passed | 0.005 |
| test_forwarded_proto_is_ignored_unless_proxy_is_trusted | passed | 0.010 |
| test_safe_headers_are_always_sent | passed | 0.007 |
| test_ssl_context_refuses_anything_below_tls_1_2 | passed | 0.289 |


### test_usability.py

| Test | Result | Time (s) |
|---|---|---|
| test_every_form_field_has_a_label | passed | 0.021 |
| test_images_have_alt_text | passed | 0.017 |
| test_base_page_has_language_main_landmark_and_skip_link | passed | 0.001 |
| test_messages_are_announced_to_screen_readers | passed | 0.001 |
| test_search_form_has_sensible_defaults | passed | 0.002 |
| test_no_configuration_needed_to_start | passed | 0.001 |
| test_contrast_helper_matches_known_values | passed | 0.001 |
| test_status_badge_colours_meet_aa_contrast | passed | 0.001 |
| test_every_status_badge_also_has_a_symbol | passed | 0.002 |
| test_main_page_colours_meet_aa_contrast | passed | 0.001 |

