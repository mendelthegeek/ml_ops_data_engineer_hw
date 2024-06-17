import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)

df = pd.read_parquet("./data/sample.parquet")

wide = df.pivot_table(index='time', columns=["field", "robot_id"], values="value")
wide.columns = wide.columns.map(lambda x: x[0] + "_" + str(x[1]))

wide.index = pd.to_datetime(wide.index, format="mixed")

interpolate_fill = wide.interpolate(method="time")

position_columns = [col_name for col_name in interpolate_fill.columns if "f" not in col_name]
positions = interpolate_fill[position_columns]

velocity = positions.apply(
    lambda p:
        p/positions.index.diff().total_seconds()*1000,
    axis=0
)
velocity.columns = ["v"+col_name for col_name in velocity.columns]

acceleration = velocity.apply(
    lambda v:
        v/velocity.index.diff().total_seconds()*1000,
    axis=0
)
acceleration.columns = ["a"+col_name[1:] for col_name in acceleration.columns]

for id in df["robot_id"].unique().tolist():
    v_columns_w_id = velocity.loc[:, velocity.columns.str.contains(str(id))]
    velocity[f"v_{str(id)}"] = np.sqrt(
        v_columns_w_id.apply(lambda x: x**2)
        .sum(axis=1)
    )
    a_columns_w_id = acceleration.loc[:, acceleration.columns.str.contains(str(id))]
    acceleration[f"a_{str(id)}"] = np.sqrt(
        a_columns_w_id.apply(lambda x: x**2)
        .sum(axis=1)
    )
    f_columns_w_id = interpolate_fill.filter(regex=f"f[xyz]_{str(id)}")
    interpolate_fill[f"f_{str(id)}"] = np.sqrt(
        f_columns_w_id.apply(lambda x: x**2)
        .sum(axis=1)
    )
calculated = interpolate_fill.join(velocity).join(acceleration).bfill()
print(calculated)