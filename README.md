# Voice Controlled AWS Infrastructure Automation

## Project Overview

This project demonstrates how AWS cloud infrastructure can be created and managed using voice commands.  
The system uses Python along with speech recognition to capture user voice input and automatically perform AWS operations.

Instead of manually creating resources from the AWS console or CLI, this project allows users to control cloud infrastructure simply by speaking commands.

The goal of the project is to simplify cloud management and demonstrate automation capabilities using Python and AWS SDK.

---

## How It Works

Voice Command → Python Script → AWS SDK (boto3) → AWS Cloud Resources

1. The user speaks a command.
2. The Python program captures the voice using a speech recognition library.
3. The command is processed and converted into an AWS action.
4. Using boto3 (AWS SDK for Python), the program creates or manages AWS resources.

---

## AWS Services Used

- EC2 (Elastic Compute Cloud)
- VPC (Virtual Private Cloud)
- S3 (Simple Storage Service)
- IAM (Identity and Access Management)

---

## Technologies Used

- Python
- Speech Recognition
- AWS SDK (boto3)
- AWS Cloud Infrastructure
- Linux Environment

---

## Example Voice Commands

Examples of commands supported by the system:

- "Create an EC2 instance"
- "Launch a new server"
- "Create an S3 bucket"
- "Show running instances"
- "Stop an EC2 instance"

The system interprets the command and automatically performs the corresponding AWS action.

---

## Key Features

- Automates AWS infrastructure using voice commands
- Integrates speech recognition with AWS SDK
- Reduces manual cloud configuration
- Demonstrates real-world cloud automation concepts
- Can be extended to support more AWS services

---

## Project Purpose

This project was built as part of a cloud and automation learning journey to explore how voice interfaces can be used to manage cloud infrastructure.

It demonstrates the integration of Python automation, AWS cloud services, and voice-controlled interaction for infrastructure management.

---

## Future Improvements

- Support for more AWS services
- Improved voice command recognition
- Web interface for monitoring infrastructure
- Integration with DevOps workflows

---

## Author

Hitesh Thakran  
Cloud & Infrastructure Enthusiast

LinkedIn  
https://www.linkedin.com/in/hitesh-thakran-9102ba371/
