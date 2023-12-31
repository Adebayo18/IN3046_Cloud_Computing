data "aws_ami" "ami_id" {
  most_recent = true
  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "allow_public_traffic" {
  name = var.security_group_name 
  ingress {
    description = "TCP from public"
    from_port = var.ui_container_port
    to_port = var.ui_container_port
    protocol = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port = 22
    to_port = 22
    protocol = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allows downloading of packages and libraries"
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow public"
  }

}

resource "aws_instance" "my_instance" {
  ami           = data.aws_ami.ami_id.image_id
  instance_type = var.instance_type
  key_name = var.key_name
  

  # Assign the IAM role to the instance
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size            = 28  # size in GBs
    volume_type            = "gp3"
    delete_on_termination  = true
  }

  vpc_security_group_ids = [aws_security_group.allow_public_traffic.id]

  tags = {
    Name = var.ec2_tag
  }
  depends_on = [ aws_security_group.allow_public_traffic ]
}

# IAM Role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  name = var.iam_role_name

  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

# Attach managed policy for full SQS access
resource "aws_iam_role_policy_attachment" "sqs_full_access" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

resource "aws_iam_role_policy_attachment" "ecr_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.ec2_role.name
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = var.ec2_profile_name
  role = aws_iam_role.ec2_role.name
}