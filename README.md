# GFW Tile Service
Raster and vector tile API for datasets in the [GFW Data API](https://github.com/wri/gfw-data-api) and Titiler dynamic tiling for raster assets in publicly accessible cloud storage.

## Developing
### Option 1: Developing against the Data API postgres database in one of the cloud environments (dev, staging or production):
* Make sure you have ssh access to the bastion host of the aws account (contact a Data API Engineering team member to get help with this).

* Open ssh tunnel connection to the database you'd like to connect to. For example, for the `staging` environment:

    ```ssh -i ~/.ssh/id_rsa -N -L 5432:application-autoscaling-698c9c01-db99-4430-a97a-6baaae853dc6.cljrqsduwhdo.us-east-1.rds.amazonaws.com:5432 ec2-user@gfw-staging```

* Set the environment variables for the **read only** credentials of the above database. The environment variables are `GFW_DB_NAME`,  `GFW_DB_USER_RO` and `GFW_DB_PASSWORD_RO`. These are also listed in the `docker-compose.dev.yml` file.

* In `docker-compose.dev.yml`, set `DATA_LAKE_BUCKET`  to the desired environment's bucket name. By default, the `staging` environment bucket (`gfw-data-lake-staging`)  will be used.

* In `docker-compose.dev.yml`, set `AWS_DEFAULT_PROFILE` to your aws profile in `~/.aws` that will grant your dev instance access to the aws resources including the data lake bucket above in the aws account of the interest (contact a Data API Engineering team member to get an account).

* Run the start up script from the root directory:
```./scripts/develop```

### Option 2: Developing against a local instance of Data API database

* Start dev instance of Data API locally using the instructions [here](https://github.com/wri/gfw-data-api?tab=readme-ov-file#run-locally-with-docker)

* Run the start up script from the root directory with the option to point to the local Data API:
```./scripts/develop --local_data_api```