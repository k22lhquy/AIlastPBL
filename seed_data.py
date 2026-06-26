# """
# Seed script: Tự động tạo dữ liệu test cho hệ thống
# - Tạo 3 tài khoản giả
# - Mỗi tài khoản tạo 2 Q&A và trả lời lẫn nhau, và tự follow/like lẫn nhau
# (Người dùng đã yêu cầu bỏ phần tạo Community Posts tự động)
# Chạy: python seed_data.py
# """
# import requests
# import io
# import json
# import base64

# BASE_URL = "http://localhost:8000"

# # ──────────────────────────────────────────────
# # BƯỚC 1: Định nghĩa người dùng giả
# # ──────────────────────────────────────────────
# USERS = [
#     {"username": "thantai_rice", "password": "Test@1234"},
#     {"username": "dinhduong_blog",   "password": "Test@1234"},
#     {"username": "chuyengia_keto", "password": "Test@1234"},
# ]

# # ──────────────────────────────────────────────
# # BƯỚC 2: Định nghĩa Q&A content
# # ──────────────────────────────────────────────
# QA_DATA = [
#     {
#         "body": "Gạo lứt có nhiều protein hơn gạo trắng không?",
#         "tags": ["gạo", "dinh dưỡng", "protein"],
#         "answers": [
#             "Gạo lứt có hàm lượng protein tương đương gạo trắng (khoảng 7-8g/100g), nhưng gạo lứt giữ nguyên cám và mầm nên giàu xơ, vitamin B, khoáng chất hơn hẳn.",
#         ]
#     },
#     {
#         "body": "Thành phần dinh dưỡng chính trong gạo bao gồm những gì?",
#         "tags": ["gạo", "dinh dưỡng", "thành phần"],
#         "answers": [
#             "Gạo chủ yếu chứa: Tinh bột (70-80%), Protein (6-8%), Chất béo (0.5-1%), Chất xơ, Vitamin nhóm B (B1, B3, B6), Khoáng chất (Sắt, Kẽm, Magie).",
#             "Ngoài các thành phần chính, gạo còn chứa các axit amin thiết yếu như glutamic acid, aspartic acid và leucine, đóng vai trò quan trọng trong chuyển hóa cơ thể."
#         ]
#     },
#     {
#         "body": "Chế độ ăn keto có nên bao gồm gạo không?",
#         "tags": ["keto", "chế độ ăn", "gạo", "carb"],
#         "answers": [
#             "Chế độ keto nghiêm ngặt không bao gồm gạo vì gạo chứa nhiều carb (77g/100g), sẽ phá vỡ trạng thái ketosis. Người theo keto thường thay bằng rau củ ít carb."
#         ]
#     },
#     {
#         "body": "Vitamin B1 (Thiamine) trong gạo có tác dụng gì với cơ thể?",
#         "tags": ["vitamin B1", "thiamine", "gạo", "dinh dưỡng"],
#         "answers": [
#             "Vitamin B1 (Thiamine) trong gạo có vai trò thiết yếu trong chuyển hóa năng lượng từ carbohydrate, hỗ trợ hoạt động của hệ thần kinh và tim mạch. Thiếu B1 gây bệnh tê phù (beriberi)."
#         ]
#     },
#     {
#         "body": "So sánh chỉ số GI của gạo trắng và gạo lứt?",
#         "tags": ["GI", "gạo", "đường huyết", "tiểu đường"],
#         "answers": [
#             "Gạo trắng có chỉ số GI cao (72-83), gây tăng đường huyết nhanh. Gạo lứt có GI thấp hơn (50-66) nhờ chứa nhiều xơ làm chậm hấp thu glucose. Người tiểu đường typ 2 nên ưu tiên gạo lứt."
#         ]
#     },
# ]

# # ──────────────────────────────────────────────
# # UTILITY FUNCTIONS
# # ──────────────────────────────────────────────
# def register_user(user):
#     r = requests.post(f"{BASE_URL}/auth/register", json=user)
#     return r.json()

# def login_user(user):
#     r = requests.post(f"{BASE_URL}/auth/login", json=user)
#     d = r.json()
#     if d.get("success"):
#         return d["data"]["access_token"]
#     return None

# def auth_headers(token):
#     return {"Authorization": f"Bearer {token}"}

# def extract_user_id(token):
#     # JWT decoding payload base64 snippet without any 3rd party lib
#     try:
#         payload_b64 = token.split('.')[1]
#         payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
#         payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
#         return payload.get("user_id")
#     except:
#         return None

# def create_question(token, body, tags):
#     r = requests.post(
#         f"{BASE_URL}/qa/questions",
#         json={"body": body, "tags": tags},
#         headers=auth_headers(token)
#     )
#     return r.json()

# def create_answer(token, question_id, body):
#     r = requests.post(
#         f"{BASE_URL}/qa/questions/{question_id}/answers",
#         data={"body": body},
#         headers=auth_headers(token)
#     )
#     return r.json()

# def like_user(token, user_id):
#     r = requests.patch(f"{BASE_URL}/users/{user_id}/like", headers=auth_headers(token))
#     return r.json()


# # ──────────────────────────────────────────────
# # MAIN SEED LOGIC
# # ──────────────────────────────────────────────
# def main():
#     print("═" * 55)
#     print("🌱  SEED SCRIPT - Tạo dữ liệu test (Q&A Only)")
#     print("═" * 55)

#     # Step 1: Register & Login
#     tokens = {}
#     user_ids = {}
#     for u in USERS:
#         print(f"\n👤 Đăng ký/Đăng nhập: {u['username']}")
#         reg = register_user(u)
#         if not reg.get("success"):
#             print(f"   ⚠️  Đã tồn tại hoặc lỗi: {reg.get('message')}")

#         token = login_user(u)
#         if not token:
#             print(f"   ❌ Đăng nhập thất bại cho {u['username']}")
#             continue

#         uid = extract_user_id(token)
#         tokens[u["username"]] = token
#         user_ids[u["username"]] = uid
#         print(f"   ✅ Đăng nhập thành công (ID: {uid})")

#     if not tokens:
#         print("\n❌ Không có token nào. Dừng script.")
#         return

#     token_list = list(tokens.values())
#     user_id_list = list(user_ids.values())

#     # Step 2: Create Q&As and answers
#     print("\n" + "═" * 55)
#     print("❓ TẠO Q&A & TRẢ LỜI")
#     print("═" * 55)

#     question_ids = []
#     for i, qa in enumerate(QA_DATA):
#         author_token = token_list[i % len(token_list)]
#         print(f"\n📝 Q: {qa['body'][:60]}...")
#         q_res = create_question(author_token, qa["body"], qa["tags"])
#         q_id = q_res.get("data", {}).get("id")
#         if not q_id:
#             print(f"   ❌ Lỗi tạo câu hỏi: {q_res}")
#             continue
#         question_ids.append(q_id)
#         print(f"   ✅ Tạo thành công (ID: {q_id})")

#         # Create answers from different users
#         for j, answer_body in enumerate(qa["answers"]):
#             answerer_idx = (i + j + 1) % len(token_list)
#             ans_res = create_answer(token_list[answerer_idx], q_id, answer_body)
#             if ans_res.get("success"):
#                 print(f"   💬 Câu trả lời bởi user_{answerer_idx + 1}: OK")
#             else:
#                 print(f"   ⚠️  Lỗi trả lời: {ans_res}")


#     # Step 3: Like each other's profiles
#     print("\n" + "═" * 55)
#     print("❤️  TƯƠNG TÁC LIKE PROFILE")
#     print("═" * 55)
#     for i, (uname, uid) in enumerate(user_ids.items()):
#         for j, liker_token in enumerate(token_list):
#             if j != i:
#                 like_user(liker_token, uid)
#         print(f"   ❤️  Profile @{uname} nhận {len(token_list)-1} likes")


#     # Summary
#     print("\n" + "═" * 55)
#     print("✅ SEED HOÀN THÀNH!")
#     print("═" * 55)
#     print(f"👥 Tài khoản: {len(tokens)}")
#     print(f"❓ Câu hỏi Q&A: {len(question_ids)}")
#     print()
#     print("💡 Giờ bạn có thể tự tạo bài Post và test Chatbot!")
#     print("═" * 55)


# if __name__ == "__main__":
#     main()


import requests
import json
import base64

BASE_URL = "http://localhost:8000"

# ──────────────────────────────────────────────
# TÀI KHOẢN DUY NHẤT
# ──────────────────────────────────────────────
USER = {
    "username": "lehuuquy",
    "password": "12345678"
}

# ──────────────────────────────────────────────
# 20 BÀI Q&A NHIỀU CHỦ ĐỀ
# ──────────────────────────────────────────────
QA_DATA = [
{
"body": "Uống bao nhiêu nước mỗi ngày là đủ?",
"tags": ["y_te", "suc_khoe"],
"answers": [
"Người trưởng thành thường cần khoảng 2 lít nước mỗi ngày.",
"Lượng nước cần thiết phụ thuộc cân nặng và mức độ vận động.",
"Nên uống nước đều đặn thay vì đợi khát mới uống.",
"Mùa nóng hoặc khi vận động mạnh cần bổ sung nhiều nước hơn.",
"Nước đóng vai trò quan trọng trong quá trình trao đổi chất."
]
},
{
"body": "Ngủ bao nhiêu tiếng mỗi ngày là tốt nhất?",
"tags": ["y_te", "giac_ngu"],
"answers": [
"Người trưởng thành nên ngủ từ 7 đến 9 tiếng.",
"Ngủ đủ giúp tăng khả năng tập trung.",
"Thiếu ngủ có thể ảnh hưởng đến trí nhớ.",
"Chất lượng giấc ngủ cũng quan trọng như thời lượng ngủ.",
"Nên duy trì giờ ngủ cố định mỗi ngày."
]
},
{
"body": "Vitamin C có tác dụng gì đối với cơ thể?",
"tags": ["y_te", "vitamin"],
"answers": [
"Vitamin C hỗ trợ hệ miễn dịch.",
"Giúp cơ thể hấp thụ sắt tốt hơn.",
"Có vai trò chống oxy hóa.",
"Hỗ trợ quá trình lành vết thương.",
"Có nhiều trong cam, quýt và ổi."
]
},
{
"body": "Ăn nhiều rau xanh có lợi ích gì?",
"tags": ["y_te", "dinh_duong"],
"answers": [
"Rau xanh cung cấp nhiều chất xơ.",
"Giúp hỗ trợ hệ tiêu hóa.",
"Cung cấp vitamin và khoáng chất.",
"Có thể giúp giảm nguy cơ bệnh tim mạch.",
"Nên đa dạng các loại rau trong khẩu phần ăn."
]
},
{
"body": "Tại sao cần tiêm vaccine?",
"tags": ["y_te", "vaccine"],
"answers": [
"Vaccine giúp phòng ngừa nhiều bệnh truyền nhiễm.",
"Giúp cơ thể tạo miễn dịch chủ động.",
"Giảm nguy cơ lây lan trong cộng đồng.",
"Nhiều bệnh nguy hiểm đã được kiểm soát nhờ vaccine.",
"Nên tiêm theo lịch khuyến nghị."
]
},
{
"body": "BMI là gì?",
"tags": ["y_te", "can_nang"],
"answers": [
"BMI là chỉ số khối cơ thể.",
"BMI được tính từ cân nặng và chiều cao.",
"Giúp đánh giá tình trạng cân nặng tương đối.",
"BMI không phản ánh hoàn toàn sức khỏe tổng thể.",
"Nên kết hợp với các chỉ số khác khi đánh giá."
]
},
{
"body": "Làm sao để tăng sức đề kháng?",
"tags": ["y_te", "mien_dich"],
"answers": [
"Ăn uống cân bằng dinh dưỡng.",
"Ngủ đủ giấc mỗi ngày.",
"Tập thể dục thường xuyên.",
"Giữ tinh thần thoải mái.",
"Hạn chế thuốc lá và rượu bia."
]
},
{
"body": "Ăn khuya có hại không?",
"tags": ["y_te", "dinh_duong"],
"answers": [
"Ăn khuya thường xuyên có thể ảnh hưởng tiêu hóa.",
"Dễ làm tăng lượng calo nạp vào.",
"Có thể ảnh hưởng chất lượng giấc ngủ.",
"Nên ăn nhẹ nếu thực sự đói.",
"Tránh thực phẩm nhiều dầu mỡ vào buổi tối."
]
},
{
"body": "Tập thể dục bao nhiêu phút mỗi ngày là hợp lý?",
"tags": ["y_te", "the_thao"],
"answers": [
"Khoảng 30 phút mỗi ngày là mức phổ biến.",
"Có thể chia nhỏ thành nhiều khoảng thời gian.",
"Đi bộ nhanh cũng mang lại lợi ích.",
"Quan trọng là duy trì đều đặn.",
"Nên chọn môn phù hợp với thể trạng."
]
},
{
"body": "Tại sao cần khám sức khỏe định kỳ?",
"tags": ["y_te", "kham_benh"],
"answers": [
"Giúp phát hiện bệnh sớm.",
"Theo dõi tình trạng sức khỏe tổng thể.",
"Có thể giảm chi phí điều trị về lâu dài.",
"Nhiều bệnh không có triệu chứng rõ ràng.",
"Nên khám theo khuyến nghị của bác sĩ."
]
},
{
"body": "Cao huyết áp là gì?",
"tags": ["y_te", "tim_mach"],
"answers": [
"Là tình trạng áp lực máu tăng cao.",
"Có thể làm tăng nguy cơ đột quỵ.",
"Thường cần theo dõi lâu dài.",
"Chế độ ăn uống ảnh hưởng nhiều đến huyết áp.",
"Nên kiểm tra huyết áp định kỳ."
]
},
{
"body": "Tiểu đường type 2 là gì?",
"tags": ["y_te", "tieu_duong"],
"answers": [
"Là bệnh liên quan đến rối loạn đường huyết.",
"Thường gặp ở người trưởng thành.",
"Lối sống ảnh hưởng nhiều đến nguy cơ mắc bệnh.",
"Kiểm soát chế độ ăn là rất quan trọng.",
"Nên theo dõi đường huyết thường xuyên."
]
},
{
"body": "Tại sao cần ăn sáng?",
"tags": ["y_te", "dinh_duong"],
"answers": [
"Bữa sáng cung cấp năng lượng đầu ngày.",
"Giúp tăng khả năng tập trung.",
"Có thể giảm cảm giác đói quá mức vào buổi trưa.",
"Nên chọn thực phẩm giàu dinh dưỡng.",
"Không nên bỏ bữa sáng thường xuyên."
]
},
{
"body": "Thiếu máu có biểu hiện gì?",
"tags": ["y_te", "benh_hoc"],
"answers": [
"Có thể gây mệt mỏi.",
"Da xanh xao là dấu hiệu thường gặp.",
"Một số người bị chóng mặt.",
"Thiếu sắt là nguyên nhân phổ biến.",
"Nên kiểm tra nếu có triệu chứng kéo dài."
]
},
{
"body": "Đi bộ có tốt cho tim mạch không?",
"tags": ["y_te", "tim_mach"],
"answers": [
"Đi bộ là hình thức vận động đơn giản.",
"Giúp cải thiện tuần hoàn máu.",
"Có lợi cho sức khỏe tim mạch.",
"Phù hợp với nhiều độ tuổi.",
"Nên duy trì đều đặn mỗi tuần."
]
},
{
"body": "Stress kéo dài ảnh hưởng thế nào đến sức khỏe?",
"tags": ["y_te", "tam_ly"],
"answers": [
"Có thể gây mất ngủ.",
"Ảnh hưởng khả năng tập trung.",
"Làm tăng cảm giác mệt mỏi.",
"Có thể ảnh hưởng huyết áp.",
"Nên tìm cách thư giãn phù hợp."
]
},
{
"body": "Lợi ích của việc ngủ đúng giờ là gì?",
"tags": ["y_te", "giac_ngu"],
"answers": [
"Giúp đồng bộ đồng hồ sinh học.",
"Cải thiện chất lượng giấc ngủ.",
"Hỗ trợ phục hồi cơ thể.",
"Tăng khả năng tập trung ban ngày.",
"Giúp hình thành thói quen tốt."
]
},
{
"body": "Tại sao cần đánh răng hai lần mỗi ngày?",
"tags": ["y_te", "rang_mieng"],
"answers": [
"Giúp giảm mảng bám.",
"Hạn chế sâu răng.",
"Giúp hơi thở thơm mát.",
"Bảo vệ sức khỏe răng miệng.",
"Nên kết hợp dùng chỉ nha khoa."
]
},
{
"body": "Ánh nắng mặt trời có lợi ích gì?",
"tags": ["y_te", "vitamin_d"],
"answers": [
"Giúp cơ thể tổng hợp vitamin D.",
"Hỗ trợ sức khỏe xương.",
"Có thể cải thiện tâm trạng.",
"Nên tiếp xúc ánh nắng hợp lý.",
"Tránh nắng gắt giữa trưa."
]
},
{
"body": "Làm sao để duy trì lối sống lành mạnh?",
"tags": ["y_te", "song_khoe"],
"answers": [
"Ăn uống cân bằng.",
"Ngủ đủ giấc.",
"Tập thể dục thường xuyên.",
"Giữ tinh thần tích cực.",
"Khám sức khỏe định kỳ."
]
}
]


# ──────────────────────────────────────────────
# HÀM TIỆN ÍCH
# ──────────────────────────────────────────────
def register_user(user):
    return requests.post(f"{BASE_URL}/auth/register", json=user).json()

def login_user(user):
    r = requests.post(f"{BASE_URL}/auth/login", json=user).json()
    if r.get("success"):
        return r["data"]["access_token"]
    return None

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def create_question(token, body, tags):
    return requests.post(
        f"{BASE_URL}/qa/questions",
        json={"body": body, "tags": tags},
        headers=auth_headers(token)
    ).json()

def create_answer(token, question_id, body):
    return requests.post(
        f"{BASE_URL}/qa/questions/{question_id}/answers",
        data={"body": body},
        headers=auth_headers(token)
    ).json()

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("🌱 SEED DATA - 1 ACCOUNT + 20 Q&A")

    # Đăng ký (nếu đã tồn tại thì bỏ qua)
    reg = register_user(USER)
    if not reg.get("success"):
        print("⚠️ Tài khoản có thể đã tồn tại, tiếp tục đăng nhập...")

    token = login_user(USER)
    if not token:
        print("❌ Đăng nhập thất bại!")
        return

    print(f"✅ Đăng nhập thành công: {USER['username']}")

    # Tạo 20 câu hỏi và tự trả lời
    for i, qa in enumerate(QA_DATA, 1):

        q = create_question(
            token,
            qa["body"],
            qa["tags"]
        )

        qid = q.get("data", {}).get("id")

        if not qid:
            print(f"❌ Lỗi tạo câu hỏi {i}")
            continue

        for answer in qa["answers"]:
            create_answer(token, qid, answer)

        print(
            f"✅ [{i}/{len(QA_DATA)}] "
            f"{qa['body']} "
            f"({len(qa['answers'])} answers)"
        )

    print("\n🎉 Hoàn tất seed dữ liệu!")

if __name__ == "__main__":
    main()
