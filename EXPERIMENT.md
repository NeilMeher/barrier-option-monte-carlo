# Experiment log

- 2026-11-18. Read the discrete-monitoring paper and froze the synthetic contract grid, replication counts, and timing design in Git.
- Ran the seeded 4,096-path pilot. Six unit checks passed, covering payoff discounting, continuous quadrature, discrete quadrature stability, distant barrier, time-zero knockout, and pathwise parity and order.
- Full run uses the frozen specifications. The calibrated runtime panel chooses method-specific path counts from each local machine's timing pilot. Performance may vary between runs.
