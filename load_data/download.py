import os
import boto3
from load_data.load_data import load
from load_data.post_processing import cli

s3 = boto3.client("s3")

for i in range(0, 300):

    prefix = f"geotrellis/results/firealerts_gadm_2020-03-23/2020-03-23/fireAlerts_20200323_1934/all/part-00{str(i).zfill(3)}-fda1eafb-2d6e-42df-8b12-eb71454eba0f-c000.csv"
    output = f"viirs_{i}.csv"
    s3.download_file("gfw-pipelines-devE", prefix, output)
    print(f"Download and load {prefix}")
    load(output)
    os.remove(output)

print("DONE loading")
print("Start postprocessing")
cli()
