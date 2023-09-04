
# Deploying Telegram YouTube/Instagram Downloader Bot on AWS EC2

## Step-by-Step Instructions:

### 1. Set Up AWS EC2 Instance
- Log in to your AWS Management Console.
- Navigate to EC2 and launch a new instance.
- Choose the Amazon Linux 2 AMI.
- Select the appropriate instance type. For lightweight applications, a `t2.micro` or `t3.micro` might be sufficient.
- Configure instance details, storage, and tags as per your requirements.
- Configure your security group to allow inbound traffic on port 22 for SSH and any other ports your application may use.
- Review and launch the instance.
- Download the key pair, e.g., `your_key.pem`.

### 2. Connect to EC2 Instance
From your local terminal or command prompt:

```bash
chmod 400 path_to_your_key.pem
ssh -i "path_to_your_key.pem" ec2-user@your_ec2_public_dns
```

### 3. Update EC2 Instance

```bash
sudo yum update -y
```

### 4. Install Python & pip

```bash
sudo yum install python3 -y
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
```

### 5. Transfer Files to EC2

From your local terminal or command prompt:

```bash
scp -i "path_to_your_key.pem" your_bot_script.py ec2-user@your_ec2_public_dns:~
scp -i "path_to_your_key.pem" requirements.txt ec2-user@your_ec2_public_dns:~
scp -i "path_to_your_key.pem" .env ec2-user@your_ec2_public_dns:~
```

### 6. Install Required Python Packages

On your EC2 instance:

```bash
pip3 install --user -r requirements.txt
```

### 7. Run the Bot

To run the bot and keep it running even after closing the terminal:

```bash
screen
python3 your_bot_script.py
```

To detach from the screen session:

For Mac: `Ctrl + A` followed by `Ctrl + D`
For Windows using Putty: `Ctrl + A` followed by `D`

To reattach to a screen session:

```bash
screen -r
```

## Additional Information:

- Ensure that the EC2 security group allows inbound traffic on the necessary ports for your application.
- For long-term deployment and better management, consider using AWS services like Elastic Beanstalk or ECS.
- Regularly monitor and check logs to handle any unexpected issues.
- Set up AWS CloudWatch for logging and monitoring.


path_to_your_key.pem" .env ec2-user@your_ec2_public_dns:~
```

### 6. Set Up Python Environment on EC2

```bash
pip3 install --user -r requirements.txt
mkdir downloads
```

### 7. Run the Bot

You can run the bot in the background using the `screen` utility:

```bash
screen -S bot
python3 your_bot_script.py
```

To detach from the screen session and let the bot run in the background, press `CTRL + A` followed by `CTRL + D`.

### 8. Re-attach to the Screen Session (If Needed)

If you want to check the bot's status or logs:

```bash
screen -r bot
```

### 9. Stop the Bot

To stop the bot, re-attach to the screen session and press `CTRL + C`.

## Detaching from the Screen Session on Mac

- Press `CTRL + A`.
- Release the keys.
- Press `CTRL + D`.

This will detach you from the screen session, and the bot will continue to run in the background on the EC2 instance.

## Note:

Remember to monitor your AWS resources to avoid unexpected charges and shut down or terminate resources when not in use.

