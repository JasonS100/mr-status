# External TDP watchdog

Runs on GitHub-hosted infrastructure, not the trading droplet. It checks only the
already-public publisher timestamp and a minimal observer timestamp. No SSH keys,
broker credentials, Discord secrets, account details or private engine reports
are needed by the monitor.

The requested schedule is every five minutes. GitHub can delay scheduled jobs;
this is not a guaranteed-latency paging service. Thresholds: publisher 15 minutes,
observer 20 minutes. A failed first probe is retried after 30 seconds, then the
workflow fails. Missing, malformed and future timestamps fail closed.

Watch failures through GitHub Actions notifications according to the account's
notification settings. This installation does not alter global notification
preferences or prove email/mobile receipt. Host-side Discord reports cannot
announce an outage if the host itself is offline; this workflow is the independent
failure signal. It performs no remediation.

A stale heartbeat means host, collector, publisher or delivery trouble, not proof
of a particular root cause. A GitHub-wide outage is a shared dependency and can
prevent this watchdog from running.
