import re
from itertools import pairwise

import numpy as np
import pandas as pd


# pivots table into time series measuring features
def widen(df):
    wide = df.pivot_table(index='time', columns=["field", "robot_id"], values="value")
    wide.columns = wide.columns.map(lambda x: x[0] + "_" + str(x[1]))  # collapse multiindex
    wide.index = pd.to_datetime(wide.index, format="mixed")  # store as time series

    return wide


# derives velocity and acceleration from position
def robot_motion(wide_df):
    # for calculation of motion metrics, we linearly interpolate
    interpolate_fill = wide_df.interpolate(method="time")
    # calculates velocity
    position_columns = [col_name for col_name in interpolate_fill.columns if "f" not in col_name]
    positions = interpolate_fill[position_columns]  # extract position columns
    velocity = positions.apply(
        lambda p:
        p / positions.index.diff().total_seconds() * 1000,
        axis=0
    )  # velocity as position-delta/time, in mm/ms
    velocity.columns = ["v" + col_name for col_name in velocity.columns]  # vx_i, vy_i, vz_i
    # calculates acceleration, similar to above for velocity
    acceleration = velocity.apply(
        lambda v:
        v / velocity.index.diff().total_seconds() * 1000,
        axis=0
    )  # acceleration as velocity-delta/time, in mm/ms^2
    acceleration.columns = ["a" + col_name[1:] for col_name in acceleration.columns]  # ax_i, ay_i, az_i
    return velocity.join(acceleration)


# gets absolute metrics from vector metrics
def calculate_vectors(wide, motion, robot_ids):
    vector_lengths = pd.DataFrame()  # empty frame to store outputs

    # helper function for vector length, to avoid repeating code
    def vector_length(cols):
        return np.sqrt(  # euclidean vector size
            cols.apply(lambda x: x ** 2)  # run on all passed columns
            .sum(axis=1)
        )
    # runs on each provided robot id
    for r_id in robot_ids:
        v_columns_w_id = motion.filter(regex=f"v[xyz]_{str(r_id)}")  # extract velocity columns
        a_columns_w_id = motion.filter(regex=f"a[xyz]_{str(r_id)}")  # extract acceleration columns
        f_columns_w_id = wide.filter(regex=f"f[xyz]_{str(r_id)}")  # extract force columns
        # check for empty to avoid writing unnecessary columns
        if not v_columns_w_id.empty:
            vector_lengths[f"v_{str(r_id)}"] = vector_length(v_columns_w_id)  # v_i
        if not a_columns_w_id.empty:
            vector_lengths[f"a_{str(r_id)}"] = vector_length(a_columns_w_id)  # a_i
        if not f_columns_w_id.empty:
            vector_lengths[f"f_{str(r_id)}"] = vector_length(f_columns_w_id)  # f_i

    return vector_lengths


# runs main functions sequentially to produce supertable
def calculate_features(df):
    wide = widen(df)  # reshape data
    motion = robot_motion(wide)  # add velocity, acceleration
    vector_lengths = calculate_vectors(wide, motion, df["robot_id"].unique().tolist())  # get absolute sizes
    # produce a single supertable
    calculated = wide.join(motion).join(vector_lengths)
    return calculated.bfill()  # fills in remaining NaNs


# calculates total distance traveled by each robot
def distance_travelled(wide):
    distances = []
    # for each robot separately
    for i in range(2):  # i = 0, 1 for robot i+1 = 1, 2
        # extract all position columns e.g. (x_1, y_1 , z_1) for robot i+1 = 1, 2
        # this doesn't assume any such columns, but extracts any which we do have
        position_columns = list(filter(lambda s: re.match(f"[xyz]_{str(i+1)}", s), wide.columns))
        # produces a list of pairs of successive vectors
        # Nan entries will introduce errors, and add nothing useful, so we drop them
        calculate = pairwise(wide[position_columns].dropna().values)
        # sum the distance traveled between all pairs of successive points
        distances.append(sum([np.linalg.norm(b - a) for a, b in calculate]))

    return distances  # returns size 2 list of distance travelled for each robot
