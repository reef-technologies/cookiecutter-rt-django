output "connection_string" {
  value     = "postgres://${aws_db_instance.admin.username}:${aws_db_instance.admin.password}@${aws_db_instance.admin.endpoint}/${aws_db_instance.admin.name}"
  sensitive = true
}

output "user" {
  value     = aws_db_instance.admin.username
}

output "password" {
  value     = aws_db_instance.admin.password
  sensitive = true
}

output "endpoint" {
  value = aws_db_instance.admin.endpoint
}

output "port" {
  value = aws_db_instance.admin.port
}

output "name" {
  value = aws_db_instance.admin.name
}