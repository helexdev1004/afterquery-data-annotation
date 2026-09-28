# AfterQuery — data annotation for AI evaluation

Thirty-eight **harbor-format benchmark tasks** written for the AfterQuery Experts programme.
Each one lives in its own repository; this page is the index.

This is data annotation of a particular kind. There is no labelling queue and no rubric to tick
through: each item is a complete, self-contained piece of professional work, packaged so that a
frontier AI agent can attempt it unaided and a program can decide, without a human in the loop,
whether it actually got the job done.

Every task ships four things:

- **an instruction** — the brief, written the way a colleague would hand the work over
- **an environment** — a Docker image holding the data, tools and mess the work starts from
- **a sealed verifier** — a second container, invisible to the agent, that scores the result `0` or `1`
- **a reference solution** — the work done properly, proving the task is solvable

The domains were chosen for depth rather than breadth: geodetic network adjustment, quarry blast
vibration compliance, bell partial spectra, GD&T plate inspection, fish respirometry, seed genebank
provenance, concurrency bugs in a ledger service. Each one is work somebody is paid to do.

## How a task runs

1. Harbor builds `environment/Dockerfile` and drops the agent inside with `instruction.md`.
   It has a shell, network access and a fixed time budget.
2. The container stops. Only the paths named in `artifacts` in `task.toml` survive.
3. A second container is built from `tests/Dockerfile`. The verifier runs there with those
   artifacts mounted, compares them against ground truth the agent never had access to, and
   writes a single `0` or `1`.

Two calibration runs keep it honest: the **oracle** run substitutes `solution/solve.sh` for the
agent and must score `1`; the **nop** run does nothing at all and must score `0`.

## Running any of them

With [harbor](https://github.com/laude-institute/harbor) installed and Docker running:

```bash
uv tool install harbor

git clone https://github.com/helexdev1004/afterquery-geodetic-network-adjust
cd afterquery-geodetic-network-adjust
harbor run -p . -a oracle -e docker   # reference solution — must score 1
harbor run -p . -a nop    -e docker   # nothing happens    — must score 0
```

## The tasks

### Science

| Task | What it asks for | Field | Agent budget | Expert estimate |
| --- | --- | --- | --- | --- |
| [`assign-find-contexts`](https://github.com/helexdev1004/afterquery-assign-find-contexts) | Assign excavation finds to their stratigraphic contexts | Archaeology | 4 h | 7 h |
| [`bed-lake-samples`](https://github.com/helexdev1004/afterquery-bed-lake-samples) | Attribute lake sediment samples to their source beds | Geology | 4 h | 5 h |
| [`calibrate-plot-moisture`](https://github.com/helexdev1004/afterquery-calibrate-plot-moisture) | Calibrate TDR and capacitance probes to volumetric water content | Soil Physics | 4 h | 3 h |
| [`certify-piece-soaks`](https://github.com/helexdev1004/afterquery-certify-piece-soaks) | Derive soak times for heat-treatment certificates | Heat Treatment | 4 h | 4 h |
| [`connect-borough-drains`](https://github.com/helexdev1004/afterquery-connect-borough-drains) | Resolve the downstream manhole for each borough drain | Engineering | 4 h | 7 h |
| [`derive-trout-respiration`](https://github.com/helexdev1004/afterquery-derive-trout-respiration) | Work up intermittent-flow respirometry into SMR and RMR | Biology | 4 h | 4 h |
| [`esterase-assay-workup`](https://github.com/helexdev1004/afterquery-esterase-assay-workup) | Work up 96-well esterase screens into per-mosquito activity | Biology | 4 h | 5 h |
| [`gauge-blast-vibration`](https://github.com/helexdev1004/afterquery-gauge-blast-vibration) | Extract peak vertical ground velocity from a quarry blast | Seismology | 4 h | 3 h |
| [`geodetic-network-adjust`](https://github.com/helexdev1004/afterquery-geodetic-network-adjust) | Least-squares adjustment of an unfamiliar geodetic network | Earth | 4 h | 6 h |
| [`grade-pulled-boards`](https://github.com/helexdev1004/afterquery-grade-pulled-boards) | Grade sawn oak boards against the visual grading rules | Engineering | 4 h | 7 h |
| [`integrate-tracer-breakthrough`](https://github.com/helexdev1004/afterquery-integrate-tracer-breakthrough) | Integrate tracer breakthrough curves from packed-column runs | Hydrology | 4 h | 4 h |
| [`name-released-lots`](https://github.com/helexdev1004/afterquery-name-released-lots) | Reproduce a genebank's lot-release practice from its day book | Biology | 4 h | 6 h |
| [`pick-coring-targets`](https://github.com/helexdev1004/afterquery-pick-coring-targets) | Select coring targets from a gradiometer survey | Geophysics | 4 h | 6 h |
| [`place-erosion-probes`](https://github.com/helexdev1004/afterquery-place-erosion-probes) | Recover height and substrate for each erosion probe | Geomorphology | 4 h | 5 h |
| [`project-facade-no2`](https://github.com/helexdev1004/afterquery-project-facade-no2) | Project roadside NO2 from the monitor to the building facade | Air Quality | 4 h | 3 h |
| [`settle-chronometer-trials`](https://github.com/helexdev1004/afterquery-settle-chronometer-trials) | Settle chronometer rates from trial observations | Physics | 4 h | 6 h |
| [`sort-bell-spectra`](https://github.com/helexdev1004/afterquery-sort-bell-spectra) | Recover bell identities from unlabelled partial spectra | Physics | 4 h | 9 h |
| [`sum-station-runoff`](https://github.com/helexdev1004/afterquery-sum-station-runoff) | Sum monthly runoff for a catchment water balance | Hydrology | 4 h | 4 h |

### Software

| Task | What it asks for | Field | Agent budget | Expert estimate |
| --- | --- | --- | --- | --- |
| [`ledger-rule-races`](https://github.com/helexdev1004/afterquery-ledger-rule-races) | Fix invariant-breaking races in a concurrent ledger service | Databases | 4 h | 6 h |
| [`port-report-queries`](https://github.com/helexdev1004/afterquery-port-report-queries) | Port reporting queries so they keep their original meaning | Databases | 4 h | 7 h |
| [`reckon-error-budgets`](https://github.com/helexdev1004/afterquery-reckon-error-budgets) | Compute error budgets for a platform review | Site Reliability | 4 h | 4 h |

### ML

| Task | What it asks for | Field | Agent budget | Expert estimate |
| --- | --- | --- | --- | --- |
| [`reckon-sweep-cost`](https://github.com/helexdev1004/afterquery-reckon-sweep-cost) | Cost a batch-size sweep to a target metric | Training Analysis | 4 h | 4 h |

### Operations

| Task | What it asks for | Field | Agent budget | Expert estimate |
| --- | --- | --- | --- | --- |
| [`locate-blowing-alarms`](https://github.com/helexdev1004/afterquery-locate-blowing-alarms) | Locate fibre blowing alarms along the duct run | Telecom Construction | 4 h | 5 h |
| [`number-lining-defects`](https://github.com/helexdev1004/afterquery-number-lining-defects) | Number tunnel lining defects by ring | Compliance | 4 h | 5 h |
| [`number-lining-defects-v5`](https://github.com/helexdev1004/afterquery-number-lining-defects-v5) | Number tunnel lining defects by ring (later revision) | Compliance | 4 h | 5 h |
| [`plan-inbound-pallets`](https://github.com/helexdev1004/afterquery-plan-inbound-pallets) | Assign pallet positions for next week's inbound deliveries | Warehouse Receiving | 4 h | 4 h |
| [`project-compressor-services`](https://github.com/helexdev1004/afterquery-project-compressor-services) | Project service due dates across a compressor house | Plant Maintenance | 4 h | 4 h |
| [`reckon-pellet-protein`](https://github.com/helexdev1004/afterquery-reckon-pellet-protein) | Predict expected protein for feed pellet samples | Feed Milling | 4 h | 5 h |
| [`reckon-resin-drying`](https://github.com/helexdev1004/afterquery-reckon-resin-drying) | Reconstruct resin drying time at each moulding shot | Plastics Manufacturing | 4 h | 5 h |
| [`reckon-section-earthworks`](https://github.com/helexdev1004/afterquery-reckon-section-earthworks) | Compute cut, fill and topsoil at road cross-sections | Highway Earthworks | 4 h | 6 h |
| [`tally-comfort-hours`](https://github.com/helexdev1004/afterquery-tally-comfort-hours) | Tally comfort hours for a service-charge rebate | Building Management | 4 h | 4 h |
| [`total-clerk-commission`](https://github.com/helexdev1004/afterquery-total-clerk-commission) | Total quarterly commission for the sales desk | Payroll Accounting | 4 h | 4 h |
| [`total-plan-traffic`](https://github.com/helexdev1004/afterquery-total-plan-traffic) | Total traffic served by each signal plan run | Traffic Engineering | 4 h | 5 h |
| [`trace-fabric-faults`](https://github.com/helexdev1004/afterquery-trace-fabric-faults) | Trace flagged fabric faults through to finished panels | Supply chain | 4 h | 6 h |
| [`trace-reject-reels`](https://github.com/helexdev1004/afterquery-trace-reject-reels) | Trace rejected sheets back to their paper reels | Carton Printing | 4 h | 4 h |
| [`trace-tanker-batches`](https://github.com/helexdev1004/afterquery-trace-tanker-batches) | Trace which pipeline batch filled each road tanker | Fuel Terminals | 4 h | 5 h |

### Hardware

| Task | What it asks for | Field | Agent budget | Expert estimate |
| --- | --- | --- | --- | --- |
| [`budget-rail-power`](https://github.com/helexdev1004/afterquery-budget-rail-power) | Size rail traction power against the board energy budget | Power Integrity | 4 h | 4 h |
| [`report-plate-inspection`](https://github.com/helexdev1004/afterquery-report-plate-inspection) | Write up a GD&T plate inspection from CMM runs | CAD | 4 h | 5 h |

Thirty-eight tasks across 5 domains, 191 hours of estimated expert work.

`number-lining-defects` and `number-lining-defects-v5` are two revisions of one task, kept side
by side so the change in how it was specified and graded stays visible.

## Reading these

In every repo, `tests/` and `solution/` hold the answers. To try a task honestly, read only
`instruction.md` and `environment/`.
