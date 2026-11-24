# Output and regression validation

Before accepting an important derived output, check relevant invariants such as:

- expected row/entity count and grain;
- unique identifiers where required;
- expected columns/types/units;
- no new impossible/missing values unless intended;
- deterministic ordering only when downstream consumers require it;
- stable summary statistics for a known fixture/subset where appropriate.

For a data-processing bug, prefer a small fixture or executable assertion that reproduces the failure and protects against recurrence.
