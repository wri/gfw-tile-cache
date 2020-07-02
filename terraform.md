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
| container\_name | n/a | `string` | `"gfw-tile-cache"` | no |
| container\_port | n/a | `number` | `80` | no |
| desired\_count | n/a | `number` | `1` | no |
| environment | An environment namespace for the infrastructure. | `string` | n/a | yes |
| git\_sha | n/a | `any` | n/a | yes |
| log\_level | n/a | `string` | n/a | yes |
| log\_retention | n/a | `number` | `30` | no |
| region | n/a | `string` | `"us-east-1"` | no |

## Outputs

| Name | Description |
|------|-------------|
| cloudfront\_distribution\_domain\_name | n/a |
| cloudfront\_distribution\_id | n/a |
| tile\_cache\_bucket\_name | n/a |
| tile\_cache\_url | n/a |

