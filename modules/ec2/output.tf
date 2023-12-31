output "ami_id" {
  value = data.aws_ami.ami_id.image_id
}

output "application_url" {
  value = "${aws_instance.my_instance.public_dns}:5000"
}

output "dns" {
  value = aws_instance.my_instance.public_dns
}

output "ec2path" {
  value = basename(abspath(path.module))
}