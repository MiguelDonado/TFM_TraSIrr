- If we want to profile main.py, this should be put at the end

```py
    with cProfile.Profile() as profile:
        run()

    results = pstats.Stats(profile)
    results.sort_stats(pstats.SortKey.CUMULATIVE)
    results.print_stats("src/")
    # Save profile stats to a file
    filename = Path(config.network).stem
    results.dump_stats(PROFILING_DIR / f"{filename}.prof")
```