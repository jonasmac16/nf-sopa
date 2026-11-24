# General scientific-computing reference

Use for substantive scientific analysis regardless of domain.

## Establish scientific grain and design

- Identify the unit of observation and the unit of inference; they may differ.
- Preserve scientifically meaningful hierarchy such as subject -> sample -> replicate -> run/measurement.
- Establish paired, repeated, longitudinal, clustered, blocked, or batch structure before filtering, splitting, aggregation, or inference.
- Treat identifiers as scientific entities with semantics, not merely join keys.

## Separate kinds of correctness

Distinguish:

1. computational correctness: code performs the intended operations;
2. numerical correctness: algorithms/solvers approximate the intended quantities adequately;
3. statistical validity: assumptions and inferential procedure fit the design/data;
4. scientific validity: the computation supports the claimed scientific interpretation.

A successful execution or passing software test does not by itself establish scientific validity.

## Provenance and assumptions

- Version scientific reference resources that can change results.
- Keep units, coordinate/reference systems, transformations, normalization, and parameter conventions explicit.
- Make stochastic seeds and consequential algorithm parameters explicit.
- Separate exploratory choices from confirmatory/pre-specified analysis when that distinction matters.
- Record decisions that change scientific interpretation in `docs/DECISIONS.md`.
