"""Unstructured bug definitions for the Case Analyzer agent."""

UNSTRUCTURED_BUGS = """
============================== BUGTRACKER DUMP ==============================
BUG-ID: 847392 | Component: Gateway-Controller | Severity: High
Title: Gateway controller routing logic drops connections during backend timeout mismatches
--- COMMENTS ---
[09:30 AM PDT - dev_triage] verified gateway timeout is hardcoded to 15000ms in routing layer header.
[11:30 AM PDT - oncall_eng] customer support linked ticket Case 10243 to this bug!! verified under load backend p99 latency hits 16.2s, causing hard drop on gateway side before HTTP response returns.
[13:15 PDT - dev_owner] created draft fix -> internal.pr.tracker/48392 to make routing gateway timeout dynamic & configurable via envoy flags. Status currently In Progress. Next step is code review on PR 48392.
=============================================================================
"""