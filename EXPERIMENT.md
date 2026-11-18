# Experiment log

- 2026-11-18. Read the discrete-monitoring paper and froze the synthetic contract grid, replication counts, and timing design in Git.
- Ran the seeded 4,096-path pilot. Six unit checks passed, covering payoff discounting, continuous quadrature, discrete quadrature stability, distant barrier, time-zero knockout, and pathwise parity and order.
- Full run uses the frozen specifications. The calibrated runtime panel chooses method-specific path counts from each local machine's timing pilot. Performance may vary between runs.
- Reinstalled and reran the six tests, pilot and full study in a clean checkout with NumPy 2.4.1 after replacing the [yanked 2.4.0 pin](https://pypi.org/project/numpy/2.4.0/). The 74 fixed-path estimates matched exactly, as did the hidden-crossing and error-grid figures. Runtime varies with local conditions.
