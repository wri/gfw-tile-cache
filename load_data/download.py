import os
import boto3

from load_data import create_table
from load_data import seed
from load_data import post_processing

s3 = boto3.client("s3")


def cli():
    create_table.cli()

    for i in range(0, 300):
        prefix = f"geotrellis/results/firealerts_gadm_2020-03-23/2020-03-23/fireAlerts_20200323_1934/all/part-00{str(i).zfill(3)}-fda1eafb-2d6e-42df-8b12-eb71454eba0f-c000.csv"
        output = f"viirs_{i}.csv"
        s3.download_file("gfw-pipelines-dev", prefix, output)
        print(f"Download and load {prefix}")
        seed.load(output)
        os.remove(output)

    print("DONE loading")
    print("Start postprocessing")
    post_processing.cli()


if __name__ == "__main__":
    cli()
