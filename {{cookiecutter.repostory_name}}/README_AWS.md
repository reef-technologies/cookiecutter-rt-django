# Deploying to AWS

The deployment is split into two steps:

Files related to AWS deployment has been generated in `devops/` directory.

By convention, projects that are meant to be deployed to AWS have a `deploy-to-aws.sh` script in the root dir and a `devops` directory.
The script builds the docker image, uploads it and tells AWS to reload the app (causing a new ec2 machine to be spawned).
In the `devops` directory you will find terraform configuration as well as packer files (for building the AMI).

If you want to deploy your app to an AWS environment, you need to do following steps:

- configuring your environment
- create an infra s3 bucket
- deploy `tf/core` (contains stuff common to all environments in given AWS Account)
- deploy chosen `tf/main/envs/<selected_env>` (by default staging and prod are generated)

## Prerequisites

Before the first `terraform apply` of an environment, make sure the following are in place.
A fresh checkout will **not** deploy without them.

### A registered, delegated domain with a Route53 hosted zone

The deployment provisions an ACM certificate validated through DNS and an `A` record on the
load balancer, both inside a **public Route53 hosted zone on the same AWS account**. You need:

- a domain that is **registered and correctly delegated** to that hosted zone (the placeholder
  `fake-domain.com` in the tfvars will not work);
- the matching values in `devops/tf/main/envs/<env>/terraform.tfvars`: `base_domain_name`
  (the zone apex, e.g. `example.com`) and `domain_name` (the app FQDN, e.g. `staging.api.example.com`).

Verify the zone exists and delegation is healthy:

```
aws route53 list-hosted-zones
dig +short NS <base_domain_name> @8.8.8.8   # must return the awsdns.* servers of your zone
```

If the NS records don't point at your hosted zone, ACM validation will hang forever with no
clear error - fix delegation first.

### An EC2 SSH public key

`ec2_ssh_key` in `terraform.tfvars` must contain the **public** key material
(`ssh-ed25519 AAAA...`), not a path and not the private key. It is required - an empty string
passes `terraform plan` but then `aws_key_pair` fails on apply. Generate one with:

```
ssh-keygen -t ed25519 -f ~/.ssh/<project>-<env> -N ""
cat ~/.ssh/<project>-<env>.pub   # paste this line into ec2_ssh_key
```

### SSH access (allowed source IPs)

SSH (port 22) and the monitoring mTLS endpoint (port 10443) are locked down by source IP.
The defaults are the Reef jump-boxes; if you deploy from elsewhere you get **no SSH access** at
all. Override the allowlists in `terraform.tfvars`:

```
ssh_allowed_cidrs        = ["<your.ip.addr.ess>/32"]
monitoring_allowed_cidrs = ["<monitoring.host>/32"]
```

Note that SSH is a convenience, not the primary debugging channel - see [Diagnostics](#diagnostics).

{% if cookiecutter.monitoring %}
### Monitoring certificates

nginx serves a mutual-TLS monitoring endpoint (port 10443) and **will not start** until it is
given valid certificates. The repository ships placeholders containing `replace-me` in
`devops/tf/main/files/nginx/monitoring_certs/`:

- `monitoring-ca.crt.txt` - the CA certificate
- `monitoring.crt.txt` - the server certificate
- `monitoring.key.txt` - the server private key

Replace each placeholder with a real PEM **before** the first `terraform apply` (a precondition
fails the apply with a clear message if any still contains `replace-me`). Two ways to do it:

- **Production:** generate a cert-key pair via
  [prometheus-grafana-monitoring](https://github.com/reef-technologies/prometheus-grafana-monitoring)
  (see its README). It produces `cert.crt`, `cert.key` and `ca.crt`; paste them into the
  `.txt` files mapped as `cert.crt -> monitoring.crt.txt`, `cert.key -> monitoring.key.txt`,
  `ca.crt -> monitoring-ca.crt.txt`.
- **Quick self-signed pair for testing:**

  ```
  # CA
  openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out monitoring-ca.crt.txt \
    -subj "/CN=<project>-monitoring-ca" -days 365
  # server key + cert signed by the CA
  openssl req -newkey rsa:2048 -nodes -keyout monitoring.key.txt -out server.csr -subj "/CN=monitoring"
  openssl x509 -req -in server.csr -CA monitoring-ca.crt.txt -CAkey ca.key -CAcreateserial \
    -out monitoring.crt.txt -days 365
  ```

  Paste the resulting PEM blocks (including the `-----BEGIN/END-----` lines) into the matching
  `.txt` files.
{% endif %}

## Required software

*AWS CLI*

AWS recommends using profiles, when dealing with multiple AWS accounts.
To choose between environments, rather than switching access and secret keys, we just switch our profiles.
We can choose our profile name, which make it easier to recognize in which environment we operate.
To configure AWS environment, you need to have AWS CLI installed.
It is recommended to use AWS v2, which can be downloaded from:
<https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>

*Terraform* You will also need terraform version 1.0.x. It is recommended to use `tfenv` to install terraform with correct version.
You can download an install it from <https://github.com/tfutils/tfenv>

*direnv* To avoid mistakes when switching environments (or regions), it is recommended to use `direnv` tools, which supports loading environment variables from .envrc file, placed in directory.
You can read about it here:
<https://direnv.net/>

## Configure your environment

To configure your AWS profile, please run:

```
$ aws configure --profile <profile_name>
```

And answer following questions:

```
AWS Access Key ID: ...
AWS Secret Access Key: ...
Default region name: us-east-1 (just an example)
Default output format [None]: (can be left blank)
```

Once, configured, you can switch your profile using `AWS_PROFILE=` env variable or by adding `--profile` option to your aws cli command.

It's handy to create .envrc file in the project rood directory (where deploy-to-aws.sh is created) with content:

```
export AWS_PROFILE=<your_profile_name>
export AWS_REGION=<selected_aws_region>
```

And then accept changes by using command:

```
$ direnv allow
```

After doing that, anytime you enter the project directory, correct profile will be loaded.

## Configuring infra

You only need to do this if you change anything in `devops` directory (or if you mess something up in AWS console and want to revert the changes).

Create infra bucket

Before being able to run terraform, we need to create S3 bucket, which will hold the state.
This bucket is used by all environments and needs to be globally unique.

To create bucket, please type:

```
aws s3 mb --region {{ cookiecutter.aws_region }} s3://{{ cookiecutter.aws_infra_bucket }}
```

TF has a following structure:

```
|- devops
  |- tf
    |- core
    |- main
      |- envs
      | |- staging
      | |- prod
      |- modules
```

You can run terraform from:

- core
- envs/staging
- envs/prod

directories.

Directory *core* contains infrastructure code, which needs to be created BEFORE pushing docker image.
It is responsible for creating docker registries, which you can use, to push docker images to.

Code placed in *main* is the rest of the infrastructure, which is created after pushing docker image.

Each of the environment (and core) can be applied by executing:

```
terraform init
terraform apply
```

IMPORTANT! the env variables for the apps (`.env` file) and `docker-compose.yml` are defined in terraform files, if you change any, you need to run `terraform apply` AND refresh the ec2 instance.
The same goes for AMI built by packer.

## Adding secrets to the projects

Cloud init is configured to provision EC2 machines spun up as part of this project's infrastructure.
As part of this provisioning, SSM parameters following a specific name convention are read and saved as files in EC2's home directory (RDS access details are managed in another way).
SSM parameters can be managed via AWS console (Systems Manager -> Parameter Store) or via AWS CLI (`aws ssm`).
The naming convention is `/application/{{ cookiecutter.aws_project_name }}/{env}/{path_of_the_file_to_be_created}`, for example `/application/project/staging/.env`.
A few such parameters are managed by terraform in this project (e.g. `.env`, `docker-compose.yml`) and more can be added.
In case you need to add confidential files (like a GCP credentials file) you can simply create appropriate SSM parameters.
These will only be accessible to people that access to AWS or EC2 machines, not to people who have access to this repository.
One such parameter, namely `/application/{{ cookiecutter.aws_project_name }}/{env}/secret.env` is treated specially - if it exists (it doesn't by default) its contents are appended to `.env` during EC2 machine provisioning - this is a convenient way of supplying pieces of confidential information, like external systems' access keys to `.env`.

{% if cookiecutter.observability %}
## Observability

The project ships a Grafana Alloy collector as part of `docker-compose.yml`, alongside `app`, `celery` and `nginx`. Alloy receives OTLP traces from every service on `alloy:4317`/`alloy:4318`, applies tail-sampling and forwards traces to Grafana Tempo, plus tails Docker container logs and forwards them to Grafana Loki. **There is no separate EC2 instance for the collector** — it lives in the same `docker-compose` as the app.

### Alloy configuration

`alloy/config.alloy` is deployed as an SSM parameter at `/application/{{ cookiecutter.aws_project_name }}/{env}/alloy/config.alloy`, managed by terraform (see `devops/tf/main/modules/backend/parameters.docker-compose.tf`). Cloud init writes it to `alloy/config.alloy` next to `docker-compose.yml` on the EC2 host. Any change to `config.alloy` therefore requires a `terraform apply` plus a refresh of the EC2 instance — editing the file in place on the box is overwritten on the next provision.

### Required secrets in `.env`

In addition to the Loki block (`LOKI_URL`, `LOKI_USER`, `LOKI_PASSWORD`, `LOKI_CLIENT`, `LOKI_CLIENT_SERVER_GROUP`), observability uses:

- `TEMPO_URL`, `TEMPO_USER`, `TEMPO_PASSWORD` — Tempo uses the **same `.htpasswd` credentials** as Loki (see the top-level project README for how to generate them via `add_loki_target.sh`).
- `OTEL_SERVICE_NAMESPACE` — defaults to the repository name; usually fine.
- `OTEL_DEPLOYMENT_ENVIRONMENT` — `staging` / `production`.
- `GIT_SHA` — set automatically by the deploy pipeline. `devops/scripts/build-backend.sh` uses `GIT_SHA` from the build environment or falls back to `git rev-parse --short HEAD`, passes it as `--build-arg GIT_SHA=...`, and the application image stores it permanently as `GIT_SHA` and `OTEL_SERVICE_VERSION`. Cloud Init reads the value from the pulled image into `.env` so nginx reports the same `service.version`.

### Running without Loki/Tempo credentials

`LOKI_URL`/`TEMPO_URL` default to Reef's internal aggregators (`loki.reef.pl` / `tempo.reef.pl`)
and the credentials are generated by an internal tool. Outside Reef you have two options:

- Leave the credentials blank. Alloy still starts and the stack is healthy, but it cannot ship
  logs/traces to Loki/Tempo (the exporters just fail). **Container logs still reach CloudWatch**
  regardless, so you don't lose observability on the box itself.
- Disable observability entirely by regenerating the project with `observability=false` - this
  drops the `alloy` service and the OTEL wiring from the compose file.

{% endif %}

{% if cookiecutter.vulnerabilities_scanning %}
## Vulnerability scanning

This project was generated with `vulnerabilities_scanning` enabled, so you **must** create an
additional SSM parameter named `/application/{{ cookiecutter.aws_project_name }}/{env}/.vuln.env`
with the environment variables required by [vulnrelay](https://github.com/reef-technologies/vulnrelay)
**before** deploying. Terraform does not create this parameter for you. Look at the
`/envs/prod/.vuln.env.template` file to see the expected file format.

> **Important:** the `.vuln.env` file is referenced via `env_file:` in `docker-compose.yml`, so
> if the SSM parameter is missing the **entire `docker compose up` fails** on the EC2 host and the
> machine never becomes healthy - not just the `vulnrelay` container. Create it (even with dummy
> values for a test deploy) before applying the environment. With dummy DefectDojo values the
> `vulnrelay` container restart-loops, which is harmless to the rest of the stack.

For variable values, please refer to the [instructions in the internal handbook](https://github.com/reef-technologies/internal-handbook/blob/master/vuln_management.md).

To stand up a test deploy without real DefectDojo credentials:

```
printf 'ENV=staging\nDD_URL=https://defectdojo.invalid\nDD_API_KEY=dummy-not-configured\nDD_PRODUCT={{ cookiecutter.aws_project_name }}\nSENTRY_DSN=\n' \
  | aws ssm put-parameter --name /application/{{ cookiecutter.aws_project_name }}/staging/.vuln.env \
      --type SecureString --value file:///dev/stdin --overwrite
```
{% endif %}

## Deploying apps

The docker containers are built with code you have locally, including any changes.
Building requires docker.
To successfully run `deploy-to-aws.sh` you first need to do `./setup-prod.sh`.
It uses the aws credentials stored as `AWS_PROFILE` variable.
If you don't set this variable, the `default` will be used.

`deploy-to-aws.sh` is meant for **subsequent** deploys - it builds the image, pushes it and
triggers an instance refresh of the running Auto Scaling Group. For the very **first** deploy
of an environment follow the ordered sequence in [First deploy](#first-deploy) below
(the script tolerates a missing ASG, but the infrastructure has to be applied in the right order).

## First deploy

The first deploy of an environment has a strict order, because the EC2 machine pulls the
application image from ECR the moment it boots - the image (including the `:latest` tag) has to
exist *before* the environment is applied. Do **not** run `deploy-to-aws.sh` first.

1. **Make sure the [Prerequisites](#prerequisites) are satisfied** (domain/zone, SSH key{% if cookiecutter.monitoring %}, monitoring certificates{% endif %}{% if cookiecutter.vulnerabilities_scanning %}, `.vuln.env` SSM parameter{% endif %}).

2. **State bucket** (once per AWS account):

   ```
   aws s3 mb --region {{ cookiecutter.aws_region }} s3://{{ cookiecutter.aws_infra_bucket }}
   ```

3. **`tf/core`** - creates the ECR repositories (app + backups, for every env):

   ```
   cd devops/tf/core && terraform init && terraform apply
   ```

4. **Build and push the images** (this pushes both `:latest` and the SHA tag, for the app and the
   backups image - the booting machine needs `:latest`):

   ```
   ./setup-prod.sh
   ./devops/scripts/build-backend.sh <env>     # <env> = staging or prod
   ```

5. **Apply the environment** - this is what actually creates the VPC, RDS, ALB, ASG, DNS, etc.:

   ```
   cd devops/tf/main/envs/<env> && terraform init && terraform apply
   ```

From now on, redeploying code is just `./deploy-to-aws.sh <env>` (build + push + instance refresh)
or pushing to a `deploy-<env>` branch (see the CD workflow).

## Diagnostics

The primary debugging channel is **CloudWatch Logs**, not SSH (SSH is restricted to
`ssh_allowed_cidrs`). Useful commands:

```
# container logs (one log stream per container, grouped per machine)
aws logs tail /aws/ec2/{{ cookiecutter.aws_project_name }}-<env> --follow

# cloud-init / boot output of the machine
aws ec2 get-console-output --instance-id <id> --latest --output text

# is the app healthy behind the load balancer?
TG=$(aws elbv2 describe-target-groups --names {{ cookiecutter.aws_project_name }}-<env> \
  --query 'TargetGroups[0].TargetGroupArn' --output text)
aws elbv2 describe-target-health --target-group-arn "$TG"

# certificate status (must be ISSUED before the ALB listener can use it)
aws acm describe-certificate --certificate-arn <arn> --query 'Certificate.Status'
```

The CloudWatch log group `/aws/ec2/<project>-<env>` is created by terraform with a 30-day
retention and is removed on `terraform destroy`.
