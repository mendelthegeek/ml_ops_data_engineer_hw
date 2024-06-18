import pandas as pd
import ETL

pd.set_option('display.max_columns', None)

df = pd.read_parquet("./data/sample.parquet")

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