# Sources and data dictionary

- Barrier correction for discrete monitoring. Broadie, Glasserman and Kou, 1997. See the paper’s theorem and shifted down-barrier convention. Accessed 2026-11-18. Link to publisher-hosted author copy. [Paper](https://www.columbia.edu/~mnb2/broadie/Assets/bgk_mf.pdf)
- Continuous monitoring. Rubinstein and Reiner, 1991, zero-rebate barrier options. Accessed 2026-11-18. The model uses the reflected Gaussian density. [Paper](https://digicoll.lib.berkeley.edu/record/86304/files/b120984374_C044481811.pdf)

The experiment uses synthetic contracts and innovations generated from seed 3107. No third-party observations or article copies are included. Rates and volatilities are annual decimals, maturities are in years, and prices and errors are US dollars per option on one share.

In estimates.csv, group identifies the main anchor grid, contract robustness grid, or separately calibrated runtime experiment. paths, steps, and replications are counts. reference is the matching continuous price. mean_price is the replication mean, bias is its signed difference from reference, mean_se is the average within-replication standard error and rmse is the square root of the mean squared price error across replications. median_seconds includes random number generation and estimator computation. benchmarks.txt records runtime environment and the continuous and discrete benchmarks.

The path illustration selects the first fine path generated from a separate seed that crosses on the fine grid while surviving all five displayed dates. It illustrates a mechanism rather than estimating its frequency.
