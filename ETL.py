import re
from itertools import pairwise

import numpy as np
import pandas as pd


def widen(df):
    wide = df.pivot_table(index='time', columns=["field", "robot_id"], values="value")
    wide.columns = wide.columns.map(lambda x: x[0] + "_" + str(x[1]))
    wide.index = pd.to_datetime(wide.index, format="mixed")

    return wide


def robot_motion(wide_df):
    interpolate_fill = wide_df.interpolate(method="time")

    position_columns = [col_name for col_name in interpolate_fill.columns if "f" not in col_name]
    positions = interpolate_fill[position_columns]
    velocity = positions.apply(
        lambda p:
        p / positions.index.diff().total_seconds() * 1000,
        axis=0
    )
    velocity.columns = ["v" + col_name for col_name in velocity.columns]

    acceleration = velocity.apply(
        lambda v:
        v / velocity.index.diff().total_seconds() * 1000,
        axis=0
    )
    acceleration.columns = ["a" + col_name[1:] for col_name in acceleration.columns]
    return velocity.join(acceleration)


def calculate_vectors(wide, motion, robot_ids):
    vector_lengths = pd.DataFrame()

    def vector_length(cols):
        return np.sqrt(
            cols.apply(lambda x: x ** 2)
            .sum(axis=1)
        )

    for r_id in robot_ids:
        v_columns_w_id = motion.filter(regex=f"v[xyz]_{str(r_id)}")
        a_columns_w_id = motion.filter(regex=f"a[xyz]_{str(r_id)}")
        f_columns_w_id = wide.filter(regex=f"f[xyz]_{str(r_id)}")
        vector_lengths[f"v_{str(r_id)}"] = vector_length(v_columns_w_id)
        vector_lengths[f"a_{str(r_id)}"] = vector_length(a_columns_w_id)
        vector_lengths[f"f_{str(r_id)}"] = vector_length(f_columns_w_id)

    return vector_lengths


def calculate_features(df):
    wide = widen(df)

    motion = robot_motion(wide)

    vector_lengths = calculate_vectors(wide, motion, df["robot_id"].unique().tolist())

    calculated = wide.join(motion).join(vector_lengths)
    return calculated.bfill()


def distance_traveled(wide):

    position_columns_1 = list(filter(lambda s: re.match("[xyz]_1", s), wide.columns))
    calculate = pairwise(wide[position_columns_1].dropna().values)
    distance_1 = sum([np.linalg.norm(b - a) for a, b in calculate])

    position_columns_2 = list(filter(lambda s: re.match("[xyz]_2", s), wide.columns))
    calculate = pairwise(wide[position_columns_2].dropna().values)
    distance_2 = sum([np.linalg.norm(b - a) for a, b in calculate])

    return distance_1, distance_2
