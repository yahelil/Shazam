import speech_recognition as sr
import pyaudio


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""
        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception: " + str(e))
    return said

text = get_audio()

if "hello" in text:
    print("hello, how are you?")
elif "what is your name" in text:
    print("My name is Tim")
else:
    print(text)