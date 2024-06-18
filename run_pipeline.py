import pandas as pd
import ETL

pd.set_option('display.max_columns', None)

df = pd.read_parquet("./data/sample.parquet")

wide = ETL.widen(df)
motion = ETL.robot_motion(wide)
vector_lengths = ETL.calculate_vectors(wide, motion, df["robot_id"].unique().tolist())

wide.to_csv("./output/wide.csv")
motion.to_csv("./output/motion.csv")
vector_lengths.to_csv("./output/vector_lengths.csv")

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

for uuid, run in runs_by_uuid.items():
    formatted = ETL.widen(run)
    start = formatted.index.min()
    end = formatted.index.max()
    distance_1, distance_2 = ETL.distance_traveled(formatted)
    runtime_stats.loc[uuid] = [
        start,
        end,
        end - start,
        distance_1,
        distance_2,
        distance_1 + distance_2
    ]

runtime_stats.to_csv("./output/runtime_stats.csv")