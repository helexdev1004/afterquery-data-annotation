# Answering a request from the store

The store holds seed in lots. Every lot belongs to one accession, and every
accession has a germination standard of its own, given with the campaign. A
campaign is the store's day book: a list of events in the order they happened,
each stamped with the day it happened on, counted from the first day of the
campaign.

Your program is given one campaign and answers every request in it.

## The lots

A lot is known by its name. It holds a number of seeds, and it carries the
result of the last germination test made on it, as a whole percentage, with the
day that test was made.

## The events

**DEPOSIT** puts a new lot in the store, with its accession, the seeds it holds
and the germination figure it came in with. That figure is a test made on the
day of the deposit.

**TEST** records a germination test on a lot: the figure, on the day of the
event.

**SPLIT** takes a named number of seeds out of a parent lot and makes a new lot
of them, under the same accession. The parent keeps what is left.

**TOPUP** moves a named number of seeds out of one lot into another lot of the
same accession. The lot that receives them ends up with a germination figure
that stands for what it now holds: the two figures weighted by the seeds each
part brings, rounded to a whole percentage.

**REGEN** grows a lot out and puts the harvest in the store as a new lot, with
its own seeds and its own germination figure, tested on the day of the event.
The harvest is new seed and stands on its own figure. The lot that was grown
out is finished with and is no longer part of the store, whatever it still
holds.

**WITHDRAW** takes seeds out of a lot and out of the store.

**DISCARD** takes a lot out of the store.

**REQUEST** asks, for one accession, on the day of the event: which lot does
the store release? The name of that lot is the answer, one line for each
request, in the order they come. If the store has nothing it can release for
that accession that day, the answer is a single `-`.

## Holds

The standard is what the accession's seed is expected to germinate at. A
germination test that falls short of the standard puts the lot it was made on
under hold, and a later test on that lot that meets the standard lifts it
again. Seed under hold is not released.

## Which lot the store releases

A lot can be released on the day of a request when all of these hold:

* it belongs to the accession asked for;
* it is still part of the store;
* it holds at least 100 seeds;
* it is not under hold;
* its germination test is current, which it is for 365 days after the day it
  was made.

**The store turns over its stock: of the lots it can release, it releases the
oldest seed.** Where two would be equally old, it takes the one whose name
comes first.

## What this note does not decide

The store has never written these down, and they are left to you. The worked
campaigns settle every one of them - not singly, but by having to come out
right all together.

1. Whether a lot holding exactly the hundred seeds may be released.
2. Whether a lot split off carries the date of the test it inherits, or is
   treated as tested on the day of the split.
3. Whether a test recorded on the day of a request is in effect for that
   request.
4. Whether a lot that has been grown out can still be released while it holds
   seed.
5. What the date of the germination test becomes for a lot that is topped up.

## The worked campaigns

`worked.json` holds fourteen campaigns of the same kind as the ones your
program will be given, each with the answer the store gave to every request in
it. They are there to be reproduced. A reading of this note that reproduces all
fourteen is the reading the store works to.
