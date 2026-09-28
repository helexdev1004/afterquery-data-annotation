# AfterQuery — data annotation for AI evaluation

Thirty-eight **harbor-format benchmark tasks** written for the AfterQuery Experts programme.

This is data annotation of a particular kind. There is no labelling queue and no rubric to tick
through: each item is a complete, self-contained piece of professional work, packaged so that a
frontier AI agent can attempt it unaided and a program can decide, without a human in the loop,
whether it actually got the job done.

Every task supplies four things:

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

## Layout

```
<task>/
  instruction.md          the brief — the only thing the agent is told
  task.toml               artifacts, timeouts, resources, metadata
  environment/            Dockerfile and data for the agent's container
  solution/solve.sh       reference solution; scores 1 by construction
  tests/                  verifier image, grading logic and ground truth
  cheat/                  optional: a deliberate cheating attempt, never executed
```

## Running one

With [harbor](https://github.com/laude-institute/harbor) installed and Docker running:

```bash
uv tool install harbor

cd geodetic-network-adjust
harbor run -p . -a oracle -e docker   # reference solution — must score 1
harbor run -p . -a nop    -e docker   # nothing happens    — must score 0
```

## The tasks
### Science

| Task | What it asks for | Field | Expert hours |
| --- | --- | --- | --- |
| [`assign-find-contexts`](assign-find-contexts/) | Assign excavation finds to their stratigraphic contexts | Archaeology | 7 |
| [`bed-lake-samples`](bed-lake-samples/) | Attribute lake sediment samples to their source beds | Geology | 5 |
| [`calibrate-plot-moisture`](calibrate-plot-moisture/) | Calibrate TDR and capacitance probes to volumetric water content | Soil Physics | 3 |
| [`certify-piece-soaks`](certify-piece-soaks/) | Derive soak times for heat-treatment certificates | Heat Treatment | 4 |
| [`connect-borough-drains`](connect-borough-drains/) | Resolve the downstream manhole for each borough drain | Engineering | 7 |
| [`derive-trout-respiration`](derive-trout-respiration/) | Work up intermittent-flow respirometry into SMR and RMR | Biology | 4 |
| [`esterase-assay-workup`](esterase-assay-workup/) | Work up 96-well esterase screens into per-mosquito activity | Biology | 5 |
| [`gauge-blast-vibration`](gauge-blast-vibration/) | Extract peak vertical ground velocity from a quarry blast | Seismology | 3 |
| [`geodetic-network-adjust`](geodetic-network-adjust/) | Least-squares adjustment of an unfamiliar geodetic network | Earth | 6 |
| [`grade-pulled-boards`](grade-pulled-boards/) | Grade sawn oak boards against the visual grading rules | Engineering | 7 |
| [`integrate-tracer-breakthrough`](integrate-tracer-breakthrough/) | Integrate tracer breakthrough curves from packed-column runs | Hydrology | 4 |
| [`name-released-lots`](name-released-lots/) | Reproduce a genebank's lot-release practice from its day book | Biology | 6 |
| [`pick-coring-targets`](pick-coring-targets/) | Select coring targets from a gradiometer survey | Geophysics | 6 |
| [`place-erosion-probes`](place-erosion-probes/) | Recover height and substrate for each erosion probe | Geomorphology | 5 |
| [`project-facade-no2`](project-facade-no2/) | Project roadside NO2 from the monitor to the building facade | Air Quality | 3 |
| [`settle-chronometer-trials`](settle-chronometer-trials/) | Settle chronometer rates from trial observations | Physics | 6 |
| [`sort-bell-spectra`](sort-bell-spectra/) | Recover bell identities from unlabelled partial spectra | Physics | 9 |
| [`sum-station-runoff`](sum-station-runoff/) | Sum monthly runoff for a catchment water balance | Hydrology | 4 |

### Software

| Task | What it asks for | Field | Expert hours |
| --- | --- | --- | --- |
| [`ledger-rule-races`](ledger-rule-races/) | Fix invariant-breaking races in a concurrent ledger service | Databases | 6 |
| [`port-report-queries`](port-report-queries/) | Port reporting queries so they keep their original meaning | Databases | 7 |
| [`reckon-error-budgets`](reckon-error-budgets/) | Compute error budgets for a platform review | Site Reliability | 4 |

### ML

| Task | What it asks for | Field | Expert hours |
| --- | --- | --- | --- |
| [`reckon-sweep-cost`](reckon-sweep-cost/) | Cost a batch-size sweep to a target metric | Training Analysis | 4 |

### Operations

| Task | What it asks for | Field | Expert hours |
| --- | --- | --- | --- |
| [`locate-blowing-alarms`](locate-blowing-alarms/) | Locate fibre blowing alarms along the duct run | Telecom Construction | 5 |
| [`number-lining-defects`](number-lining-defects/) | Number tunnel lining defects by ring | Compliance | 5 |
| [`number-lining-defects-v5`](number-lining-defects-v5/) | Number tunnel lining defects by ring (later revision) | Compliance | 5 |
| [`plan-inbound-pallets`](plan-inbound-pallets/) | Assign pallet positions for next week's inbound deliveries | Warehouse Receiving | 4 |
| [`project-compressor-services`](project-compressor-services/) | Project service due dates across a compressor house | Plant Maintenance | 4 |
| [`reckon-pellet-protein`](reckon-pellet-protein/) | Predict expected protein for feed pellet samples | Feed Milling | 5 |
| [`reckon-resin-drying`](reckon-resin-drying/) | Reconstruct resin drying time at each moulding shot | Plastics Manufacturing | 5 |
| [`reckon-section-earthworks`](reckon-section-earthworks/) | Compute cut, fill and topsoil at road cross-sections | Highway Earthworks | 6 |
| [`tally-comfort-hours`](tally-comfort-hours/) | Tally comfort hours for a service-charge rebate | Building Management | 4 |
| [`total-clerk-commission`](total-clerk-commission/) | Total quarterly commission for the sales desk | Payroll Accounting | 4 |
| [`total-plan-traffic`](total-plan-traffic/) | Total traffic served by each signal plan run | Traffic Engineering | 5 |
| [`trace-fabric-faults`](trace-fabric-faults/) | Trace flagged fabric faults through to finished panels | Supply chain | 6 |
| [`trace-reject-reels`](trace-reject-reels/) | Trace rejected sheets back to their paper reels | Carton Printing | 4 |
| [`trace-tanker-batches`](trace-tanker-batches/) | Trace which pipeline batch filled each road tanker | Fuel Terminals | 5 |

### Hardware

| Task | What it asks for | Field | Expert hours |
| --- | --- | --- | --- |
| [`budget-rail-power`](budget-rail-power/) | Size rail traction power against the board energy budget | Power Integrity | 4 |
| [`report-plate-inspection`](report-plate-inspection/) | Write up a GD&T plate inspection from CMM runs | CAD | 5 |

`number-lining-defects` and `number-lining-defects-v5` are two revisions of one task, kept side by
side so the change in how it was specified and graded stays visible.

## Reading these

`tests/` and `solution/` hold the answers. To try a task honestly, read only `instruction.md`
and `environment/`.

