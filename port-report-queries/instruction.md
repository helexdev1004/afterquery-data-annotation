# The reporting queries don't mean the same thing any more

We've moved the nightly reporting off MySQL onto PostgreSQL 15. The schema went
across fine, and someone had already put the query set through a transpiler, so
everything in `/app/queries` is valid PostgreSQL - all twenty-four parse, run
against the new schema, and come back with rows. Nothing errors. Nothing looks
broken.

The trouble is they don't all return what they used to. The transpiler did the
syntax and left the meaning alone, and the two servers don't agree about what
some of these expressions do. I got caught by two of them already and I'd rather
not guess at the rest.

What I need is every query giving back what its MySQL original gave back. Leave
the corrected set in `/app/ported/` - one file per query, the same twenty-four
filenames as in `/app/queries`.

What's here to work with:

- `/app/queries/*.sql` - the transpiled set, where you're starting from
- `/app/expected/*.tsv` - what each query returned on the old server, for the
  data that's loaded here. Tab separated, header row, `NULL` printed for a null.
- `/app/schema.sql` - the schema as the migration built it
- `reports-up` starts the database, `reports-up --reseed` puts the data back the
  way it shipped
- `psql "$DATABASE_URL"` is installed and `DATABASE_URL` is already set

Three things worth being clear about before you start.

The data in this box is not the data I'm checking against. I run your queries
over a second extract with the same schema that isn't in here, so `/app/expected`
is the answer sheet for the extract you've got and for nothing else. I check both
of them, and at least 22 of the 24 have to come back right on each.

I compare the whole result set, in order. Numbers compare as numbers, so trailing
zeros don't matter to me. Text has to match exactly. A null is not an empty
string.

The old server isn't installed here. You've got the network, so stand one up and
test against it if that's how you'd rather work - I don't mind how you get there,
only whether the numbers come back right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
