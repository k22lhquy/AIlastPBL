"""
Seed script: Tự động tạo dữ liệu test cho hệ thống
- Tạo 3 tài khoản giả
- Mỗi tài khoản tạo 2 Q&A và trả lời lẫn nhau, và tự follow/like lẫn nhau
(Người dùng đã yêu cầu bỏ phần tạo Community Posts tự động)
Chạy: python seed_data.py
"""
import requests
import io
import json
import base64

BASE_URL = "http://localhost:8000"

# ──────────────────────────────────────────────
# BƯỚC 1: Định nghĩa người dùng giả
# ──────────────────────────────────────────────
USERS = [
    {"username": "thantai_rice", "password": "Test@1234"},
    {"username": "dinhduong_blog",   "password": "Test@1234"},
    {"username": "chuyengia_keto", "password": "Test@1234"},
]

# ──────────────────────────────────────────────
# BƯỚC 2: Định nghĩa Q&A content
# ──────────────────────────────────────────────
QA_DATA = [
    {
        "body": "Gạo lứt có nhiều protein hơn gạo trắng không?",
        "tags": ["gạo", "dinh dưỡng", "protein"],
        "answers": [
            "Gạo lứt có hàm lượng protein tương đương gạo trắng (khoảng 7-8g/100g), nhưng gạo lứt giữ nguyên cám và mầm nên giàu xơ, vitamin B, khoáng chất hơn hẳn.",
        ]
    },
    {
        "body": "Thành phần dinh dưỡng chính trong gạo bao gồm những gì?",
        "tags": ["gạo", "dinh dưỡng", "thành phần"],
        "answers": [
            "Gạo chủ yếu chứa: Tinh bột (70-80%), Protein (6-8%), Chất béo (0.5-1%), Chất xơ, Vitamin nhóm B (B1, B3, B6), Khoáng chất (Sắt, Kẽm, Magie).",
            "Ngoài các thành phần chính, gạo còn chứa các axit amin thiết yếu như glutamic acid, aspartic acid và leucine, đóng vai trò quan trọng trong chuyển hóa cơ thể."
        ]
    },
    {
        "body": "Chế độ ăn keto có nên bao gồm gạo không?",
        "tags": ["keto", "chế độ ăn", "gạo", "carb"],
        "answers": [
            "Chế độ keto nghiêm ngặt không bao gồm gạo vì gạo chứa nhiều carb (77g/100g), sẽ phá vỡ trạng thái ketosis. Người theo keto thường thay bằng rau củ ít carb."
        ]
    },
    {
        "body": "Vitamin B1 (Thiamine) trong gạo có tác dụng gì với cơ thể?",
        "tags": ["vitamin B1", "thiamine", "gạo", "dinh dưỡng"],
        "answers": [
            "Vitamin B1 (Thiamine) trong gạo có vai trò thiết yếu trong chuyển hóa năng lượng từ carbohydrate, hỗ trợ hoạt động của hệ thần kinh và tim mạch. Thiếu B1 gây bệnh tê phù (beriberi)."
        ]
    },
    {
        "body": "So sánh chỉ số GI của gạo trắng và gạo lứt?",
        "tags": ["GI", "gạo", "đường huyết", "tiểu đường"],
        "answers": [
            "Gạo trắng có chỉ số GI cao (72-83), gây tăng đường huyết nhanh. Gạo lứt có GI thấp hơn (50-66) nhờ chứa nhiều xơ làm chậm hấp thu glucose. Người tiểu đường typ 2 nên ưu tiên gạo lứt."
        ]
    },
]

# ──────────────────────────────────────────────
# UTILITY FUNCTIONS
# ──────────────────────────────────────────────
def register_user(user):
    r = requests.post(f"{BASE_URL}/auth/register", json=user)
    return r.json()

def login_user(user):
    r = requests.post(f"{BASE_URL}/auth/login", json=user)
    d = r.json()
    if d.get("success"):
        return d["data"]["access_token"]
    return None

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def extract_user_id(token):
    # JWT decoding payload base64 snippet without any 3rd party lib
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        return payload.get("user_id")
    except:
        return None

def create_question(token, body, tags):
    r = requests.post(
        f"{BASE_URL}/qa/questions",
        json={"body": body, "tags": tags},
        headers=auth_headers(token)
    )
    return r.json()

def create_answer(token, question_id, body):
    r = requests.post(
        f"{BASE_URL}/qa/questions/{question_id}/answers",
        data={"body": body},
        headers=auth_headers(token)
    )
    return r.json()

def like_user(token, user_id):
    r = requests.patch(f"{BASE_URL}/users/{user_id}/like", headers=auth_headers(token))
    return r.json()


# ──────────────────────────────────────────────
# MAIN SEED LOGIC
# ──────────────────────────────────────────────
def main():
    print("═" * 55)
    print("🌱  SEED SCRIPT - Tạo dữ liệu test (Q&A Only)")
    print("═" * 55)

    # Step 1: Register & Login
    tokens = {}
    user_ids = {}
    for u in USERS:
        print(f"\n👤 Đăng ký/Đăng nhập: {u['username']}")
        reg = register_user(u)
        if not reg.get("success"):
            print(f"   ⚠️  Đã tồn tại hoặc lỗi: {reg.get('message')}")

        token = login_user(u)
        if not token:
            print(f"   ❌ Đăng nhập thất bại cho {u['username']}")
            continue

        uid = extract_user_id(token)
        tokens[u["username"]] = token
        user_ids[u["username"]] = uid
        print(f"   ✅ Đăng nhập thành công (ID: {uid})")

    if not tokens:
        print("\n❌ Không có token nào. Dừng script.")
        return

    token_list = list(tokens.values())
    user_id_list = list(user_ids.values())

    # Step 2: Create Q&As and answers
    print("\n" + "═" * 55)
    print("❓ TẠO Q&A & TRẢ LỜI")
    print("═" * 55)

    question_ids = []
    for i, qa in enumerate(QA_DATA):
        author_token = token_list[i % len(token_list)]
        print(f"\n📝 Q: {qa['body'][:60]}...")
        q_res = create_question(author_token, qa["body"], qa["tags"])
        q_id = q_res.get("data", {}).get("id")
        if not q_id:
            print(f"   ❌ Lỗi tạo câu hỏi: {q_res}")
            continue
        question_ids.append(q_id)
        print(f"   ✅ Tạo thành công (ID: {q_id})")

        # Create answers from different users
        for j, answer_body in enumerate(qa["answers"]):
            answerer_idx = (i + j + 1) % len(token_list)
            ans_res = create_answer(token_list[answerer_idx], q_id, answer_body)
            if ans_res.get("success"):
                print(f"   💬 Câu trả lời bởi user_{answerer_idx + 1}: OK")
            else:
                print(f"   ⚠️  Lỗi trả lời: {ans_res}")


    # Step 3: Like each other's profiles
    print("\n" + "═" * 55)
    print("❤️  TƯƠNG TÁC LIKE PROFILE")
    print("═" * 55)
    for i, (uname, uid) in enumerate(user_ids.items()):
        for j, liker_token in enumerate(token_list):
            if j != i:
                like_user(liker_token, uid)
        print(f"   ❤️  Profile @{uname} nhận {len(token_list)-1} likes")


    # Summary
    print("\n" + "═" * 55)
    print("✅ SEED HOÀN THÀNH!")
    print("═" * 55)
    print(f"👥 Tài khoản: {len(tokens)}")
    print(f"❓ Câu hỏi Q&A: {len(question_ids)}")
    print()
    print("💡 Giờ bạn có thể tự tạo bài Post và test Chatbot!")
    print("═" * 55)


if __name__ == "__main__":
    main()
