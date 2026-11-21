# Terra-GEN

Turn a client's AWS requirement into ready-to-use Terraform and an architecture diagram.
Rule-based: no AI, no API keys, same input always gives the same output.

Built for people who get a deployment task from a client but are not comfortable writing
Terraform (HCL) by hand.

## What it does

1. You paste the client's full requirement (or fill a YAML file).
2. Terra-GEN reads it, shows **what it understood**, and lets you correct it.
3. It picks the AWS services, applies your budget and availability answers, and generates:
   - `merged/main.tf`: the whole infrastructure in one file
   - `split/`: the same code, one file per service (`vpc.tf`, `ec2.tf`, ...)
   - `terraform.tfvars`: placeholders for the values you fill in yourself
   - an architecture page (diagram, traffic flow, decisions, what is not covered)
   - a code page with one-click **Copy** buttons
   - a PDF and a short report
4. It runs `terraform fmt` and `terraform validate` on the result.

Anything it cannot build yet is listed under **Not covered, write manually**. Nothing is silently dropped.

## Supported AWS services (so far)

| Service | Notes |
|---|---|
| VPC | 2 public + 2 private subnets, internet gateway, no NAT gateway (keeps cost low) |
| EC2 | Web server, size follows the budget |
| RDS | MySQL or PostgreSQL in private subnets, Multi-AZ when high availability is requested |
| S3 | Private, encrypted, versioned bucket |

Planned: load balancer and Auto Scaling, CloudFront, Route 53, Lambda and API Gateway,
DynamoDB, SQS/SNS, CloudWatch, IAM roles, ECS/EKS.

## Quick start (Linux or WSL)

    git clone https://github.com/krishna5ai/Terra-GEN.git
    cd Terra-GEN
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Optional, for the validation step: install [Terraform](https://developer.hashicorp.com/terraform/install).

### Use the website

    python server.py

Open http://localhost:5000, paste a requirement, review it, generate.

### Use the command line

    python main.py samples/shop-site.yaml     # from a requirement YAML file
    python extract.py samples/client1.txt     # from plain text, with a review step
    python validate.py                        # terraform fmt / init / validate on the output

Results are written to the `output/` folder.

## Security

- Terra-GEN never asks for AWS credentials. Generated files contain placeholders (`FILL_...`)
  that you replace in `terraform.tfvars` on your own computer.
- `terraform.tfvars` and Terraform state files are git-ignored. Never commit them.
- Generated defaults: private S3 buckets, encrypted disks and databases, database not
  public, IMDSv2 required, SSH limited to the IP you set.
- Always run `terraform plan` and read it before `terraform apply`. Run `terraform destroy`
  when you are done to stop charges.

## Limits

- Requirements are read with keyword rules, so unusual wording may be missed. That is why
  there is a review step before generating.
- Costs are not calculated. Use the AWS Pricing Calculator for quotes.
- Treat the output as a solid starting point and review it before using it in production.

## Project layout

    app/          generator, registry, evaluator, extractor, architecture, PDF and pages, web app
    templates/    Terraform templates (one per service)
    web/          website templates
    samples/      example requirements
    main.py       generate from a YAML file
    extract.py    generate from plain text
    validate.py   check the output with Terraform
    server.py     start the website

## License

MIT. See `LICENSE`.
