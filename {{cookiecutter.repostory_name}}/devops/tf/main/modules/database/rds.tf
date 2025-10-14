resource "random_string" "random" {
  length           = 20
  special          = true
  override_special = "$."
}

resource "aws_db_subnet_group" "self" {
  name       = "${var.name}-${var.env}"
  subnet_ids = var.subnets

  tags = {
    Project = var.name
    Env = var.env
    Name = "DB subnet group"
  }
}

resource "aws_db_parameter_group" "postgres_params" {
  name_prefix   = "${var.name}-${var.env}-"
  family = "postgres16"

  parameter {
    name         = "shared_buffers"
    value        = "{DBInstanceClassMemory/32768}" # 1/4 of memory (value in 8kB blocks)
  }

  parameter {
    name         = "effective_cache_size"
    value        = "{DBInstanceClassMemory/16384}" # 1/2 of memory (value in 8kB blocks)
    apply_method = "immediate"
  }

  parameter {
    name         = "work_mem"
    value        = "{DBInstanceClassMemory/65536}" # 1/64 of memory (value in 1kB blocks)
    apply_method = "immediate"
  }

  parameter {
    name         = "maintenance_work_mem"
    value        = "{DBInstanceClassMemory/16384}" # 1/16 of memory (value in 1kB blocks)
    apply_method = "immediate"
  }

  parameter {
    name         = "autovacuum_work_mem"
    value        = "{DBInstanceClassMemory/16384}" # 1/16 of memory (value in 1kB blocks)
    apply_method = "immediate"
  }

  parameter {
    name         = "effective_io_concurrency"
    value        = "200"
    apply_method = "immediate"
  }

  parameter {
    name  = "random_page_cost"
    value = "1.1"
    apply_method = "immediate"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "self" {
  identifier             = "${var.name}-${var.env}-db"
  allocated_storage      = 5
  max_allocated_storage  = 20
  storage_encrypted      = true
  engine                 = "postgres"
  engine_version         = "16.8"
  instance_class         = var.instance_type
  username               = "master"
  db_name                = "backend"
  password               = random_string.random.result
  skip_final_snapshot    = true
  availability_zone      = var.azs[0]
  db_subnet_group_name   = aws_db_subnet_group.self.name
  vpc_security_group_ids = [aws_security_group.db.id]
  parameter_group_name   = aws_db_parameter_group.postgres_params.name

  tags = {
    Project = var.name
  }
}
