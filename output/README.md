# output/

Generated output from simulation runs, written here automatically when a run reaches
`completed` status (see `application/handlers/command/execute_simulation_run_handler.py`
and `infrastructure/csv_position_log_file_writer.py` /
`infrastructure/csv_passenger_stats_file_writer.py`).

One subdirectory per run, named by run id:

```
output/
  <run-id>/
    position_log.csv       # required output 1 — wide format, one row per tick
    passenger_stats.csv    # required output 2 — min/max/avg wait_time and total_time
```

This directory and this file are checked into the repo so the expected output location is
discoverable without running anything first. The generated `<run-id>/` subdirectories and
their `.csv` files are not — they're transient, regenerated on every run, and gitignored.
