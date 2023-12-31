output "ssh_command" {
  description = "Command to connect to the instance via SSH"
  value       = "ssh -i ${path.module}/${var.key_pair_name} ec2-user@${module.ec2.dns}"
}

output "application_url" {
  value = module.ec2.application_url
}