# Esterase plates: how a day is worked up

The insectary screens field-caught mosquitoes for raised esterase activity, one
mosquito to a well.

## The plate

Each mosquito is ground in buffer and made up to a fixed volume. Homogenates
ground at the insectary are cleared in the centrifuge before plating; those
that come in ground from the field stations go on as they are. An aliquot of
each goes on a 96-well plate, the p-nitrophenyl acetate substrate is added to
the whole plate at once, and the reader follows the yellow of the
p-nitrophenol the esterases split from it, at 405 nm.

A plate has eighty homogenates, four blanks (buffer and substrate, no
homogenate) and twelve p-nitrophenol standards. The standards hold a known
amount of p-nitrophenol in the full well volume and no substrate.

The reader names a well by its place in the carriage, not by anything printed
on the plate. A plate goes into the carriage with its own A1 at the reader's
A1, and the day file's `layout` is the plate as it was made up.

## The day file

A day is one JSON object: `day`, and `plates`, a list. Each plate has

- `plate`, `reader`: labels.
- `mode`: what the reader exported. `absorbance` is optical density.
  `milli-absorbance` is optical density times a thousand. `transmittance` is
  per cent of light passed, and optical density is `-log10(T / 100)`.
- `time_unit`: `s` or `min`, the unit of `read_times`.
- `read_times`: when each read was taken, from the first read.
- `chamber_c`: the reader chamber temperature for the run, deg C.
- `layout`: by well, the role of the well: `blank`; `standard` with `nmol`, the
  p-nitrophenol in the well; or `sample` with `id`, the mosquito, `prep`,
  `spun` or `crude` as the homogenate was cleared or not, and `dilution`, how
  many times the aliquot goes into the whole homogenate.
- `reads`: by well, the reader's export, one value for every read time.

## The arithmetic

1. Turn every read into optical density.
2. A well's rate is the least-squares slope of its optical density against
   time, through all of its reads, in OD a minute.
3. The blank rate of a plate is the mean of the rates of its four blanks. It is
   taken off the rate of every sample on that plate.
4. OD per nmol for a plate is the least-squares slope, with an intercept, of the
   twelve standards' optical density (each standard's mean over its reads)
   against their nmol.
5. A sample's rate less the blank rate, over OD per nmol, is nmol a minute in
   the well. Times `dilution` it is nmol a minute for the whole mosquito.
6. Activity is reported at 25 C. The rate doubles for every ten degrees, so the
   figure is multiplied by `2 ** ((25 - chamber_c) / 10)`.

## What is reported

One line for every sample on the day, the mosquito and its activity in nmol a
minute at 25 C to two decimals, separated by a space:

    M-041207 38.61

The order of the lines does not matter.
