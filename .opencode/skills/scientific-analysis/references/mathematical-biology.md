# Mathematical biology reference

## Model specification

- Make equations, state variables, parameters, initial/boundary conditions, units, and parameter domains explicit.
- Check dimensional consistency where quantities carry physical or biological units.
- Distinguish fitted, fixed, measured, assumed, and literature-derived parameters.
- Consider structural/practical identifiability before interpreting fitted parameter values biologically.

## Numerical validity

For ODE/PDE/stochastic/optimization/simulation work, record consequential choices such as:

- solver/algorithm;
- absolute and relative tolerances;
- step-size, mesh, discretization, event handling, or convergence criteria;
- stiffness handling;
- random seed and ensemble size for stochastic methods.

Test whether scientific conclusions are stable to reasonable solver/tolerance/discretization changes when numerical error could matter.

## Scientific interpretation

- Check expected invariants, conservation laws, positivity/bounds, equilibria, or limiting behavior where the model implies them.
- Distinguish a numerical artifact from a model prediction.
- Use sensitivity/uncertainty analysis when conclusions depend on poorly constrained parameters.
- Do not interpret parameter estimates beyond what the data/model can identify.
