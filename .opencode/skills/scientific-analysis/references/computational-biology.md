# Computational and systems biology reference

## Biological structure

- Identify the biological entity and scale represented by each state, feature, node, interaction, or observation.
- Preserve subject/sample/condition/time/replicate structure through model fitting and validation.
- Treat pathway, interaction, regulatory, or ontology databases as versioned scientific inputs rather than timeless truth.

## Predictive and data-driven models

- Split validation/test data at the scientifically independent unit, often subject or biological specimen rather than row.
- Prevent feature engineering, normalization, imputation, selection, or hyperparameter choices from learning from held-out biological units.
- Separate predictive performance from mechanistic or causal interpretation unless the design supports the stronger claim.

## Simulation and systems models

- Record model equations/structure, parameter sources, initial conditions, perturbations, seeds, and simulation settings that affect conclusions.
- Check sensitivity to uncertain parameters and biologically plausible ranges where conclusions depend on them.
- Distinguish qualitative robustness from a single nominal simulation trajectory.
