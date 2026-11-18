import argparse
import csv
from dataclasses import dataclass, replace
from math import erfc, exp, log, pi, sqrt
from pathlib import Path
import platform
from time import perf_counter

import numpy as np
from figure import Plot

ROOT = Path(__file__).resolve().parent
SEED = 3107


@dataclass(frozen=True)
class Contract:
    spot: float = 100
    strike: float = 100
    barrier: float = 95
    rate: float = .03
    vol: float = .25
    maturity: float = 1

    def __post_init__(self):
        if min(self.spot, self.strike, self.barrier, self.vol, self.maturity) <= 0:
            raise ValueError("Spot, strike, barrier, volatility and maturity must be positive")

    @property
    def drift(self):
        return self.rate - self.vol ** 2 / 2


def normal(x):
    return erfc(-x / sqrt(2)) / 2


def continuous(c):
    if c.spot <= c.barrier:
        return 0.0
    variance = c.vol**2 * c.maturity
    initial = log(c.spot / c.barrier)
    cutoff = max(0, log(c.strike / c.barrier))
    drift = c.drift * c.maturity

    def truncated_call(mean):
        asset = c.barrier * exp(mean + variance / 2)
        return (asset * normal((mean + variance - cutoff) / sqrt(variance))
                - c.strike * normal((mean - cutoff) / sqrt(variance)))

    reflected = exp(-2 * c.drift * initial / c.vol**2)
    return exp(-c.rate * c.maturity) * (
        truncated_call(initial + drift) - reflected * truncated_call(-initial + drift)
    )


def integral_check(c, points=20001):
    if c.spot <= c.barrier:
        return 0.0
    initial = log(c.spot / c.barrier)
    variance = c.vol ** 2 * c.maturity
    mean = initial + c.drift * c.maturity
    grid = np.linspace(max(0, log(c.strike / c.barrier)), max(mean, 0) + 12 * sqrt(variance), points)
    density = np.exp(-(grid - mean) ** 2 / (2 * variance)) / sqrt(2 * pi * variance)
    survival = -np.expm1(-2 * initial * grid / variance)
    payoff = np.maximum(c.barrier * np.exp(grid) - c.strike, 0)
    return exp(-c.rate * c.maturity) * float(np.trapezoid(density * survival * payoff, grid))


def discrete_quadrature(c, steps, points):
    if c.spot <= c.barrier:
        return 0.0
    initial = log(c.spot / c.barrier)
    dt = c.maturity / steps
    variance = c.vol ** 2 * dt
    drift = c.drift * dt
    upper = initial + abs(c.drift * c.maturity) + 12 * c.vol * sqrt(c.maturity)
    dx = upper / points
    grid = (np.arange(points) + .5) * dx

    def transition(displacement):
        return np.exp(-(displacement - drift)**2 / (2 * variance)) * dx / sqrt(2 * pi * variance)

    kernel = transition(grid[None, :] - grid[:, None])
    density_mass = transition(grid - initial)
    for _ in range(1, steps):
        density_mass = density_mass @ kernel
    return exp(-c.rate * c.maturity) * float(density_mass @ np.maximum(c.barrier * np.exp(grid) - c.strike, 0))


def samples(c, innovations, method):
    if method not in {"grid", "bridge", "knock_in", "vanilla"}:
        raise ValueError(f"Unknown estimator {method}")
    steps = innovations.shape[1]
    variance = c.vol**2 * c.maturity / steps
    initial = log(c.spot / c.barrier)
    log_paths = initial + np.cumsum(c.drift * c.maturity / steps + sqrt(variance) * innovations, axis=1)
    payoff = exp(-c.rate * c.maturity) * np.maximum(c.barrier * np.exp(log_paths[:, -1]) - c.strike, 0)
    if method == "vanilla":
        return payoff
    clipped = np.maximum(log_paths, 0)
    if method == "grid":
        return payoff * ((initial > 0) & np.all(log_paths > 0, axis=1))
    previous = np.column_stack((np.full(len(log_paths), max(initial, 0)), clipped[:, :-1]))
    weight = np.prod(-np.expm1(-2 * previous * clipped / variance), axis=1)
    return payoff * (1 - weight if method == "knock_in" else weight)


def estimate(c, paths, steps, seed, methods):
    estimates = {name: [0.0, 0.0, 0.0] for name in methods}
    rng = np.random.default_rng(seed)
    for start in range(0, paths, 4096):
        batch = min(4096, paths-start)
        tick = perf_counter()
        innovations = rng.standard_normal((batch, steps))
        rng_seconds = perf_counter() - tick
        for name in methods:
            tick = perf_counter()
            values = samples(c, innovations, name)
            record = estimates[name]
            record[0] += float(values.sum())
            record[1] += float(values @ values)
            record[2] += perf_counter() - tick + rng_seconds
    return {name: (total/paths, sqrt(max(0, square-total**2/paths)/(paths-1)/paths), seconds)
            for name, (total, square, seconds) in estimates.items()}


def experiment(c, paths, steps, repetitions, cell, group, methods=("grid", "bridge")):
    rows = [estimate(c, paths, steps, [SEED, cell, rep], methods) for rep in range(repetitions)]
    benchmark = continuous(c)
    for method in methods:
        values, ses, seconds = np.array([row[method] for row in rows]).T
        errors = values - benchmark
        yield dict(group=group, method=method, barrier=c.barrier, volatility=c.vol, maturity=c.maturity,
                   paths=paths, steps=steps, replications=repetitions, reference=benchmark,
                   mean_price=float(values.mean()), bias=float(errors.mean()),
                   mean_se=float(ses.mean()), rmse=float(np.sqrt(np.mean(errors**2))),
                   median_seconds=float(np.median(seconds)))


def figures(c, rows, out):
    colors = {"grid": "#973e30", "bridge": "#166c77"}
    anchor = [row for row in rows if row["group"] == "anchor"]
    if anchor:
        max_paths = max(row["paths"] for row in anchor)
        selected = [row for row in anchor if row["paths"] == max_paths]
        ymax = max(row["rmse"] for row in selected) * 1.15
        for axis, filename in (("steps", "error-grid"), ("median_seconds", "error-runtime")):
            transform = np.log2 if axis == "steps" else float
            xmax = max(transform(row[axis]) for row in selected)
            plot = Plot("Synthetic barrier call", f"RMSE vs {'monitoring grid' if axis == 'steps' else 'runtime'} · {max_paths:,} paths per replication",
                        (0, xmax * 1.04), (0, ymax),
                        "Grid dates" if axis == "steps" else "Median seconds per replication", "RMSE (USD)",
                        x_ticks=[(transform(x), str(x)) for x in [1, 4, 16, 64, 256] if transform(x) <= xmax] if axis == "steps" else None)
            for label, color in colors.items():
                points = [(transform(row[axis]), row["rmse"]) for row in selected if row["method"] == label]
                plot.series(points, color, "Grid only" if label == "grid" else "Brownian bridge")
            plot.save(out / f"{filename}.svg")

    fine = 128
    rng = np.random.default_rng([SEED, 999])
    while True:
        log_path = np.r_[log(c.spot), log(c.spot) + np.cumsum(
            c.drift / fine + c.vol / sqrt(fine) * rng.standard_normal(fine))]
        path = np.exp(log_path)
        if min(path[::32]) > c.barrier and min(path) <= c.barrier:
            break
    plot = Plot("A crossing between observation dates", "Synthetic path · five sampled values lie above the barrier",
                (0, 1), (min(path) - 3, max(path) + 6), "Time (years)", "Spot (USD)")
    plot.series([(0, c.barrier), (1, c.barrier)], colors["grid"], "Barrier", dots=False)
    plot.series(list(zip(np.arange(fine+1)/fine, path)), colors["bridge"], "Fine path", dots=False)
    plot.series(list(zip(np.arange(0, fine+1, 32)/fine, path[::32])), "#172333", "Sampled dates", line=False)
    plot.save(out / "hidden-crossing.svg")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "report")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    c = Contract()
    groups = []
    if args.quick:
        groups = [(c, 4096, step, 4, "anchor") for step in (4, 32)]
    else:
        groups = [(c, paths, step, 10, "anchor")
                  for paths in (8192, 32768) for step in (1, 4, 16, 64, 256)]
        groups += [(replace(c, barrier=h, vol=v, maturity=t), 16384, 16, 8, "robustness")
                   for h in (85, 95, 99) for v in (.15, .25, .40) for t in (.25, 1, 2)]
    rows = []
    for cell, (contract, paths, steps, reps, group) in enumerate(groups):
        rows.extend(experiment(contract, paths, steps, reps, cell, group))
    if not args.quick:
        for method in ("grid", "bridge"):
            pilot = [estimate(c, 32768, 16, [SEED, 100, j], (method,))[method][2] for j in range(3)]
            paths = max(2, round(32768 * .10 / np.median(pilot)))
            rows.extend(experiment(c, paths, 16, 10, 110, "runtime_target", (method,)))

    steps = 16
    prices = [discrete_quadrature(c, steps, n) for n in ((300, 600) if args.quick else (600, 1200))]
    shift = c.barrier * exp(-.5826 * c.vol * sqrt(c.maturity / steps))
    benchmarks = {
        "continuous_analytic": continuous(c), "continuous_quadrature": integral_check(c),
        "discrete_coarse": prices[0], "discrete_fine": prices[1],
        "discrete_bgk_shift": continuous(replace(c, barrier=shift)),
    }
    with (out / "estimates.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    (out / "benchmarks.txt").write_text(
        f"Python {platform.python_version()}, NumPy {np.__version__}, {platform.platform()}\n"
        + "\n".join(f"{k}={v:.8f}" for k, v in benchmarks.items()) + "\n", encoding="utf-8"
    )
    figures(c, rows, out)
    print((out / "benchmarks.txt").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
