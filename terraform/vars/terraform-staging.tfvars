environment               = "staging"
log_level                 = "info"
tile_cache_url            = "staging-tiles.globalforestwatch.org"
desired_count             = 1
auto_scaling_min_capacity = 1
auto_scaling_max_capacity = 15
fargate_cpu               = 8192
fargate_memory            = 16384
data_lake_bucket_name     = "gfw-data-lake-staging"
