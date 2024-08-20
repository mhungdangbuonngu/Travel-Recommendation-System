import pyaudio
import wave
import threading
import speech_recognition as sr
import time
import tkinter as tk
from tkinter import scrolledtext
from tkinter import font
import json
import re
import psycopg2
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second
filename = "output.wav"
postgres_url = "postgresql://travel_database_owner:1V5lHzuegKYh@ep-delicate-haze-a1w36zia.ap-southeast-1.aws.neon.tech/travel_database?sslmode=require"
os.environ["GOOGLE_API_KEY"] = "AIzaSyBdzf2O2lJ3oxFN3b1erMVBcbMCgtzzu3k"

# Initialize LLM and SentenceTransformer
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')
template = """
    You are an AI travel suggestion chatbot. Your task is to analyze the Request:

    Request: "{travel_request}"

    Extract the following 7 pieces of information not in any specific order: Type, District, City, Number_of_people, Price, Rating, and Description.
    Return the result by vietnamese in the following format:
    {{
        "Type": "...",
        "District": "...",
        "City": "...",
        "Number_of_people": "...",
        "Price": "...",
        "Rating": "...",
        "Description": "..."
    }}

    Ensure that the "Type" is one of the following: "Hotel," "Restaurant," or "TouristAttraction." If one or two types are mentioned, return only those. If none are mentioned, include all three types.

    For any information not specified in the travel request, return `null`. Ensure that the JSON result is strictly valid JSON, with no extra text, comments, or parentheses.

    The "District" not include "quận" or "huyện". The "City" not include "thành phố" or "tỉnh".

    The "Price" should be an integer. The "Rating" should be a float.
    """
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | llm

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()  # Create an interface to PortAudio
        self.stream = None
        self.frames = []
        self.recording = False
        self.lock = threading.Lock()
        self.record_thread = None
        self.text_widget = None

    def start_recording(self):
        with self.lock:
            if not self.recording:
                self.recording = True
                self.frames = []
                self.stream = self.p.open(format=sample_format,
                                          channels=channels,
                                          rate=fs,
                                          frames_per_buffer=chunk,
                                          input=True)
                # Start recording in a separate thread
                self.record_thread = threading.Thread(target=self.record_audio)
                # Display message after 2 seconds delay
                threading.Thread(target=self.show_start_message).start()
                self.record_thread.start()

    def show_start_message(self):
        def update_dots(count):
            if count < len(messages):
                self.text_widget.delete('1.0', tk.END)  # Clear the text widget
                self.text_widget.insert(tk.END, messages[count])
                self.root.after(250, update_dots, count + 1)
            else:
                self.text_widget.delete('1.0', tk.END)  # Clear the text widget
                self.text_widget.insert(tk.END, "Bắt đầu\n")  # Move to a new line

        messages = [".", "..", "...", "....", ".....", "......", ".......", "........"]
        self.text_widget.delete('1.0', tk.END)  # Clear the text widget initially
        self.root.after(0, update_dots, 0)

    def show_stop_message(self):
        # Display the stop message immediately
        self.update_text("Kết thúc")
        # Wait for 2 seconds before stopping the stream and processing
        time.sleep(2)
        # Close stream and process file after the delay
        with self.lock:
            if not self.recording:
                self.stream.stop_stream()
                self.stream.close()
                self.p.terminate()  # Terminate the PyAudio instance
                self.record_thread.join()
                self.save_to_file()
                text = self.audio_to_text()
                self.p = pyaudio.PyAudio()  # Reinitialize PyAudio instance for new recordings
                self.process_audio(text)  # Process the audio text for suggestions

    def stop_recording(self):
        with self.lock:
            if self.recording:
                # Start a thread to handle stopping and processing
                threading.Thread(target=self.show_stop_message).start()
                self.recording = False

    def record_audio(self):
        while self.recording:
            try:
                data = self.stream.read(chunk, exception_on_overflow=False)
                self.frames.append(data)
            except IOError as e:
                print(f"IOError: {e}")
                break

    def save_to_file(self):
        self.update_text('Đang xử lý')
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(self.p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(self.frames))

    def audio_to_text(self):
        recognizer = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="vi")
                return text
            except sr.UnknownValueError:
                return "Google Speech Recognition không thể hiểu âm thanh"
            except sr.RequestError as e:
                return f"Không thể kết nối với Google Speech Recognition service; {e}"

    def process_audio(self, query):
        conn = psycopg2.connect(postgres_url)
        cur = conn.cursor()

        cur.execute("SET search_path TO travel_database;")

        cur.execute("SELECT * FROM information_schema.tables WHERE table_name = 'hotel';")
        if not cur.fetchone():
            self.update_text("Bảng 'Hotel' không tồn tại trong schema 'travel_database'.")
            cur.close()
            conn.close()
            return


        response = chain.invoke(query)
        response_text = str(response.content)
        cleaned_json_str = re.search(r'\{.*?\}', response_text, re.DOTALL).group(0)
        result_dict = json.loads(cleaned_json_str)
        cur.execute("""
        SELECT
            h.HotelID,
            h.Name,
            (h.Address).street AS Street,
            (h.Address).district AS District,
            (h.Address).city AS City,
            h.Rating,
            h.Description,
            h.Comments,
            p.Price,
            p.RoomType,
            p.Capacity
        FROM
            travel_database.Hotel h
        JOIN
            travel_database.HotelPrice p ON h.HotelID = p.HotelID
        WHERE
        ((h.Address).district = %s OR %s IS NULL) AND
        ((h.Address).city = %s OR %s IS NULL)
        """,(
            result_dict['District'],
            result_dict['District'],
            result_dict['City'],
            result_dict['City']
        ))

        # Lấy kết quả và so sánh mô tả
        rows = cur.fetchall()
        print(str(rows))
        descriptions = [row[6] for row in rows]
        descriptions_with_info = []
        # Mô tả từ result
        result_description = result_dict['Description'] if result_dict['Description'] else ""
        result_embedding = model.encode([result_description])

        # So sánh và sắp xếp kết quả
        for row in rows:
            description = row[6]
            embedding = model.encode([description])
            similarity = cosine_similarity(result_embedding, embedding)[0][0]
            descriptions_with_info.append((row, description, similarity))

        # Sắp xếp theo mức độ liên quan giảm dần
        descriptions_with_info.sort(key=lambda x: x[2], reverse=True)

        self.update_text(f"Yêu cầu người dùng: {query}")
        for info in descriptions_with_info:
            row, description, similarity = info
            self.update_text(f"HotelID: {row[0]}")
            self.update_text(f"Name: {row[1]}")
            self.update_text(f"Address: {row[2]}, {row[3]}, {row[4]}")
            self.update_text(f"Rating: {row[5]}")
            self.update_text(f"Description: {row[6]}")
            self.update_text(f"Similarity: {similarity:.4f}")
            self.update_text(f"Comments: {row[7]}")
            self.update_text(f"Price: {row[8]}, RoomType: {row[9]}, Capacity: {row[10]}")
            self.update_text("\n")

        cur.close()
        conn.close()

    def update_text(self, message):
        # Method to update the text in the GUI
        if self.text_widget:
           # self.text_widget.delete('1.0', tk.END)  # Clear the text widget
            self.text_widget.insert(tk.END, message + '\n')
            self.text_widget.yview(tk.END)
            
           


def toggle_recording():
    if recorder.recording:
        recorder.stop_recording()
        start_button.config(text="Bắt đầu ghi âm", bg="lightgreen", fg="black")
    else:
        recorder.start_recording()
        start_button.config(text="Kết thúc ghi âm", bg="red", fg="white")

# Set up GUI
root = tk.Tk()
root.title("Voice Recorder")

# Define a modern font
modern_font = font.Font(family="Arial", size=12, weight="bold")

recorder = AudioRecorder()
recorder.root = root

# Create a ScrolledText widget with modern font
recorder.text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=15, font=modern_font)
recorder.text_widget.pack(padx=10, pady=10)

# Create a toggle button with modern font
start_button = tk.Button(root, text="Bắt đầu ghi âm", command=toggle_recording, font=modern_font, bg="lightgreen", fg="black")
start_button.pack(padx=10, pady=10)

root.mainloop()

