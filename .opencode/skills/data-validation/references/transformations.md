# Transformation checks

## Filters

- Record count before/after meaningful filters.
- Which identifiers were removed and whether removal is expected.
- Missing-value behavior in predicates.

## Joins

Before joining, identify intended keys and relationship: one-to-one, one-to-many, many-to-one, or intentionally many-to-many.

Check key uniqueness appropriate to that relationship, unmatched keys on both sides where relevant, and row count after the join. Treat unexpected many-to-many behavior or unexplained row multiplication as a likely bug.

## Grouping/aggregation

Verify grouping variables, number of groups, missing-value behavior, weighting/units, and expected output grain. Ensure grouping state does not accidentally leak into later operations.

## Reshaping

Verify identifier columns, name/value mapping, duplicate cells, ordering assumptions, and output grain after pivot/widen/stack/unstack operations.
