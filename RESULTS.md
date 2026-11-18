# Results

For the synthetic anchor, the analytical continuous down-and-out call price was $5.02941643. Direct integration of the conditional survival payoff gave $5.02941640. At 32,768 paths, the grid-only method had an upward mean error of $2.46 on 16 dates and $0.69 on 256 dates. Brownian-bridge RMSE was $0.078 and $0.044 at those grids. The residual signed errors vary with random draws. Brownian-bridge conditional survival removes missed-crossing bias under the assumed GBM, while simulation noise remains.

| Separate 16-date runtime experiment | Paths | Median seconds | Signed mean error | RMSE |
|---|---:|---:|---:|---:|
| Grid only | 265,560 | 0.097 | +$2.429 | $2.429 |
| Brownian bridge | 161,181 | 0.108 | −$0.035 | $0.045 |

Runtimes include innovations and estimator processing. Each method was calibrated independently to a 0.10-second budget, and realized medians differ. The runtime figure traces the main grid experiment with fixed path counts. The table uses the separate fixed-budget experiment.

The 16-date contract was worth $7.48632 using 1,200-node quadrature versus $7.48758 using 600. Lowering the continuous barrier by the Broadie–Glasserman–Kou shift gave $7.43100, about $0.055 below the refined discrete estimate. A residual of this order is larger than the observed quadrature refinement difference. The discrete contract pays on paths that cross the barrier between dates and subsequently recover.

These estimates apply to the stated synthetic contracts and assume exact GBM log transitions, a constant barrier and no rebate. The robustness cells in [estimates.csv](report/estimates.csv) vary barrier, volatility and maturity, and report simulation uncertainty separately from numerical monitoring error.
