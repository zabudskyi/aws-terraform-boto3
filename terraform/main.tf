provider "aws" {
  region = "${var.region}"
}

resource "aws_security_group" "allow_ssh_http_icmp" {
  name        = "allow_ssh_http_icmp"
  description = "Allow all inbound ssh, http and icmp traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "instance1" {
  ami             = "${var.ami}"
  instance_type   = "${var.instance_type}"
  key_name        = "${var.ssh_key_name}"
  security_groups = ["allow_ssh_http_icmp"]
  user_data       = "${file("files/bootstrap.txt")}"
  tags {
    Name = "Instance1"
  }
}

resource "aws_instance" "instance2" {
  ami             = "${var.ami}"
  instance_type   = "${var.instance_type}"
  key_name        = "${var.ssh_key_name}"
  security_groups = ["allow_ssh_http_icmp"]
  user_data       = "${file("files/bootstrap.txt")}"
  tags {
    Name = "Instance2"
  }
}

resource "aws_instance" "instance3" {
  ami             = "${var.ami}"
  instance_type   = "${var.instance_type}"
  key_name        = "${var.ssh_key_name}"
  security_groups = ["allow_ssh_http_icmp"]
  user_data       = "${file("files/bootstrap.txt")}"
  tags {
    Name = "Instance3"
  }
}

resource "aws_eip" "ip1" {
  instance = "${aws_instance.instance1.id}"
  vpc      = true
}

resource "aws_eip" "ip2" {
  instance = "${aws_instance.instance2.id}"
  vpc      = true
}

resource "aws_eip" "ip3" {
  instance = "${aws_instance.instance3.id}"
  vpc      = true
}

resource "aws_route53_record" "instance1" {
  zone_id = "${var.route53_zone_id}"
  name    = "a.${var.domain_name}"
  type    = "A"
  ttl     = "300"
  records = ["${aws_eip.ip1.public_ip}"]
}

resource "aws_route53_record" "instance2" {
  zone_id = "${var.route53_zone_id}"
  name    = "b.${var.domain_name}"
  type    = "A"
  ttl     = "300"
  records = ["${aws_eip.ip2.public_ip}"]
}

resource "aws_route53_record" "instance3" {
  zone_id = "${var.route53_zone_id}"
  name    = "c.${var.domain_name}"
  type    = "A"
  ttl     = "300"
  records = ["${aws_eip.ip3.public_ip}"]
}
