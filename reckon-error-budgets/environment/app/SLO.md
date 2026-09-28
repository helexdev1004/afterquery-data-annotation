# Service level objectives: how the fortnightly figures are made

## Requests

The collector writes one record for every request: the time, the stream it
arrived on, the HTTP status code as a number, and the latency in milliseconds.
`collector_rules.csv` holds the collector's relabelling rules, which give the
service each stream carries. `requests.csv` has the fortnight's records.

The collector was set up stream by stream, by whoever owned the service at the
time. Records that are not in the form this section describes are first
brought into it; every service is reported.

## A good request

`service_catalog.csv` gives each service's runtime, its latency objective in
milliseconds and its target, the percentage of requests that should be good. A
request is good when its status is below 500 and its latency is no more than
the service's latency objective.

## A week's figures

Weeks run Monday to Sunday; week 1 begins on Monday 1 February 2027. For a
service and a week, `good_pct` is the good requests as a percentage of all the
service's requests that week. The error budget is what the target leaves:
100 less the target. `budget_used_pct` is 100 less `good_pct`, as a percentage
of that budget, so a service exactly on target has used 100.
