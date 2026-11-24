# Bioinformatics, genomics, and omics reference

## Biological identity and grain

- Distinguish subject, biological sample, aliquot, biological replicate, technical replicate, library, lane/run, cell, feature, and measurement where applicable.
- Do not split train/test or aggregate across levels in ways that leak information from the same biological subject or specimen unless scientifically intended.
- Validate identifier namespace and versioning (for example Ensembl IDs with/without version suffixes) before joins or annotation mapping.

## Reference resources

Record exact versions when results depend on them, including as applicable:

- reference genome/build and patch level;
- gene/transcript annotation release;
- transcriptome/proteome/database release;
- ontology/pathway/reference panel;
- aligner/index/database construction inputs.

Treat coordinate conventions as part of the schema: genome build, contig naming, strand, and 0/1-based or half-open/closed interval semantics can invalidate otherwise correct joins.

## Experimental structure and preprocessing

- Preserve batch, library preparation, sequencing technology, lane/run, paired-end/read-group, and other technical factors when relevant.
- Distinguish normalization or transformation needed for visualization/modeling from raw-scale quantities used by methods that model counts or other native distributions.
- Treat filtering, feature selection, and normalization performed using all samples as potential leakage when downstream validation/test sets are intended to be independent.
- For high-dimensional inference, consider multiple testing and the exact hypothesis family.

Do not interpret annotation absence, zero counts, or missing measurements as equivalent without evidence.
