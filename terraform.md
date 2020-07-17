## Requirements

| Name | Version |
|------|---------|
| terraform | >=0.12.26 |
| aws | ~> 2.65.0 |

## Providers

| Name | Version |
|------|---------|
| aws | ~> 2.65.0 |
| template | n/a |
| terraform | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| auto\_scaling\_cooldown | Time in seconds to pass before scaling up or down again. | `number` | `300` | no |
| auto\_scaling\_max\_capacity | Minimum number of tasks to deploy when scaling up. | `number` | n/a | yes |
| auto\_scaling\_max\_cpu\_util | CPU usage percentage which will trigger autoscaling event. | `number` | `75` | no |
| auto\_scaling\_min\_capacity | Minimum number of tasks to keep when scaling down. | `number` | n/a | yes |
| container\_name | Description of tile service app container image. | `string` | `"gfw-tile-cache"` | no |
| container\_port | Port tile cache app will listen on. | `number` | `80` | no |
| desired\_count | Initial number of service instances to launch. | `number` | n/a | yes |
| environment | An environment namespace for the infrastructure. | `string` | n/a | yes |
| fargate\_cpu | vCPU for service. | `number` | `256` | no |
| fargate\_memory | Memory for service in MB. | `number` | `1024` | no |
| git\_sha | Git SHA to use to tag image. | `string` | n/a | yes |
| log\_level | n/a | `string` | `"Log level for tile service app."` | no |
| log\_retention | Time in days to keep logs. | `number` | `30` | no |
| region | Default AWS Region. | `string` | `"us-east-1"` | no |
| tile\_cache\_url | URL of tile cache. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| cloudfront\_distribution\_domain\_name | n/a |
| cloudfront\_distribution\_id | n/a |
| ecs\_update\_service\_policy\_arn | n/a |
| tile\_cache\_bucket\_name | n/a |
| tile\_cache\_bucket\_policy\_update\_policy\_arn | n/a |
| tile\_cache\_cluster | n/a |
| tile\_cache\_service | n/a |
| tile\_cache\_url | n/a |

