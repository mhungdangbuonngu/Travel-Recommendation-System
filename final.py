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
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
import io
import argparse
import psycopg2

chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second

parser = argparse.ArgumentParser(description='Nhập URL PostgreSQL và khóa API Google.')

parser.add_argument('--postgres_url', type=str, required=True, help='URL kết nối với PostgreSQL.')
parser.add_argument('--google_api_key', type=str, required=True, help='Khóa API Google.')

args = parser.parse_args()

# Gán giá trị cho postgres_url và GOOGLE_API_KEY
postgres_url = args.postgres_url
os.environ["GOOGLE_API_KEY"] = args.google_api_key

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
        self.audio_data = io.BytesIO()
        
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
            if time.time() - start_time < 2:
                # Hiển thị các dấu chấm trong 3 giây đầu tiên
                if count < len(messages):
                    self.text_widget.delete('1.0', tk.END)  # Xóa nội dung text widget
                    self.text_widget.insert(tk.END, messages[count])
                    self.root.after(250, update_dots, count + 1)
                else:
                    self.root.after(250, update_dots, 0)  # Quay lại biểu tượng đầu tiên
            else:
                # Sau 3 giây, hiển thị thông điệp "Bắt đầu"
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert(tk.END, "Đang lắng nghe\n")

        messages = [".", "..", "..."]  # Danh sách thông điệp
        self.text_widget.delete('1.0', tk.END)  # Xóa nội dung text widget ban đầu

        start_time = time.time()  # Ghi lại thời điểm bắt đầu
        self.root.after(0, update_dots, 0)  # Bắt đầu cập nhật thông điệp ngay lập tức


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
                self.p.terminate()  # Kết thúc phiên làm việc của PyAudio
                self.record_thread.join()
                self.save_to_file()  # Lưu dữ liệu vào BytesIO
                text = self.audio_to_text()  # Chuyển đổi âm thanh thành văn bản
                # self.update_text("Kết quả: " + text)
                self.p = pyaudio.PyAudio()  # Khởi tạo lại phiên làm việc của PyAudio cho các bản ghi mới
                self.process_audio(text)  # Xử lý văn bản âm thanh cho các gợi ý

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
        self.audio_data.close()  # Đảm bảo rằng đối tượng cũ được đóng nếu còn mở
        del self.audio_data  # Xóa tham chiếu đến đối tượng cũ
        self.audio_data = io.BytesIO()  # Tạo một BytesIO mới để lưu âm thanh
        with wave.open(self.audio_data, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(self.p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(self.frames))
        self.audio_data.seek(0)

    def audio_to_text(self):
        recognizer = sr.Recognizer()
        self.audio_data.seek(0)
        with sr.AudioFile(self.audio_data) as source:
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

        cur.execute("SET search_path TO travel_database, public;")

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
        self.update_text(str(result_dict))
        
        embedding_query = model.encode(result_dict['Description'])
        embedding_query_list = embedding_query.tolist()
        
        cur.execute("""
            WITH query_embedding AS (
                SELECT %s::vector(768) AS query_vector
            ),
            similarity_scores AS (
                SELECT
                    h.hotel_id,
                    h.name,
                    h.address,
                    h.rating,
                    h.description,
                    (1 - (h.embedding_description <=> query_vector)) AS similarity
                FROM
                    Hotel h
                    CROSS JOIN query_embedding
                WHERE
                    (h.address).city = %s
                ORDER BY
                    similarity DESC
                LIMIT 2
            )
            -- Chọn 2 khách sạn có độ tương đồng cao nhất
            SELECT
                hotel_id,
                name,
                address,
                rating,
                description,
                similarity
            FROM
                similarity_scores;
        """, (embedding_query_list, result_dict['City']))

        rows = cur.fetchall()
   
        self.update_text(f"Yêu cầu người dùng: {query}")
        for row in rows:
            self.update_text(f"HotelID: {row[0]}")
            self.update_text(f"Name: {row[1]}")
            self.update_text(f"Address: {row[2]}")
            self.update_text(f"Rating: {row[3]}")
            self.update_text(f"Description: {row[4]}")
            self.update_text(f"Similarity: {row[5]}")
            self.update_text("-" * 40)

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
root.title("Travel Recommendation System")

modern_font = font.Font(family="Arial", size=18)

recorder = AudioRecorder()
recorder.root = root

# Create a ScrolledText widget with modern font
recorder.text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=modern_font)
recorder.text_widget.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)  # Make it expand and fill

# Create a toggle button with modern font
start_button = tk.Button(root, text="Bắt đầu ghi âm", command=lambda: toggle_recording(), font=modern_font, bg="lightgreen", fg="black")
start_button.pack(padx=10, pady=10)
root.mainloop()

