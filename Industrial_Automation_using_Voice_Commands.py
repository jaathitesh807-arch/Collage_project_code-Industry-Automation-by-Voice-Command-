import speech_recognition as sr
import pyttsx3
import boto3
import sounddevice as sd
import soundfile as sf
import sys
import time

REGION = "us-east-1"
AMI_ID = "ami-0f3caa1cf4417e51b"   
INSTANCE_TYPE = "t3.micro"
KEY_NAME = "key-for-virginia"      

ec2 = boto3.client("ec2", region_name=REGION)
ec2_res = boto3.resource("ec2", region_name=REGION)

engine = pyttsx3.init()
engine.setProperty("rate", 160)

def speak(text):
    print("\nSYSTEM:", text)
    engine.say(text)
    engine.runAndWait()

def record():
    fs = 44100
    duration = 4
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write("voice.wav", recording, fs)
    return "voice.wav"

def listen():
    r = sr.Recognizer()
    with sr.AudioFile(record()) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        print("YOU:", text)
        return text.lower()
    except:
        return ""

def get_name(tags):
    if not tags:
        return "N/A"
    for t in tags:
        if t["Key"] == "Name":
            return t["Value"]
    return "N/A"

def list_vpcs():
    vpcs = ec2.describe_vpcs()["Vpcs"]
    print("\n--- VPC LIST ---")
    for v in vpcs:
        print(v["VpcId"], v["CidrBlock"], get_name(v.get("Tags")))

def list_subnets(vpc_id):
    subs = ec2.describe_subnets(
        Filters=[{"Name":"vpc-id","Values":[vpc_id]}]
    )["Subnets"]
    print("\n--- SUBNETS ---")
    for s in subs:
        print(s["SubnetId"], s["CidrBlock"], get_name(s.get("Tags")))

def list_igws():
    igws = ec2.describe_internet_gateways()["InternetGateways"]
    print("\n--- IGW ---")
    for g in igws:
        attached = "None"
        if g["Attachments"]:
            attached = g["Attachments"][0]["VpcId"]
        print(g["InternetGatewayId"], get_name(g.get("Tags")), attached)

def create_vpc():
    list_vpcs()
    name = input("Enter VPC Name: ")
    cidr = input("Enter CIDR: ")

    vpc = ec2_res.create_vpc(CidrBlock=cidr)
    vpc.wait_until_available()
    vpc.create_tags(Tags=[{"Key":"Name","Value":name}])

    ec2.modify_vpc_attribute(VpcId=vpc.id, EnableDnsSupport={'Value': True})
    ec2.modify_vpc_attribute(VpcId=vpc.id, EnableDnsHostnames={'Value': True})

    print("VPC:", vpc.id)
    speak("VPC created")

def create_igw():
    name = input("Enter IGW Name: ")

    igw = ec2.create_internet_gateway()
    igw_id = igw["InternetGateway"]["InternetGatewayId"]

    ec2.create_tags(Resources=[igw_id], Tags=[{"Key":"Name","Value":name}])

    list_vpcs()
    vpc_id = input("Attach to VPC: ")

    igws = ec2.describe_internet_gateways()["InternetGateways"]
    for g in igws:
        for att in g.get("Attachments", []):
            if att["VpcId"] == vpc_id:
                print("Already attached:", g["InternetGatewayId"])
                speak("VPC already has internet gateway")
                return

    ec2.attach_internet_gateway(
        InternetGatewayId=igw_id,
        VpcId=vpc_id
    )

    print("IGW:", igw_id)
    speak("IGW attached")

def create_subnet():
    list_vpcs()
    vpc_id = input("Enter VPC ID: ")

    name = input("Subnet Name: ")
    cidr = input("Subnet CIDR: ")

    subnet = ec2_res.create_subnet(
        VpcId=vpc_id,
        CidrBlock=cidr
    )

    subnet.create_tags(Tags=[{"Key":"Name","Value":name}])

    ec2.modify_subnet_attribute(
        SubnetId=subnet.id,
        MapPublicIpOnLaunch={"Value": True}
    )

    print("Subnet:", subnet.id)
    speak("Subnet created")

def create_route_table():
    list_vpcs()
    vpc_id = input("Enter VPC ID: ")

    rt = ec2.create_route_table(VpcId=vpc_id)
    rt_id = rt["RouteTable"]["RouteTableId"]

    list_igws()
    igw_id = input("Enter IGW ID: ")

    ec2.create_route(
        RouteTableId=rt_id,
        DestinationCidrBlock="0.0.0.0/0",
        GatewayId=igw_id
    )

    subnet_id = input("Enter Subnet ID: ")

    ec2.associate_route_table(
        RouteTableId=rt_id,
        SubnetId=subnet_id
    )

    print("Route Table:", rt_id)
    speak("Route table configured")

def create_sg(vpc_id):
    name = input("Security Group Name: ")

    sg = ec2.create_security_group(
        GroupName=name,
        Description="Voice SG",
        VpcId=vpc_id
    )

    sg_id = sg["GroupId"]
    permissions = []

    if input("Enable SSH? (yes/no): ").lower() == "yes":
        permissions.append({
            "IpProtocol":"tcp",
            "FromPort":22,
            "ToPort":22,
            "IpRanges":[{"CidrIp":"0.0.0.0/0"}]
        })

    if input("Enable HTTP? (yes/no): ").lower() == "yes":
        permissions.append({
            "IpProtocol":"tcp",
            "FromPort":80,
            "ToPort":80,
            "IpRanges":[{"CidrIp":"0.0.0.0/0"}]
        })

    if input("Enable HTTPS? (yes/no): ").lower() == "yes":
        permissions.append({
            "IpProtocol":"tcp",
            "FromPort":443,
            "ToPort":443,
            "IpRanges":[{"CidrIp":"0.0.0.0/0"}]
        })

    if permissions:
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=permissions
        )

    print("SG:", sg_id)
    return sg_id

def launch_ec2():
    list_vpcs()
    vpc_id = input("Enter VPC ID: ")

    list_subnets(vpc_id)
    subnet_id = input("Enter Subnet ID: ")

    sg_id = create_sg(vpc_id)

    instance = ec2_res.create_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,   # ✅ KEY USED
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            "SubnetId": subnet_id,
            "DeviceIndex": 0,
            "AssociatePublicIpAddress": True,
            "Groups": [sg_id]
        }]
    )

    instance_id = instance[0].id
    print("\nInstance ID:", instance_id)

    speak("Launching instance, please wait")

    instance[0].wait_until_running()
    time.sleep(5)

    desc = ec2.describe_instances(InstanceIds=[instance_id])
    inst = desc["Reservations"][0]["Instances"][0]

    print("\n===== INSTANCE DETAILS =====")
    print("Instance ID:", instance_id)
    print("Public IP:", inst.get("PublicIpAddress"))
    print("Private IP:", inst.get("PrivateIpAddress"))
    print("VPC ID:", inst.get("VpcId"))
    print("Subnet ID:", inst.get("SubnetId"))
    print("Security Group:", inst["SecurityGroups"][0]["GroupId"])
    print("Key Pair Used:", KEY_NAME)

    speak("Instance ready")

    print("\nSSH Command:")
    print(f"ssh -i {KEY_NAME}.pem ec2-user@{inst.get('PublicIpAddress')}")

    print("\nOr use browser:")
    print("EC2 → Connect → EC2 Instance Connect")

def menu():
    print("\n1. Create VPC")
    print("2. Create IGW")
    print("3. Create Subnet")
    print("4. Create Route Table")
    print("5. Launch EC2")
    print("6. Exit")

speak("AWS Voice Tool Started")

while True:
    menu()
    speak("Say command")

    cmd = listen()

    if "vpc" in cmd:
        create_vpc()
    elif "internet" in cmd:
        create_igw()
    elif "subnet" in cmd:
        create_subnet()
    elif "route" in cmd:
        create_route_table()
    elif "instance" in cmd or "ec2" in cmd:
        launch_ec2()
    elif "exit" in cmd:
        sys.exit()
    else:
        speak("Command not understood")
