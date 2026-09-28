A seed genebank keeps its movements in a day book and answers requests for material out of it. A campaign is one such book: seed deposited, germination tests recorded, lots split, lots topped up out of one another, lots grown out again, seed withdrawn and lots discarded, all set down in the order they happened. Among them are requests, each naming an accession and a day, and for every request the store releases one of its lots. Which lot it releases is the question here, and the store's practice has to be reproduced as a program rather than worked out by hand.

The program goes at `/app/releases.py`. It is run as `python3 /app/releases.py` with one campaign as JSON on standard input, and for every request in that campaign, in the order the requests come, it prints one line: the name of the lot the store releases, or a single `-` if the store has nothing it can release for that accession on that day.

`/app/GENEBANK.md` is the store's own note. It says what each kind of event does to the lots, what puts a lot under hold and lifts it again, and which of its lots the store can release on a given day. It is candid about the handful of matters the store has never written down, and leaves those to you. `/app/worked.json` holds fourteen worked campaigns of the same kind, each carrying the name the store itself gave to every request in it.

The program is marked by being run on campaigns it has not seen. Each request is worth ten points when the line printed for it names the lot the store released, and the work is accepted at 2790 points out of a possible 2890.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
