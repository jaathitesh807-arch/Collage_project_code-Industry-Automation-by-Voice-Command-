import speech_recognition as sr
import pyttsx3
import boto3
import logging
import sounddevice as sd
import soundfile as sf
import sys

#config_start#
REGION = "us-east-1"
AMI_ID = "ami-0f3caa1cf4417e51b"
INSTANCE_TYPE = "t3.micro"
#config_end#

#logging_start#
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
#logging_end#

#voice_engine_start#
engine = pyttsx3.init()
engine.setProperty("rate", 160)

def speak(text):
    print("SYSTEM:", text)
    engine.say(text)
    engine.runAndWait()
#voice_engine_end#

#audio_record_start#
def record_audio(duration=4, filename="voice.wav"):
    fs = 44100
    speak("Recording")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, recording, fs)
    return filename
#audio_record_end#

#speech_to_text_start#
def recognize_audio(file):
    r = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        print("YOU SAID:", text)
        return text.lower()
    except:
        speak("I did not understand")
        return ""
#speech_to_text_end#

#aws_client_start#
ec2_client = boto3.client("ec2", region_name=REGION)
ec2_resource = boto3.resource("ec2", region_name=REGION)
#aws_client_end#

#vpc_list_start#
def list_vpcs():
    vpcs = ec2_client.describe_vpcs()["Vpcs"]

    print("\nAvailable VPCs")
    print("-----------------------------------------------------")
    print("{:<20} {:<18} {:<20}".format("VPC ID", "CIDR", "NAME"))
    print("-----------------------------------------------------")

    for vpc in vpcs:
        name = "N/A"
        if "Tags" in vpc:
            for tag in vpc["Tags"]:
                if tag["Key"] == "Name":
                    name = tag["Value"]
        print("{:<20} {:<18} {:<20}".format(vpc["VpcId"], vpc["CidrBlock"], name))

    print("-----------------------------------------------------")
#vpc_list_end#

#vpc_create_start#
def create_vpc():
    list_vpcs()
    name = input("Enter VPC Name: ").strip()
    cidr = input("Enter CIDR (example 10.0.0.0/16): ").strip()

    vpc = ec2_resource.create_vpc(CidrBlock=cidr)
    vpc.wait_until_available()
    vpc.create_tags(Tags=[{"Key": "Name", "Value": name}])

    speak("VPC created successfully")
    print("New VPC ID:", vpc.id)
#vpc_create_end#

#subnet_create_start#
def create_subnet():
    list_vpcs()
    vpc_id = input("Enter VPC ID: ").strip()

    name = input("Enter Subnet Name: ").strip()
    subnet_type = input("Public or Private? ").strip().lower()
    cidr = input("Enter Subnet CIDR (example 10.0.1.0/24): ").strip()

    subnet = ec2_resource.create_subnet(
        VpcId=vpc_id,
        CidrBlock=cidr
    )

    subnet.create_tags(Tags=[{"Key": "Name", "Value": name}])

    if subnet_type == "public":
        ec2_client.modify_subnet_attribute(
            SubnetId=subnet.id,
            MapPublicIpOnLaunch={"Value": True}
        )

    speak("Subnet created successfully")
    print("Subnet ID:", subnet.id)
#subnet_create_end#

#security_group_start#
def create_security_group(vpc_id):
    sg_name = input("Enter Security Group Name: ").strip()

    sg = ec2_client.create_security_group(
        GroupName=sg_name,
        Description="Voice SG",
        VpcId=vpc_id
    )

    sg_id = sg["GroupId"]
    permissions = []

    if input("Enable SSH (yes/no)? ").lower() == "yes":
        permissions.append({
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        })

    if input("Enable HTTP (yes/no)? ").lower() == "yes":
        permissions.append({
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        })

    if input("Enable HTTPS (yes/no)? ").lower() == "yes":
        permissions.append({
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        })

    if permissions:
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=permissions
        )

    return sg_id
#security_group_end#

#instance_launch_start#
def launch_instance():
    list_vpcs()
    vpc_id = input("Enter VPC ID: ").strip()

    subnets = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["Subnets"]

    print("\nAvailable Subnets")
    print("---------------------------------------------")
    print("{:<20} {:<18}".format("Subnet ID", "CIDR"))
    print("---------------------------------------------")

    for s in subnets:
        print("{:<20} {:<18}".format(s["SubnetId"], s["CidrBlock"]))

    print("---------------------------------------------")

    subnet_id = input("Enter Subnet ID: ").strip()
    sg_id = create_security_group(vpc_id)

    try:
        instance = ec2_resource.create_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[{
                "SubnetId": subnet_id,
                "DeviceIndex": 0,
                "AssociatePublicIpAddress": True,
                "Groups": [sg_id],
            }],
        )

        speak("Instance launched successfully")
        print("Instance ID:", instance[0].id)

    except Exception as e:
        print("Error:", e)
        speak("Instance launch failed")
#instance_launch_end#

#command_handler_start#
def execute_command(command):

    if "create vpc" in command:
        create_vpc()

    elif "create subnet" in command:
        create_subnet()

    elif "launch instance" in command:
        launch_instance()

    elif "stop python" in command:
        speak("Stopping program")
        sys.exit(0)

    else:
        speak("Say create vpc, create subnet, launch instance or stop python")
#command_handler_end#

#main_start#
speak("Voice AWS Agent Started in us east one")

while True:
    audio_file = record_audio()
    command_text = recognize_audio(audio_file)
    execute_command(command_text)
#main_end#
