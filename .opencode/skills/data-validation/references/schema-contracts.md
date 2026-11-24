# Schema and identifier contracts

Check whichever are semantically relevant:

- expected fields/columns and types;
- identifiers and composite keys;
- key uniqueness at the intended grain;
- duplicated records;
- missing values and sentinel encodings;
- allowed categorical levels;
- numeric ranges and impossible values;
- units, time zones, encodings, and coordinate systems;
- expected grain (subject, visit, sample, trial, measurement, etc.).

Do not infer a dataset's grain from row count alone. Establish it from documented semantics and keys.
