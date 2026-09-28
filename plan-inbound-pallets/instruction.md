Pallet positions for next week's inbound deliveries

A distribution centre books dock doors and racking a week ahead from its
suppliers' advance shipping notices. For each of forty-two notices the inbound
planner needs the number of cartons, the gross weight in kilograms and the
number of pallet positions the delivery will take. The notices come from six
suppliers' systems; the pack sizes, weights and pallet patterns come from the
centre's own item master.

`/app/RECEIVING.md` is the centre's note on how a notice is read, how units
make up inner packs, cartons and pallets, and how a delivery's weight and pallet
positions are worked out. The item master is `/app/item_master.csv`, the
notices are in `/app/asn/`, one file for each supplier, and the notices to plan
are listed in `/app/to_plan.txt`.

The plan is written to `/app/inbound_plan.csv` with the columns `asn`,
`cartons`, `gross_kg` and `pallets`, a line such as `S9-40417,112,1386.4,5`. A
line is right when cartons and pallets are exact and the weight is within 0.5
kg, and the planner will work from the file if no more than four of the
forty-two lines are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
