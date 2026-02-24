import speech_recognition as sr
import pyttsx3
import subprocess
import platform
import boto3
import logging
import sounddevice as sd
import soundfile as sf

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

engine = pyttsx3.init()
engine.setProperty("rate", 160)

def speak(text):
    print("SYSTEM:", text)
    engine.say(text)
    engine.runAndWait()

def record_audio(duration=4, filename="voice.wav"):
    fs = 44100
    speak("Recording")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, recording, fs)
    return filename

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

def create_aws_vpc():
    try:
        ec2 = boto3.resource('ec2', region_name='us-east-1')

        vpc = ec2.create_vpc(
            CidrBlock='10.0.0.0/16',
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [{'Key': 'Name', 'Value': 'hitesh-cli-vpc-python'}]
                }
            ]
        )

        vpc.wait_until_available()
        speak("VPC created successfully")
        logger.info(f"VPC ID: {vpc.id}")

    except Exception as e:
        speak("Failed to create VPC")
        logger.error(e)

def execute_command(command):
    is_windows = platform.system().lower() == "windows"

    if "date" in command:
        subprocess.run("date" if not is_windows else "date /t", shell=True)

    elif "create vpc" in command:
        speak("Creating VPC in US East One")
        create_aws_vpc()

    elif "exit" in command:
        speak("Exiting program")
        exit()

    else:
        speak("Only date or create VPC command is supported")

speak("Voice AWS program started")

while True:
    audio_file = record_audio()
    command_text = recognize_audio(audio_file)
    execute_command(command_text)

