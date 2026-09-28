Error budgets for the platform review

A platform team reviews its eight backend services every fortnight against
their service level objectives. For each service and each of the two weeks the
reliability engineer needs the share of requests that were good - answered
without a server error and within the service's latency objective - and the
error budget that week consumed, as a percentage of the budget the objective
allows.

`/app/SLO.md` is the team's note on what counts as a good request, how a week's
figures are worked out and how the collector labels requests. The services,
their runtimes and their objectives are in `/app/service_catalog.csv`, the
collector's relabelling rules are in `/app/collector_rules.csv`, and the
fortnight's request records are in `/app/requests.csv`.

The figures go in `/app/error_budget.csv` with the columns `service`, `week`,
`good_pct` and `budget_used_pct`, a line such as `svc-example,2,99.912,88.0`. A
line is right when `good_pct` is within 0.002 and `budget_used_pct` within 0.5,
and the review will use the file if no more than one of the sixteen lines is
wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
