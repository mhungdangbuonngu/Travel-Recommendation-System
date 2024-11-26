import streamlit as st
from streamlit_float import *
from streamlit_folium import st_folium
import folium
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import psycopg2
import os
import re
import json
from datetime import time
#ten page
page = st.title("Travel Recommendation System from USTH")
#khoi tao 'api' va 'model'
if "api" not in st.session_state:
    st.session_state.api=None
if 'model' not in st.session_state:
    st.session_state.model=None
if 'postgres_url' not in st.session_state:
     st.session_state.postgres_url=None
#lay api gemini-1.5
@st.cache_resource
def get_gemini(api):
    os.environ["GOOGLE_API_KEY"]=api
    return ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
#lay api va postgresql url (paste thang api :< )
if st.session_state.api is None:
    st.session_state.api='AIzaSyDLp-s6ah1ds_dWa1r1UWsxywTxMte9qFY'
if st.session_state.postgres_url is None:
    st.session_state.postgres_url='postgresql://public_owner:7CBm0fdOPkgz@ep-sweet-field-a1urmrzw.ap-southeast-1.aws.neon.tech/public?sslmode=require&options=endpoint%3Dep-sweet-field-a1urmrzw'
if st.session_state.api and st.session_state.model is None:
    st.session_state.model=get_gemini(st.session_state.api)
#amenities hotel
@st.cache_data
def get_amenities():
    conn = psycopg2.connect(st.session_state.postgres_url)
    cur = conn.cursor()
    cur.execute("SET search_path TO travel_database, public;")
    cur.execute("""
        SELECT DISTINCT unnest(amenities) AS unique_amenities
        FROM hotel;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    amenities_list = [row[0] for row in rows]
    amenities_list_str = "\n    ".join(f'"{amenities_type}"' for amenities_type in amenities_list)
    return amenities_list_str
#hotel style
@st.cache_data
def get_hotel_style():
    conn = psycopg2.connect(st.session_state.postgres_url)
    cur = conn.cursor()
    cur.execute("SET search_path TO travel_database, public;")
    cur.execute("""
        SELECT DISTINCT style
        FROM hotel
        WHERE style IS NOT NULL;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    att_type_list = [row[0] for row in rows]
    att_type_list_str = "\n    ".join(f'"{att_type}"' for att_type in att_type_list)
    return att_type_list_str
#attraction type
@st.cache_data
def get_attraction_type():
    conn = psycopg2.connect(st.session_state.postgres_url)
    cur = conn.cursor()
    cur.execute("SET search_path TO travel_database, public;")
    cur.execute("""
        SELECT DISTINCT unnest(attraction_type) AS unique_attraction_type
        FROM touristattraction;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    att_type_list = [row[0] for row in rows]
    att_type_list_str = "\n    ".join(f'"{att_type}"' for att_type in att_type_list)
    return att_type_list_str
#restaurant type
@st.cache_data
def get_restaurant_types():
    conn = psycopg2.connect(st.session_state.postgres_url)
    cur = conn.cursor()
    cur.execute("SET search_path TO travel_database, public;")
    cur.execute("""
        SELECT DISTINCT unnest(restaurant_type) AS unique_res_type
        FROM restaurant;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    res_type_list = [row[0] for row in rows]
    res_type_list_str = "\n    ".join(f'"{res_type}"' for res_type in res_type_list)
    return res_type_list_str
#suitable for restaurant
@st.cache_data
def get_suitable_for():
    conn = psycopg2.connect(st.session_state.postgres_url)
    cur = conn.cursor()
    cur.execute("SET search_path TO travel_database, public;")
    cur.execute("""
        SELECT DISTINCT unnest(suitable_for) AS unique_res_suit
        FROM restaurant;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    res_suit_list = [row[0] for row in rows]
    res_suit_list_str = "\n    ".join(f'"{res_suit}"' for res_suit in res_suit_list)
    return res_suit_list_str
amenities_list_str=get_amenities()
style_list_str=get_hotel_style()
res_type_list_str=get_restaurant_types()
res_suit_list_str=get_suitable_for()
att_type_list_str=get_attraction_type()
travel_type_list = ["Nghỉ dưỡng", "Khám phá"]
companion_list = ["friends", "family", "colleagues"]
transport_list = ["self-drive car", "motorbike", "bicycle", "public transport"]
city_list = ["Hà Nội"]
district_list = ["Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Long Biên", "Cầu Giấy", "Đống Đa", "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hà Đông", "Sơn Tây"]
# region 
template = """
You are an AI travel suggestion chatbot. Analyze the following travel request:

Request: "{travel_request}"

Extract general and specific requirements for Hotels, Restaurants, and Tourist Attractions, even if some are not explicitly mentioned. For each type, provide the following information:

**General Requirements:**
- Type:
  - If the request explicitly mentions "nghỉ dưỡng", "thư giãn", "resort", or similar keywords, and the overall tone is relaxed or leisure-oriented or have leisure activities, relaxation-focused activities(clear relaxation keywords), assign "Nghỉ dưỡng".
  - If the request explicitly mentions "khám phá", "văn hóa", "ẩm thực", or similar keywords, and the overall tone is exploratory or adventurous or exploration or have activity-focused activities (clear exploration keywords), assign "Khám phá".
  - For general requests or requests with mixed intentions, return `null`.
- Number_of_people: Extract the number of people or return null if not specified.
- Companions: Extract the companions mentioned in the request and translated it if it needed, must be one from this list: {companion_list} or return null if not specified.
- Transportation: Identify the transportation method mentioned in the request and translated, convert it if it needed, transportation must be one from this list: {transport_list} or return null if not specified.
- Time:
  - Extract specific dates or time ranges mentioned in the request.
  - If no specific dates are mentioned, check for keywords like "ngày", "tuần", "tháng" and their corresponding numbers.
  - Return null if there's no date or time ranges in the request.
  - For example, "3 ngày" should be extracted as "3 days".
- City: The mentioned city (without "city" or "province").
- District: The mentioned district (without "district") and must be one frin this list: {district_list} or else return null.
- Price_range: Specify as "low", "medium", or "high" based on the request.

**For Hotels, also identify:**
- Requirements: A summary text of specific requirements or preferences mentioned.
- Amenities: IMPORTANT - ONLY include amenities from {amenities_list} if EXPLICITLY mentioned in the request. 
  Examples:
  - If request says "need hotel with pool and gym" → include ["Pool", "Gym"]
  - If request doesn't mention any amenities → return null
  - Do NOT assume or add amenities that weren't specifically mentioned
- Style: Only include styles from this list if explicitly mentioned in the request: {style_list} or else return null

**For Restaurants, also identify:**
- Requirements: A summary text of specific requirements or preferences mentioned.
- Restaurant_Type: From this list: {restaurant_type_list}
- Suitable_For: From this list: {suitable_for_list}

**For Tourist Attractions, also identify:**
- Requirements: A list of specific requirements or preferences mentioned.
- Attraction_Type: From this list: {attraction_type_list}

Return the result using the following JSON format:

```json
{{
  "General": {{
    "Type": "...",
    "Number_of_people": "...",
    "Companion": "...",
    "Transportation": "...",
    "Time": "...",
    "City": "...",
    "District": "...",
    "Price_range": "...",
    "
  }},
  "Hotel": {{
    "Requirements": ...,
    "Amenities": [...],
    "Style": [...]
  }},
  "Restaurant": {{
    "Requirements": ...,
    "Restaurant_Type": "...",
    "Suitable_For": "..."
  }},
  "TouristAttraction": {{
    "Attraction_Type": "..."
  }}
}}

```
IMPORTANT RULES:
1. For lists (Amenities, Style), RETURN null if none are EXPLICITLY mentioned. Do NOT make assumptions or add information that isn't clearly stated or mentioned
2. Keep output strictly aligned with the provided lists

Ensure the JSON is valid. Use null for any unspecified information.
After the JSON output, add a note in Vietnamese:

"Nếu bạn cần thay đổi hoặc bổ sung bất kỳ thông tin nào, vui lòng cho tôi biết."
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | st.session_state.model
#end region

ask_template = """
You are an AI travel assistant chatbot. Analyze the following travel request:

Request: "{travel_output_json}"

### **Core Rules:**

1. **Identify Required Fields:**
    - Identify fields that are marked as "required" in the prompt.
    - If a required field is **null**, generate a question to clarify the user's preference. 

2. **STRICTLY DO NOT** generate questions for:
    - Fields with any **NON-NULL** value.
    - Fields without "required" marking in the prompt.

3. **City Validation:**
    - If the "City" field has a value but is not in the `{city_list}`, ask the user if they want to change the city.

4. **Additional Questions:**
    - Only ask additional questions about hotels, restaurants, or tourist attractions if all required fields in the "General" section have non-null values.

5. Questions about `"Time"` and `"Type"` MUST be ASKED FIRST ONLY if these fields are NULL
---

### **Verification Process:**
1. For the `General` section:
   - **Type** (required): Generate question ONLY if `Type` is `null`.
   - **Number_of_people** (required): Generate question ONLY if `Number_of_people` is `null`
   - **Companion** (required): Generate question ONLY if `Companion` is `null`.
   - **Transportation** (required):Generate question ONLY if `Transportation` is `null`.
   - **Time** (required): Generate question ONLY if `Time` is `null`.
   - **Price_range** (required): Generate question ONLY if `Price_range` is `null`.

2. For City validation:
   - If `"City"` is not in `{city_list}` but has a value, ask if the user wants to change it.

3. Additional Question (when General is fully completed):
   - If ALL required `General` fields have NON-NULL values, ask:
     **"Bạn có muốn bổ sung thêm yêu cầu gì cho khách sạn, nhà hàng, hoặc địa điểm tham quan không?"**

4. STRICTLY SKIP any field with a non-`null` value.

---

### **Question Templates (ONLY use if field is NULL AND marked with *must ask question if this field is null, else not*):**
1. If `"Type"` is null, ask:  
   **"Bạn muốn tìm loại hình du lịch nào? (Ví dụ: Food Tour, Văn hóa, Thư giãn, hoặc Trải nghiệm)"**
   Ignore the question about Type if only ask for one of Hotels, Restaurants, or Tourist Attractions.
   
2. If `"Number_of_people"` is null, ask:  
   **"Bạn đi bao nhiêu người? (Ví dụ: 1, 2, hoặc nhóm lớn hơn)"**

3. If `"Companion"` is null, ask:  
   **"Bạn đi cùng ai? (Bạn bè, Gia đình, hoặc Đồng nghiệp)"**

4. If `"Transportation"` is null, ask:  
   **"Bạn sẽ di chuyển bằng phương tiện gì? (Ví dụ: xe hơi tự lái, xe máy, hoặc phương tiện công cộng)"**

5. If `"Time"` is null, ask:  
   **"Bạn có kế hoạch đi vào thời gian nào không? (Ngày cụ thể hoặc khoảng thời gian)"**

6. If `"Price_range"` is null, ask:  
   **"Bạn muốn ngân sách cho chuyến đi này là bao nhiêu (thấp, trung bình, cao)?"**

7. Additional Question (when General is complete):
   **"Bạn có muốn bổ sung thêm yêu cầu gì cho khách sạn, nhà hàng, hoặc địa điểm tham quan không?"**

### **Special Case - City Validation:**
If City has a value but not in {city_list}:
**"Hiện tại chúng tôi chưa cung cấp dịch vụ cho thành phố này mà chỉ có tại {city_list}, liệu bạn có muốn thay đổi thành phố không?"**

---

### **Output Format:**
1. Output questions ONLY for fields marked as `required` in the prompt and STRICTLY null.
2. Add city validation question if needed.
3. If ALL required `General` fields are NON-NULL, add the question about additional requirements for hotels, restaurants, or attractions.
4. End with: **"Nếu bạn cần thay đổi hoặc bổ sung bất kỳ thông tin nào, vui lòng cho tôi biết."**

---

### **Example Output:**
If the JSON input has:
- `"Transportation"`: `null`
- `"Time"`: `null`
- `"City"`: `"Đà Nẵng"` (not in `{city_list}`),
  
The output will be:

```plaintext
Bạn sẽ di chuyển bằng phương tiện gì? (Ví dụ: xe hơi tự lái, xe máy, hoặc phương tiện công cộng)

Bạn có kế hoạch đi vào thời gian nào không? (Ngày cụ thể hoặc khoảng thời gian)

Hiện tại chúng tôi chưa cung cấp dịch vụ cho thành phố này mà chỉ có tại ['Hà Nội'], liệu bạn có muốn thay đổi thành phố không?

Nếu bạn cần thay đổi hoặc bổ sung bất kỳ thông tin nào, vui lòng cho tôi biết.
"""
ask_prompt = ChatPromptTemplate.from_template(ask_template)
ask_chain = ask_prompt | st.session_state.model 

updated_query = """
You are an AI travel suggestion chatbot. Analyze the following travel request:

Update request: "{update_travel_request}"

Extract general requirements from request while following these rules:
1. IMPORTANT: Preserve ALL non-null values from the initial request JSON
2. Only update fields that are null in the initial request OR if the city is explicitly changed
3. For new information, extract the following:

**General Requirements:**
- Type: ONLY CLASSIFY INTO TWO TYPES from {travel_type_list}. Analyze the response and map to:
  "Nghỉ dưỡng" if response mentions/implies relaxation-focused activities:
    Keywords to check:
    - "nghỉ mát", "nghỉ dưỡng", "thư giãn"
    - "resort", "spa", "biển"
    - "nghỉ ngơi", "thư thái"
    - "resort", "khách sạn sang trọng"
    Examples:
    - Response: "food tour" -> classify as: "Khám phá"
    - Response: "nghỉ dưỡng" -> classify as: "Nghỉ dưỡng"
    
  "Khám phá" if response mentions/implies exploration and activity-focused activities:
    Keywords to check:
    - "khám phá", "tham quan", "trải nghiệm"
    - "du lịch", "phượt", "tour"
    - "văn hóa", "ẩm thực", "food tour"
    - "địa điểm", "danh lam thắng cảnh"
    Examples:
    - Response: "trải nghiệm văn hóa" -> classify as: "Khám phá"
    - Response: "địa điểm tham quan" -> classify as: "Khám phá"
- Number_of_people: Extract the number of people.
- Companions: Extract the companions mentioned in the request and translated it if it needed, must be one from this list: {companion_list}.
- Transportation: Identify the transportation method mentioned in the request and translated, convert it if it needed, transportation must be one from this list: {transport_list}.
- Time: Any specific dates or time ranges mentioned.
- City: The mentioned city (without "city" or "province") and must be one from this list: {city_list}.
- Price_range: Specify as "low", "medium", or "high" based on the request.

**For Hotels, also identify:**
- Requirements: A summary text of specific requirements or preferences mentioned.
- Amenities: IMPORTANT - ONLY include amenities from {amenities_list} if EXPLICITLY mentioned in the request. 
  Examples:
  - If request says "need hotel with pool and gym" → include ["Pool", "Gym"]
  - If request doesn't mention any amenities → return null
  - Do NOT assume or add amenities that weren't specifically mentioned
- Style: Only include styles from this list if explicitly mentioned in the request: {style_list} or else return null

**For Restaurants, also identify:**
- Requirements: A summary text of specific requirements or preferences mentioned.
- Restaurant_Type: From this list: {restaurant_type_list}
- Suitable_For: From this list: {suitable_for_list}

**For Tourist Attractions, also identify:**
- Requirements: A list of specific requirements or preferences mentioned.
- Attraction_Type: From this list: {attraction_type_list}

Initial request: "{travel_output_json}"

Merge the initial request with any updates, prioritizing:
1. Keeping all non-null values from initial request
2. Only updating null fields or explicitly changed city
3. Using the following JSON format:

```json
{{
  "General": {{
    "Type": "...",
    "Number_of_people": "...",
    "Companion": "...",
    "Transportation": "...",
    "Time": "...",
    "City": "...",
    "District": "...",
    "Price_range": "...",
    "
  }},
  "Hotel": {{
    "Requirements": ...,
    "Amenities": [...],
    "Style": [...]
  }},
  "Restaurant": {{
    "Requirements": ...,
    "Restaurant_Type": "...",
    "Suitable_For": "..."
  }},
  "TouristAttraction": {{
    "Attraction_Type": "..."
  }}
}}

```

IMPORTANT VERIFICATION STEPS:
1. Before outputting, for all other fields, verify that all non-null values from the initial request are preserved unless explicitly changed in the update request.
2. Check if the update is a response to the Type question. If yes, analyze the response using the keyword mapping above
3. Classify into either "Nghỉ dưỡng" or "Khám phá"

Ensure the JSON is valid. Use null for any unspecified information.
After the JSON output, add a note in Vietnamese:

"Nếu bạn cần thay đổi hoặc bổ sung bất kỳ thông tin nào, vui lòng cho tôi biết."
"""
update_prompt = ChatPromptTemplate.from_template(updated_query)
update_chain = update_prompt | st.session_state.model
#ham def lay json file

def user_requires(chain, query, travel_type_list, companion_list, transport_list, city_list, district_list, 
                  amenities_list_str, style_list_str, res_type_list_str, res_suit_list_str, att_type_list_str):
    response = chain.invoke({
        "travel_request": query,
        "travel_type_list": travel_type_list,
        "companion_list": companion_list,
        "transport_list": transport_list,
        "city_list": city_list,
        "district_list": district_list,
        "amenities_list": amenities_list_str,
        "style_list": style_list_str,
        "restaurant_type_list": res_type_list_str,
        "suitable_for_list": res_suit_list_str,
        "attraction_type_list": att_type_list_str
    })

    # Extract and parse the JSON response
    try:
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            result_dict = json.loads(json_match.group(0))
            
            # # Print the JSON result
            # print("Extracted JSON Result:")
            # print(json.dumps(result_dict, indent=2, ensure_ascii=False))
            return result_dict
        else:
            # print("No JSON object found in the response.")
            return None
    except json.JSONDecodeError as e:
        # print("Failed to decode JSON:", e)
        # print("Raw response:", response.content)
        return None
#ketqua tra ve tu llms

def ask_user(ask_chain, response, travel_type_list, companion_list, transport_list, city_list, district_list, 
                  amenities_list_str, style_list_str, res_type_list_str, res_suit_list_str, att_type_list_str):
    response1 = ask_chain.invoke({
        "travel_output_json": response,
        "travel_type_list": travel_type_list,
        "companion_list": companion_list,
        "transport_list": transport_list,
        "city_list": city_list,
        "district_list": district_list,
        "amenities_list": amenities_list_str,
        "style_list": style_list_str,
        "restaurant_type_list": res_type_list_str,
        "suitable_for_list": res_suit_list_str,
        "attraction_type_list": att_type_list_str
    })

    st.session_state['contents'].append({"role": "assistant", "content":"Cảm ơn bạn đã cung cấp thông tin! Tuy nhiên, tôi cần thêm một số thông tin để giúp bạn tốt hơn:"})
    # print(response1.content)
    user_responses = {}

    # Process each line in the response content as a separate question
    questions = response1.content.splitlines()
    for question in questions:
        # Remove "plaintext:" prefix if it exists and trim whitespace
        question = question.replace("```plaintext", "").replace("```", "").strip()
        st.session_state['contents'].append({"role": "assistant", "content":f"{question}"})
        # Skip empty lines and avoid re-asking filled fields
        if not question or "Nếu bạn cần thay đổi hoặc bổ sung bất kỳ thông tin nào" in question:
            st.session_state['contents'].append({"role": "assistant", "content":f'{question}'})  # Print closing statement without asking for input
            continue
        
        # Ask the user for input and store the response
        user_input = st.chat_input(f"{question} ")
        while user_input is not None:
            user_responses[question] = f"[{user_input.strip()}]"
        
    # Print the responses collected for review
    # print("\nCollected User Responses:")
    # for field, answer in user_responses.items():
    #     print(f"{field}: {answer}")
    
    st.session_state['contents'].append({"role": "assistant", "content": "Nếu bạn cần thay đổi hoặc bổ sung bất kỳ thông tin nào, vui lòng cho tôi biết."})
    return user_responses
#ham update json

def update_requires(update_chain, first_respond, travel_type_list, companion_list, transport_list, city_list, update_respond,
                    amenities_list_str, style_list_str, res_type_list_str, res_suit_list_str, att_type_list_str):
    response = update_chain.invoke({
        "update_travel_request": update_respond,
        "travel_type_list": travel_type_list,
        "companion_list": companion_list,
        "transport_list": transport_list,
        "city_list": city_list,
        "travel_output_json": first_respond,
        "amenities_list": amenities_list_str,
        "style_list": style_list_str,
        "restaurant_type_list": res_type_list_str,
        "suitable_for_list": res_suit_list_str,
        "attraction_type_list": att_type_list_str
    })

    # Extract and parse the JSON response
    try:
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            result_dict = json.loads(json_match.group(0))
            
            # Print the JSON result
            # print("Extracted JSON Result:")
            # print(json.dumps(result_dict, indent=2, ensure_ascii=False))
            return result_dict
        else:
            # print("No JSON object found in the response.")
            return None
    except json.JSONDecodeError as e:
        # print("Failed to decode JSON:", e)
        # print("Raw response:", response.content)
        return None
# Khởi tạo `float_init`
float_init(theme=True, include_unstable_primary=False)

# Hàm xử lý nội dung chat
def chat_content():
    # Lưu tin nhắn người dùng vào session_state
    user_input = st.session_state.content
    # Thêm tin nhắn của người dùng vào list trong session_state
    st.session_state['contents'].append({"role": "user", "content": user_input})
    json_file=user_requires(chain, user_input, travel_type_list, companion_list, transport_list, city_list, district_list, 
                  amenities_list_str, style_list_str, res_type_list_str, res_suit_list_str, att_type_list_str)
    ask_again_respond = ask_user(ask_chain, json_file, travel_type_list, companion_list, transport_list, city_list, district_list, amenities_list_str, style_list_str, res_type_list_str, res_suit_list_str, att_type_list_str) 
    # Thêm phản hồi của bot vào list trong session_state
    update_requires_respond = update_requires(update_chain, ask_again_respond, travel_type_list, companion_list, transport_list, city_list, ask_again_respond,amenities_list_str, style_list_str, res_type_list_str, res_suit_list_str, att_type_list_str)
    # st.session_state['contents'].append({"role": "assistant", "content": bot_response})
    return update_requires_respond

# Khởi tạo `contents` để lưu lịch sử hội thoại nếu chưa có
if 'contents' not in st.session_state:
    st.session_state['contents'] = []
    border = False
else:
    border = True

# Chia bố cục thành 2 cột chiếm hết chiều ngang màn hình
col1, col2 = st.columns([1, 1])  # Tỷ lệ 1:1, bạn có thể thay đổi tỷ lệ này tùy ý

# Cột bên trái: Giao diện chat
with col1:
    with st.container(border=border):
        with st.container():
            # Ô nhập chat cố định
            st.chat_input("Nhập yêu cầu của bạn...", key='content', on_submit=chat_content) 
            button_b_pos = "0rem"
            button_css = float_css_helper(width="2.2rem", bottom=button_b_pos, transition=0)
            float_parent(css=button_css)

        # Hiển thị lịch sử hội thoại với icon của bot và người dùng

        for c in st.session_state.contents:
            if isinstance(c, dict):  # Kiểm tra chắc chắn rằng `c` là một từ điển
                # Hiển thị tin nhắn của người dùng
                if c.get("role") == "user":
                    with st.chat_message(name="user"):
                        st.write(c.get("content", ""))
            
                # Hiển thị phản hồi của bot với icon
                elif c.get("role") == "assistant":
                    with st.chat_message(name="assistant"):
                        st.write(c.get("content", ""))

# Mock dữ liệu địa điểm (sử dụng dữ liệu thực nếu có từ database)
mock_locations = [
    {"name": "Hồ Gươm", "lat": 21.0285, "lon": 105.8542, "description": "Một biểu tượng của Hà Nội."},
    {"name": "Văn Miếu", "lat": 21.0287, "lon": 105.8354, "description": "Quần thể di tích lịch sử và văn hóa."},
    {"name": "Lăng Bác", "lat": 21.0368, "lon": 105.8342, "description": "Nơi an nghỉ của Chủ tịch Hồ Chí Minh."},
]

# Cột bên phải: Bản đồ và danh sách địa điểm
with col2:
    with st.container(border=True):
        st.header("Bản đồ & Danh sách địa điểm")

        # Tạo bản đồ Folium
        map_center = [21.0285, 105.8542]  # Tọa độ trung tâm Hà Nội
        map_object = folium.Map(location=map_center, zoom_start=14)

        # Thêm marker cho các địa điểm
        for location in mock_locations:
            folium.Marker(
                location=[location["lat"], location["lon"]],
                popup=f"{location['name']}: {location['description']}",
                icon=folium.Icon(color="green"),
            ).add_to(map_object)

        # Hiển thị bản đồ
        st_data = st_folium(map_object, width=700, height=500)

        # Hiển thị danh sách địa điểm
        st.subheader("Danh sách các địa điểm")
        for location in mock_locations:
            st.write(f"**{location['name']}**: {location['description']}")

