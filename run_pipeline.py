import os
import sys

import pandas as pd
import ETL

if len(sys.argv) > 1:
    mode = (sys.argv[1])
else:
    mode = ""

pd.set_option('display.max_columns', None)
# reads in data
df = pd.read_parquet("./data/sample.parquet")
# setup to store runtime stats
runtime_stats = pd.DataFrame(columns=[
    "uuid",
    "start",
    "end",
    "runtime",
    "distance_1",
    "distance_2",
    "total_distance"
])
runtime_stats.set_index("uuid", inplace=True)
runs_by_uuid = dict(tuple(df.groupby('run_uuid')))

# run analysis on each uuid run
for uuid, run in runs_by_uuid.items():
    # ensure output dir exists
    outdir = f"./output/{uuid}"
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    if mode == "separate":
        # pivot, interpolate, and derive feature
        wide = ETL.widen(run)
        motion = ETL.robot_motion(wide)
        vector_lengths = ETL.calculate_vectors(wide, motion, df["robot_id"].unique().tolist())
        # write results into separate csvs
        wide.to_csv(outdir + "/wide.csv")
        motion.to_csv(outdir + "/motion.csv")
        vector_lengths.to_csv(outdir + "/vector_lengths.csv")

    elif mode == "full":
        ETL.calculate_features(run).to_csv(outdir+"/full.csv")

    wide = ETL.widen(run)
    # derive runtime stats
    start = wide.index.min()
    end = wide.index.max()
    distance_1, distance_2 = ETL.distance_travelled(wide)
    # append runtime stats
    runtime_stats.loc[uuid] = [
        start,
        end,
        end - start,
        distance_1,
        distance_2,
        distance_1 + distance_2
    ]
# write runtime stats
runtime_stats.to_csv("./output/runtime_stats.csv")
