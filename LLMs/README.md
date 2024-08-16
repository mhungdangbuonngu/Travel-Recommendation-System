# LLMs

### Thành Phần Chính

1. #### Ollama
   
   **Ollama** được sử dụng để khởi động một máy chủ phục vụ cho mô hình ngôn ngữ lớn (LLM). - Máy chủ này sẽ xử lý các yêu cầu và trả về kết quả dựa trên mô hình được chỉ định, trong trường hợp này là mô hình du lịch thông minh `ontocord/vistral:latest`. 

2. #### Langchain
   
   **Langchain** là một thư viện Python được sử dụng để quản lý các chuỗi lệnh và tạo ra các lời nhắc (prompts) cho mô hình ngôn ngữ. 
   
     Trong đoạn mã này, Langchain được sử dụng để tạo một chuỗi lệnh kết hợp giữa lời nhắc và mô hình ngôn ngữ, cho phép bạn tạo ra một trợ lý có thể phân tích và trích xuất thông tin từ các yêu cầu du lịch của người dùng. 

### Cách Thức Hoạt Động

1. Đầu tiên, đoạn mã cài đặt các thư viện cần thiết và khởi động máy chủ Ollama để có thể xử lý các yêu cầu thông qua mô hình ngôn ngữ. 
2. Sau đó, mô hình ngôn ngữ `ontocord/vistral:latest` được tải về từ kho dữ liệu. 
3. Tiếp theo, một lời nhắc (prompt) được tạo ra để hướng dẫn mô hình cách trích xuất thông tin quan trọng từ các yêu cầu du lịch. 
4. Mô hình được kết nối với lời nhắc này và có thể được sử dụng để phân tích và đưa ra gợi ý cho các yêu cầu du lịch cụ thể.