# GFW Tile Service
Raster and vector tile API for datasets in the [GFW Data API](https://github.com/wri/gfw-data-api) and Titiler dynamic tiling for raster assets in publicly accessible cloud storage.

## Developing
### Option 1: Developing against the Data API postgres database in one of the cloud environments (dev, staging or production):
* Make sure you have ssh access to the bastion host of the aws account (contact a
  Data API Engineering team member to get help with this).  Also, your host IP address
  (obtained by visiting `whatsmyip.com`) should be whitelisted for port 22 access in
  the gfw-production core-default security group (at
  `https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#SecurityGroups:`)

* Open an ssh tunnel connection to the database you'd like to connect to. For example, for the `staging` environment:

    ```ssh -i ~/.ssh/id_rsa -N -L 5432:application-autoscaling-698c9c01-db99-4430-a97a-6baaae853dc6.cljrqsduwhdo.us-east-1.rds.amazonaws.com:5432 ec2-user@{bastion_host}```

{bastion_host} might be something like: `ec2-18-215-196-0.compute-1.amazonaws.com`

* Set the environment variables for the **read only** credentials of the above database. The environment variables are `GFW_DB_NAME`,  `GFW_DB_USER_RO`, and `GFW_DB_PASSWORD_RO`. These are also listed in the `docker-compose.dev.yml` file. You get the values of secrets from the secrets manager of the appropriate AWS environment (production, staging, etc.)

* In `docker-compose.dev.yml`, set `DATA_LAKE_BUCKET`  to the desired environment's bucket name. By default, the `staging` environment bucket (`gfw-data-lake-staging`)  will be used.

* In `docker-compose.dev.yml`, set `AWS_DEFAULT_PROFILE` to your aws profile in `~/.aws` that will grant your dev instance access to the aws resources including the data lake bucket above in the aws account of the interest (contact a Data API Engineering team member to get an account).

* Run the start up script from the root directory:
```./scripts/develop```

You access the tile cache server at `localhost:8088` on your host.


NOTE: if you are developing on Linux (as opposed to MacOS), there can be a problem
accessing the host network, so `scripts/develop` will likely hang without being able
to access the database. If so, you can interrupt `scripts/develop` after it has built
the docker and gotten hung accessing the database. You can then start the docker by
hand via:

```docker run -it -p 127.0.0.1:8088:80 --entrypoint /bin/bash gfw-tile-cache-app:latest```

In that case, you will need to copy your `.ssh/id_rsa` and `.aws/credentials` files
into the docker and set all the needed environmental variables in the shell. You then
run the ssh tunnel from inside the docker via:

```ssh -i ~/.ssh/id_rsa -N -L 127.0.0.1:5432:gfw-aurora.cluster-ro-ch3jv7fz9pj1.us-east-1.rds.amazonaws.com:5432 "ec2-user@ec2-18-215-196-0.compute-1.amazonaws.com" &```

You can then start up the tile cache server in the docker via:

```/start-reload.sh &```


### Option 2: Developing against a local instance of Data API database

* Start dev instance of Data API locally using the instructions [here](https://github.com/wri/gfw-data-api?tab=readme-ov-file#run-locally-with-docker)

* Run the start up script from the root directory with the option to point to the local Data API:
```./scripts/develop --local_data_api```
