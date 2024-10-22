import psycopg2
import streamlit as st
from streamlit_folium import st_folium
import folium
import random
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re
page = st.title("Travel Recommendation System from USTH")
if "api" not in st.session_state:
    st.session_state.api=None
if 'model' not in st.session_state:
    st.session_state.model=None

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

@st.dialog("cai dat api_google, postgresql_url")
def setup_api_url():
    st.markdown(
        """
        input API and db url:
        """
    )
    google_api=st.text_input("API:","")
    postgres_url = st.text_input("Postgres URL:", "")
    if st.button("Lưu"):
        st.session_state.postgres_url = postgres_url
        st.session_state.api=google_api
        st.rerun()

if st.session_state.api is None or st.session_state.postgres_url is None:
    setup_api_url()
if st.session_state.api and st.session_state.model is None:
    st.session_state.model=get_gemini(st.session_state.api)

# Kiểm tra nếu postgres_url chưa được nhập, yêu cầu người dùng nhập
# Hộp nhập để yêu cầu nhập postgres_url trước khi sử dụng ứng dụng
def get_cautraloi(input):
    template="""Pretend you are a local resident in Hanoi and answer this question: {question}"""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | st.session_state.model
    response=chain.invoke (
        {"question" : input}
    )
    response_gemini = str(response.content)
    return response_gemini
# Chỉ tiếp tục chạy nếu đã có postgres_url
if 'postgres_url' in st.session_state and st.session_state.postgres_url:
    # Hàm kết nối và truy vấn dữ liệu từ cơ sở dữ liệu theo loại
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
    @st.cache_data
    def get_hotel_style():
        conn = psycopg2.connect(st.session_state.postgresql_url)
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
    # Hàm kết nối và truy vấn dữ liệu từ cơ sở dữ liệu theo loại
    @st.cache_data
    def get_data_by_type(data_type):
        # Kết nối với cơ sở dữ liệu PostgreSQL
        conn = psycopg2.connect(st.session_state.postgres_url)
        cur = conn.cursor()

        # Chuyển search_path để sử dụng schema đúng
        cur.execute("""SET search_path TO travel_database, public;""")
        
        # Chọn đúng cột id theo loại địa điểm
        if data_type == "Hotel":
            id_col = "hotel_id"
        elif data_type == "Restaurant":
            id_col = "res_id"
        else:
            id_col = "attraction_id"
        
        # Truy vấn dữ liệu dựa trên loại, loại bỏ những địa điểm có location NULL
        query = f"""
            SELECT {id_col}, name, (address).street, (address).district, (address).city, ST_Y(location), ST_X(location), description
            FROM {data_type}
            WHERE (address).city = 'Hà Nội' AND location IS NOT NULL;
        """
        cur.execute(query)
        data = cur.fetchall()

        # Đóng kết nối cơ sở dữ liệu
        cur.close()
        conn.close()

        return data, id_col

    # Chọn loại dữ liệu: Restaurant, TouristAttraction, Hotel
    data_type = st.selectbox("Chọn loại địa điểm", ["Restaurant", "TouristAttraction", "Hotel"])

    # Kiểm tra nếu dữ liệu của loại đã chọn chưa được lưu trong session_state thì mới query
    if f'{data_type}_data' not in st.session_state:
        st.session_state[f'{data_type}_data'], st.session_state[f'{data_type}_id_col'] = get_data_by_type(data_type)

    # Lấy dữ liệu từ session_state
    data = st.session_state[f'{data_type}_data']
    id_col = st.session_state[f'{data_type}_id_col']

    # Random chọn 50 địa điểm từ dữ liệu
    if 'selected_data' not in st.session_state or st.session_state['data_type'] != data_type:
        random.shuffle(data)
        st.session_state['selected_data'] = data[:50]  # Lấy 50 địa điểm ngẫu nhiên
        st.session_state['data_type'] = data_type

    # Tạo tiêu đề cho ứng dụng
    st.title(f"Nhấn vào điểm để xem thông tin chi tiết ({data_type})")

    # Tạo layout với hai cột: cột cho bản đồ và cột cho thông tin chi tiết
    col1, col2 = st.columns([2, 1])  # Tỷ lệ 2:1 giữa bản đồ và thông tin

    # Tạo bản đồ với Folium trong cột đầu tiên
    with col1:
        mymap = folium.Map(location=[21.0285, 105.8542], zoom_start=14)
        
        # Thêm các marker cho từng địa điểm
        locations = {}
        for item in st.session_state['selected_data']:
            loc_id, name, street, district, city, lat, lon, description = item
            if lat is not None and lon is not None:  # Kiểm tra location có giá trị
                address = f"{street}, {district}, {city}"
                locations[name] = {
                    "id": loc_id,
                    "type": data_type,
                    "coordinates": [lat, lon],
                    "description": description,
                    "address": address
                }
                folium.Marker(
                    location=[lat, lon],
                    popup=name,
                    icon=folium.Icon(color="green")
                ).add_to(mymap)

        # Hiển thị bản đồ trong cột 1
        st_data = st_folium(mymap, width=700, height=500)

    # Sử dụng session_state để lưu trạng thái khi chọn địa điểm
    if 'scenarios' not in st.session_state:
        st.session_state.scenarios = {}  # Dictionary để lưu các kịch bản và hội thoại

    if 'last_selected' not in st.session_state:
        st.session_state.last_selected = None

    # Hiển thị thông tin chi tiết trong cột thứ hai
    with col2:
        # Kiểm tra nếu người dùng đã click vào một marker
        if st_data and st_data["last_object_clicked"]:
            clicked_location = st_data["last_object_clicked"]["lat"], st_data["last_object_clicked"]["lng"]

            # Tìm thông tin địa điểm dựa trên tọa độ đã click
            for name, info in locations.items():
                if clicked_location == tuple(info["coordinates"]):
                    # Hiển thị thông tin chi tiết của địa điểm đã chọn
                    st.subheader(f"Thông tin chi tiết: {name}")
                    st.write(info["description"])
                    st.write(f"Địa chỉ: {info['address']}")

                    # Lưu địa điểm đã click vào session_state
                    st.session_state.last_selected = name

                    break
                    
    # ---- Thao tác với các nút và hội thoại trong sidebar ----
    with st.sidebar:
        # Thêm nút "Tạo kịch bản mới"
        if st.button("Tạo kịch bản mới"):
            new_scenario_name = f"Kịch bản {len(st.session_state.scenarios) + 1}"
            st.session_state.scenarios[new_scenario_name] = {
                "locations": [],
                "conversations": []
            }  # Tạo kịch bản với danh sách địa điểm và hội thoại
            st.success(f"Đã tạo {new_scenario_name}")

        # Lựa chọn kịch bản hiện tại
        scenario_options = list(st.session_state.scenarios.keys())
        selected_scenario = st.selectbox("Chọn kịch bản để lưu", scenario_options)

        # Thêm nút xóa kịch bản
        if st.button("Xóa kịch bản"):
            if selected_scenario in st.session_state.scenarios:
                del st.session_state.scenarios[selected_scenario]
                st.success(f"Đã xóa kịch bản {selected_scenario}")
            else:
                st.warning("Không tìm thấy kịch bản để xóa.")

        # Thêm nút Save địa điểm trong sidebar
        if st.button("Save địa điểm"):
            if st.session_state.last_selected and st.session_state.last_selected in locations:
                selected_info = locations.get(st.session_state.last_selected)  # Sử dụng get để tránh lỗi KeyError
                # Kiểm tra xem địa điểm đã được lưu trong kịch bản chưa, nếu chưa thì lưu
                if selected_info and selected_info not in st.session_state.scenarios[selected_scenario]["locations"]:
                    # Lưu địa điểm vào kịch bản đã chọn
                    st.session_state.scenarios[selected_scenario]["locations"].append({
                        "id": selected_info["id"],
                        "type": selected_info["type"],
                        "name": st.session_state.last_selected,
                        "address": selected_info["address"]
                    })
                    st.success(f"Đã lưu {st.session_state.last_selected} vào {selected_scenario}")
            elif not selected_scenario:
                st.warning("Vui lòng tạo kịch bản trước khi lưu.")
            else:
                st.warning("Vui lòng chọn một địa điểm hợp lệ trước khi lưu.")

        # Kiểm tra biến conversation_input trong session_state
        if "conversation_input" not in st.session_state:
            st.session_state.conversation_input = ""

        # Nhập hội thoại cho kịch bản
        if selected_scenario:
            conversation_input = st.chat_input("Bạn muốn hỏi gì?")
            
            if conversation_input:
                # Thêm hội thoại người dùng vào kịch bản đã chọn
                st.session_state.scenarios[selected_scenario]["conversations"].append(f"User: {conversation_input}")
                # Thêm phản hồi của bot
                bot_response=get_cautraloi(conversation_input)
                st.session_state.scenarios[selected_scenario]["conversations"].append(f"Bot:{bot_response} ")

            # Hiển thị lịch sử chat từ kịch bản đã chọn (không bị lặp)
            st.write("Lịch sử hội thoại:")
            if selected_scenario in st.session_state.scenarios:
                for idx, conversation in enumerate(st.session_state.scenarios[selected_scenario]["conversations"]):
                    st.write(f"{idx + 1}: {conversation}")

    # ---- Hiển thị dữ liệu thô trên trang chính ----
    st.header("Dữ liệu thô các kịch bản và địa điểm đã lưu")
    if st.session_state.scenarios:
        st.json(st.session_state.scenarios)  # Hiển thị dữ liệu thô dạng JSON
    else:
        st.write("Chưa có kịch bản nào.")
