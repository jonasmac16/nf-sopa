---
name: data-validation
description: Validate structured/tabular data transformations and debug suspicious analysis results. Use when loading, filtering, joining, grouping, aggregating, reshaping, converting, or writing data where schema, identifiers, missingness, cardinality, ranges, units, or row-count invariants affect correctness.
---

# Data validation workflow

Treat important transformations as operations with explicit preconditions and postconditions.

1. Establish the smallest representative input that can exercise the transformation.
2. Inspect relevant schema/type/key/missingness assumptions before the operation.
3. Validate record counts and key behavior across filters, joins, reshapes, and aggregations.
4. Investigate unexpected data loss, multiplication, coercion, or missingness rather than silently accepting it.
5. Validate output contracts before writing/using downstream results.
6. For a bug fix, add a focused regression assertion/test when practical.

Load references only as needed:

- schemas and identifiers: `references/schema-contracts.md`
- joins/filters/grouping: `references/transformations.md`
- outputs/regression checks: `references/output-validation.md`
