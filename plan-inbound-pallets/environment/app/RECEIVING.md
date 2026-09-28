# Receiving: from a supplier's notice to pallet positions

## Notices

Each supplier sends an advance shipping notice for every delivery. `asn/` has
one file for each supplier, with a line for each item on each notice: the
notice number, the line number, the item's SKU as it stands in the item master,
and the quantity in single units.

The suppliers' systems were connected one at a time over several years. A file
that does not match this section is put into the form described here first;
every supplier's notices are planned.

## The item master

`item_master.csv` has, for every SKU, the supplier, `units_per_inner` (the
single units in one inner pack, the sealed pack the item comes in),
`inners_per_carton`, `inner_kg` (the gross weight of one inner pack),
`carton_tare_kg` (the weight of the empty carton) and `cartons_per_pallet`.

## Working a delivery out

For each line, the inner packs are the units divided by `units_per_inner`, and
the cartons are the inner packs divided by `inners_per_carton`, rounded up: a
part-filled carton is a carton. The line's weight is its inner packs times
`inner_kg` plus its cartons times `carton_tare_kg`.

A delivery's cartons and gross weight are the sums over its lines. Its pallet
positions are the sum over its lines of cartons divided by
`cartons_per_pallet`, rounded up to a whole number.
