variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "dgiti-final"
}

variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.30.1.0/24", "10.30.2.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.30.11.0/24", "10.30.12.0/24"]
}

variable "app_port" {
  type    = number
  default = 80
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "instance_profile" {
  type    = string
  default = "LabInstanceProfile"
}

variable "repo_url" {
  type    = string
  default = "https://github.com/SimonP0607/Evaluacion-Final-DGITI.git"
}

variable "repo_branch" {
  type    = string
  default = "main"
}

variable "app_dir" {
  type    = string
  default = "/opt/webapp"
}

variable "db_engine_version" {
  type    = string
  default = "16"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "db_storage_type" {
  type    = string
  default = "gp2"
}

variable "db_multi_az" {
  type    = bool
  default = true
}

variable "db_name" {
  type    = string
  default = "agenda"
}

variable "db_username" {
  type    = string
  default = "agenda_admin"
}

variable "db_password" {
  type      = string
  sensitive = true

  validation {
    condition     = can(regex("^[A-Za-z0-9_-]{12,}$", var.db_password))
    error_message = "La contrasena debe tener al menos 12 caracteres: letras, numeros, guion o guion bajo."
  }
}
