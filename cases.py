"""Unstructured case definitions for the Case Analyzer agent."""

UNSTRUCTURED_CASES = """
--- EMAIL FORWARD ---
From: customer-support@retailcorp.io
Subject: Fwd: URGENT: Cloud SQL CPU hitting 100% constantly!! (#ticket-10241)
Date: Mon, CDT 09:15
Hey Miguel, customer complains about high CPU usage on Cloud SQL postgres instance.
At 9:15am Miguel recommended enabling Query Insights to spot slow queries. Customer shared query logs around 11am CDT.
Looks like full table scans on orders. Miguel recommended adding a compound index on the 'orders' table. Next step: follow up tomorrow after index build finishes to verify CPU drop.
---------------------

=== SLACK TRANSCRIPT (CHANNEL #support-triage) ===
[10:00 CDT] miguel_g: hey @here got a weird one - ref: 10242 - user cannot access Google Cloud Console, getting 403 Forbidden across the board
[10:05 CDT] miguel_g: suggested clearing browser cache & incognito cookies, didn't work
[11:30 CDT] customer_ops: heads up Miguel, this issue persists across 15+ different users in our org now!
[11:32 CDT] sarah_mgr: whoa okay that's an org policy block. escalating ticket 10242 to Tier 3 support bridge immediately!! Next action is Tier 3 checking VPC Service Controls perimeter audit logs.

[[PAGERDUTY INCIDENT ALERT - Case-10243]]
**API Gateway intermittent 502 Bad Gateway errors**
08:45 AM CDT: Miguel verified backend service timeout config on Cloud Run.
10:15 AM CDT: Live debugging call with customer revealed the gateway timeout (15s) is lower than the backend response time under heavy load (16s).
11:30 AM CDT: Internal engineering analysis confirmed this is tied to routing bug [847392] in the gateway controller layer.
RECOMMENDED ACTION: Workaround by bumping API Gateway timeout or patching controller bug 847392.
"""