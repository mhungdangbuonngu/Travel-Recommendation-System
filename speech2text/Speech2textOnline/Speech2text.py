import speech_recognition as sr
import pyttsx3

#intialize recognizer
r=sr.Recognizer()

def record_text():
    #loop in case of errors, it will go back to the top of the loop and try again
    while(1):
        try:
            #use microphone for input
            with sr.Microphone() as source:
                #prepare to recieve input, reduce noises
                r.adjust_for_ambient_noise(source, duration=0.2)

                #listen for input
                audio=r.listen(source)

                #use google to recognize
                Text=r.recognize_google(audio, language="vi")

                return Text

        except sr.RequestError as e:
            print("Can't get result; {0}".format(e))
        except sr.UnknownValueError:
            print("Unknown error")
    return

def output_text(text):
    f=open("output.txt", "a", encoding="utf-8")
    f.write(text)
    f.write("\n")
    f.close()
    return

while(1):
    text=record_text()
    output_text(text)

    print("Speech recorded.")