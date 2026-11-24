# Biostatistics and experimental-design reference

## Design and inference

- Identify the experimental unit, observational unit, and inferential unit.
- Account for pairing, repeated measures, clustering, blocking, stratification, batch, censoring, and longitudinal structure where present.
- Do not treat correlated measurements as independent merely because they occupy separate rows.
- Keep randomization, matching, inclusion/exclusion, and pre-specified contrasts visible when they affect validity.

## Modeling

- Check assumptions relevant to the chosen model rather than applying generic diagnostics mechanically.
- Make missing-data handling and its assumptions explicit.
- Report scientifically interpretable effect sizes and uncertainty, not only thresholded p-values.
- For multiple hypotheses, define the hypothesis family and correction/error-rate procedure explicitly.
- Distinguish exploratory model/feature selection from confirmatory inference when applicable.

## Validation and leakage

When fitting predictive/statistical procedures, preprocessing and resampling must respect the independent unit of evaluation. Imputation, normalization, feature selection, tuning, or batch correction can leak information if estimated using held-out units.
