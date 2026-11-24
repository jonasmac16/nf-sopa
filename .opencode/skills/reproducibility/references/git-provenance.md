# Git and provenance boundaries

Keep three identities distinct when they are separate:

1. analysis-code Git revision/worktree state;
2. external DataLad dataset revision/content availability;
3. Apptainer image identity and, if relevant, the revision of the separate container-definition repository.

A reproducible result may depend on all three. Do not commit external datasets or container repositories into the analysis project merely to capture their identities; record stable references instead.
