import pandas as pd
import ETL

pd.set_option('display.max_columns', None)

df = pd.read_parquet("./data/sample.parquet")

output = ETL.calculate_features(df)

output.to_csv("./output/sample.csv")