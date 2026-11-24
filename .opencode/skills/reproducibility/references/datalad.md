# DataLad external-input workflow

Assume an external DataLad dataset is read-only unless the user explicitly requests modification.

1. Establish which path belongs to the dataset.
2. Inspect dataset/repository state before destructive or content-management operations.
3. Determine the revision identifying the input dataset.
4. Determine whether required annexed content is locally present.
5. Retrieve only missing files required by the current computation.
6. Run analysis without mutating the source dataset.
7. Report/record dataset source/path, revision, and relevant input paths when provenance matters.

Do not recursively `get` entire datasets by default. Do not `save`, `drop`, `uninstall`, remove, or commit within external input datasets without explicit authorization.
