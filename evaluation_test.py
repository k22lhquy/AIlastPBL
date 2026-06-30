# d:\Project\backendAIPBL\evaluation_test.py
import time
import sys
import codecs
import random
import numpy as np

# Ép kiểu sys.stdout hỗ trợ UTF-8 trên Windows Console
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
sys.path.append('.')

from libs.ai.embedding import get_embedding_model
from langchain_core.documents import Document

# 1. BỘ DỮ LIỆU ĐẶC TRƯNG CỦA 20 CHỦ ĐỀ
TOPIC_DATABASE = {
    "Công nghệ RAG": {
        "facts": [
            "Hệ thống RAG kết hợp công cụ tìm kiếm tri thức ngoài với LLMs để tăng độ chính xác.",
            "Lợi ích lớn nhất của RAG là giảm thiểu hiện tượng ảo giác (hallucination) nhờ ngữ cảnh tin cậy.",
            "Hệ cơ sở dữ liệu vector và vector search giúp tìm kiếm ngữ nghĩa siêu tốc với hàng triệu tài liệu.",
            "RAG tiết kiệm kinh phí vận hành so với việc tiếp tục fine-tuning lại mô hình nền lớn.",
            "Độ chính xác của RAG phụ thuộc trực tiếp vào kích thước phân đoạn văn bản (chunk size).",
            "Việc kết hợp Hybrid Search giúp RAG đạt chỉ số xếp hạng thông tin cao nhất."
        ],
        "base_queries": [
            "RAG giúp giảm ảo giác hallucination như thế nào",
            "Tại sao kiến trúc RAG giúp giảm chi phí fine-tuning",
            "Vai trò của vector database trong tìm kiếm ngữ nghĩa cho RAG",
            "Các dòng hiệu năng ảnh hưởng đến độ chính xác chunking trong RAG",
            "Thuật toán Hybrid search giúp ích gì cho retrieval của chatbot"
        ]
    },
    "Phở Bò Việt Nam": {
        "facts": [
            "Nước dùng phở bò truyền thống phải ninh xương ống bò kèm với hành tây và gừng nướng thơm.",
            "Các nguyên liệu thảo mộc quan trọng nhất của nước dùng phở bao gồm hoa hồi, thảo quả, quế và đinh hương.",
            "Món phở luôn được thưởng thức kèm với bánh phở mềm, hành lá thái nhỏ, thịt bò tái hoặc chín ngon.",
            "Giá đỗ, húng quế, ngò gai và chanh ớt là những món kèm không thể thiếu của bát phở tròn vị.",
            "Kỹ thuật thái thịt bò mỏng và chần nhanh trong nước sôi giúp thịt giữ nguyên mùi vị và dinh dưỡng.",
            "Phở xưa được bán trên các gánh hàng rong xuyên suốt phố phường Hà Nội cổ xưa."
        ],
        "base_queries": [
            "Cách nấu nước dùng phở bò truyền thống thơm ngon đúng vị",
            "Những nguyên liệu thảo mộc nào cần thiết cho nước dùng phở",
            "Rau sống và các món gia vị ăn kèm bát phở bò gồm những gì",
            "Kỹ thuật thái và chần thịt bò tái cho phở ngon",
            "Lịch sử các gánh hàng rong bán phở xưa ở Hà Nội"
        ]
    },
    "Thời tiết Hà Nội": {
        "facts": [
            "Khí hậu Hà Nội thuộc vào vùng nhiệt đới gió mùa có bốn mùa Xuân, Hạ, Thu, Đông đặc trưng.",
            "Mùa hè Hà Nội nóng bức cao độ với mưa giông vào chiều tối, nhiệt độ từ 32 đến 38 độ C.",
            "Mùa đông ở Hà Nội trở lạnh hanh khô, chịu ảnh hưởng bởi gió mùa đông bắc.",
            "Tình trạng ô nhiễm không khí và bụi mịn PM2.5 vào mùa đông ở Hà Nội đạt mức báo động hại.",
            "Chỉ số AQI đo lường chất lượng không khí thường xuyên ở mức kêu gọi người dân dùng khẩu trang.",
            "Khí hậu mùa thu Hà Nội rất mát mẻ, thời tiết dễ chịu rất thu hút du khách tham quan."
        ],
        "base_queries": [
            "Đặc điểm thời tiết bốn mùa xuân hạ thu đông ở Hà Nội",
            "Diễn biến nhiệt độ và mưa giông mùa hè Hà Nội",
            "Áp thấp nhiệt đới và gió mùa đông bắc vào mùa đông Hà Nội",
            "Chỉ số bụi mịn PM2.5 báo động đỏ ô nhiễm không khí AQI",
            "Thời tiết mùa thu Hà Nội thích hợp cho hoạt động du lịch nào"
        ]
    },
    "Dataset Zalo": {
        "facts": [
            "Dataset Zalo E-commerce được thiết kế với 8,487 cặp hỏi đáp để đánh giá thuật toán chatbot.",
            "Bộ dữ liệu Zalo hỗ trợ độc quyền các bài toán xử lý ngôn ngữ tự nhiên (NLP) tiếng Việt.",
            "Chia tập Zalo dataset theo chuẩn 80% train, 10% validation và 10% test để đánh giá.",
            "Các thuật toán embedding và deep learning thường xuyên cạnh tranh điểm leaderboard.",
            "Dữ liệu Zalo rất giá trị cho việc đào tạo trợ lý ảo thương mại điện tử tự động hóa.",
            "Các cuộc thi Zalo AI Challenge thúc đẩy tính sáng tạo và ứng dụng chatbot vào kinh doanh."
        ],
        "base_queries": [
            "Có bao nhiêu cặp câu hỏi đáp trong dataset Zalo E-commerce",
            "Bộ dữ liệu Zalo hỗ trợ nào cho nghiên cứu NLP tiếng Việt",
            "Cách thức phân chia tỷ lệ tập dữ liệu train val test của Zalo",
            "Mô hình deep learning và embedding đạt leaderboard challenge cao",
            "Ứng dụng gặp của Zalo challenge đối với trợ lý e-commerce"
        ]
    },
    "Lịch sử Điện Biên Phủ": {
        "facts": [
            "Chiến dịch Điện Biên Phủ năm 1954 kết thúc bằng sự đầu hàng của quân đội Pháp tại Mường Thanh.",
            "Đại tướng Võ Nguyên Giáp chỉ đạo quyết định thay đổi phương châm từ đánh nhanh thắng nhanh sang đánh chắc tiến chắc.",
            "Lực lượng pháo binh và dân công xe đạp thồ góp công rất lớn cho chiến thắng vẻ vang của Việt Minh.",
            "Hiệp định Geneve được ký kết ngay sau đó để chia đôi đất nước ở vĩ tuyến 17 vì hòa bình.",
            "Chiến thắng chấn động địa cầu đã mở ra trang mới cho phong trào giải phóng dân tộc trên thế giới.",
            "Cuộc chiến đấu anh dũng ở các đồi A1, C1 và cứ điểm Him Lam thật sự là chiến tích anh hùng."
        ],
        "base_queries": [
            "Chiến dịch Điện Biên Phủ kết thúc như thế nào năm 1954",
            "Quyết định đánh chắc tiến chắc của Đại tướng Võ Nguyên Giáp",
            "Vai trò của đội pháo binh và xe đạp thồ thời lượng",
            "Ý nghĩa của hiệp định Geneve đối với vĩ tuyến 17",
            "Ý nghĩa toàn cầu của chiến thắng Điện Biên Phủ lịch sử"
        ]
    },
    "Du lịch Đà Nẵng": {
        "facts": [
            "Đà Nẵng nổi tiếng là thành phố đáng sống với bờ biển Mỹ Khê đẹp nằm trong top thế giới.",
            "Bà Nà Hills có cây Cầu Vàng đạt kỷ lục và hệ thống cáp treo đi qua mây đẹp thơ mộng.",
            "Cầu Rồng phun lửa và phun nước vào mỗi dịp cuối tuần rất thu hút du khách tập trung xem.",
            "Bán đảo Sơn Trà là nơi có chùa Linh Ứng và pho tượng Phật Bà cao nhất Việt Nam hướng biển.",
            "Du lịch Đà Nẵng còn hấp dẫn bởi các món ăn đặc sản như mì quảng, bánh tráng cuốn thịt heo.",
            "Lễ hội pháo hoa quốc tế Đà Nẵng được tổ chức hằng năm mang lại sự bùng nổ ánh sáng."
        ],
        "base_queries": [
            "Thành phố đáng sống Đà Nẵng có gì thu hút du khách",
            "Du lịch Bà Nà Hills ngắm Cầu Vàng và đi cáp treo ngủ",
            "Lịch trình xem Cầu Rồng phun lửa phun nước cuối tuần",
            "Khám phá bán đảo Sơn Trà, danh lam chùa Linh Ứng",
            "Món ăn ngon mì quảng đặc sản làm nên ẩm thực Đà Nẵng"
        ]
    },
    "Điện toán lượng tử": {
        "facts": [
            "Điện toán lượng tử hoạt động dựa trên qubit cho phép tồn tại ở trạng thái chồng chất đồng thời.",
            "Nguyên lý Heisenberg và hiệu ứng rối lượng tử cho phép kết nối liên thông giữa các qubit.",
            "Máy tính lượng tử có tốc độ tính toán vượt trội hơn siêu máy tính cổ điển trong các bài toán mật mã.",
            "Ứng dụng của lượng tử giúp giải mã cần thiết về hệ thống bảo mật và mô hình hóa hóa học.",
            "Việc duy trì trạng thái lượng tử (coherence) đòi hỏi điều kiện nhiệt độ cực lạnh gần độ zero tuyệt đối.",
            "Các hãng công nghệ lớn đang nghiên cứu chip lượng tử để tiến tới tối ưu hóa người dùng thương mại."
        ],
        "base_queries": [
            "Nguyên lý hoạt động qubit chồng chất trong điện toán lượng tử",
            "Hiệu ứng rối lượng tử Heisenberg giúp liên kết qubit ra sao",
            "Máy tính lượng tử giúp giải quyết bài toán mật mã tốc độ thế nào",
            "Điều kiện nhiệt độ âm tuyệt đối để bảo trì chip lượng tử",
            "Xu hướng phát triển chip lượng tử thương mại của hãng công nghệ"
        ]
    },
    "Sức khỏe giấc ngủ": {
        "facts": [
            "Giấc ngủ ngon vào ban đêm hỗ trợ phục hồi hệ miễn dịch và củng cố trí nhớ lâu dài.",
            "Sóng não delta phát triển mạnh nhất trong giai đoạn giấc ngủ sâu giúp khôi phục cơ thể.",
            "Melatonin là hormone tự nhiên được não bộ tiết ra vào buổi tối để gây buồn ngủ.",
            "Rối loạn mất ngủ kéo dài có thể dẫn đến tăng stress, trầm cảm và suy giảm trí tuệ.",
            "Chu kỳ giấc ngủ REM là thời điểm những giấc mơ sống động xảy ra và giúp khôi phục cảm xúc.",
            "Thiết lập thói quen ngủ đúng giờ và tránh xa ánh sáng xanh hỗ trợ nâng cao sức khỏe."
        ],
        "base_queries": [
            "Lợi ích của giấc ngủ ngon đối với trí nhớ và hệ miễn dịch",
            "Vai trò của sóng não delta trong giai đoạn giấc ngủ sâu",
            "Hormone melatonin tự nhiên giúp điều hòa giấc ngủ thế nào",
            "Tác hại của rối loạn mất ngủ kéo dài đối với sức khỏe tinh thần",
            "Chu kỳ giấc ngủ REM ảnh hưởng thế nào đến sức khỏe tinh thần"
        ]
    },
    "Kinh tế vĩ mô": {
        "facts": [
            "Kinh tế vĩ mô nghiên cứu các chỉ số tổng quát như GDP, tỷ lệ lạm phát và tỷ lệ thất nghiệp.",
            "Lạm phát lõi loại bỏ giá lương thực và năng lượng biến động để theo dõi xu hướng giá cơ bản.",
            "Cung tiền M2 và chính sách lãi suất điều hành của ngân hàng trung ương ảnh hưởng đến lạm phát.",
            "Chính sách tiền tệ thắt chặt thường được áp dụng để kiềm chế sự nóng lên của nền kinh tế.",
            "Cán cân thương mại phản ánh sự chênh lệch giữa giá trị xuất khẩu và nhập khẩu quốc gia.",
            "Tăng trưởng GDP bền vững yêu cầu sự nâng suất lao động và cải tiến công nghệ đổi mới."
        ],
        "base_queries": [
            "Kinh tế vĩ mô nghiên cứu các chỉ số GDP độc lập nào",
            "Lạm phát lõi khác gì lạm phát toàn phần trong kinh tế",
            "Ngân hàng trung ương điều hành cung tiền M2 và lãi suất ra sao",
            "Chính sách tiền tệ thắt chặt giúp ngăn ngừa bong bóng kinh tế",
            "Mối quan hệ giữa cán cân thương mại xuất khẩu và nhập khẩu"
        ]
    },
    "Chứng khoán": {
        "facts": [
            "Chỉ số VN-Index đại diện cho biến động giá của các cổ phiếu niêm yết trên sàn chứng khoán.",
            "Khối ngoại bán ròng và tự doanh mua vào liên tục tác động đến tâm lý nhà đầu tư cá nhân.",
            "Cổ phiếu bluechip có đặc tính vốn hóa lớn, tài chính lành mạnh và chi trả cổ tức đều đặn.",
            "Phân tích kỹ thuật sử dụng biểu đồ nến và đường MA20 để xác định xu hướng thị trường.",
            "Biên độ dao động trần sàn của sàn HOSE là 7% trong khi sàn HNX cho phép lên đến 10%.",
            "Nhà đầu tư cần quản trị rủi ro bằng cách cắt lỗ chủ động khi đạt tỷ lệ âm cho phép."
        ],
        "base_queries": [
            "Chỉ số VN-Index và biến động thị trường chứng khoán VN",
            "Ảnh hưởng của khối ngoại bán ròng đến tâm lý nhà đầu tư",
            "Đặc điểm của cổ phiếu bluechip trên sàn chứng khoán",
            "Cách sử dụng đường MA20 để phân tích kỹ thuật chứng khoán",
            "Biên độ dao động trần sàn margin trên HOSE và HNX"
        ]
    },
    "Bất động sản": {
        "facts": [
            "Tính thanh khoản của bất động sản phản ánh khả năng chuyển đổi thành tiền mặt nhanh chóng.",
            "Sổ đỏ sổ hồng chính chủ là cơ sở pháp lý cao nhất giúp tránh tranh chấp tài sản.",
            "Dự án căn hộ và đất nền ở các đô thị vệ tinh đang kéo dòng vốn đầu tư lớn trong năm.",
            "Quy hoạch đô thị và xây dựng cơ sở hạ tầng đóng vai trò quyết định tăng giá bất động sản.",
            "Lãi suất vay mua nhà của các ngân hàng nếu ở mức thấp sẽ kích thích thị trường phục hồi.",
            "Đầu cơ và tạo sốt đất ảo có thể làm méo mó đặc tính phát triển lành mạnh của bất động sản."
        ],
        "base_queries": [
            "Tính thanh khoản ảnh hưởng thế nào đến mua bán bất động sản",
            "Pháp lý sổ đỏ sổ hồng cần đạt trước khi giao dịch nhà đất",
            "Xu hướng mua đất nền hoặc căn hộ đô thị vệ tinh hiện nay",
            "Quy hoạch cơ sở hạ tầng giúp tăng giá bất động sản ra sao",
            "Lãi suất vay mua nhà của ngân hàng ảnh hưởng như thế nào"
        ]
    },
    "Trí tuệ nhân tạo": {
        "facts": [
            "Mạng nơ-ron nhân tạo mô phỏng cách hoạt động của các tế bào não để xử lý thông tin.",
            "Học sâu (deep learning) sử dụng nhiều lớp nơ-ron để trích xuất đại đặc trưng từ dữ liệu lớn.",
            "Thị giác máy tính giúp robot tự hành hoặc camera nhận diện khuôn mặt và vật thể thị giác.",
            "Mô hình ngôn ngữ lớn GPT và Claude tự phát triển câu trả lời tự nhiên dựa trên thống kê.",
            "Thuật toán phân loại giúp phân biệt thư rác, chống độc hại và nhận diện hành vi khách hàng.",
            "Trí tuệ nhân tạo tổng hợp (AGI) là mục tiêu đạt đến năng lực trí tuệ bằng con người."
        ],
        "base_queries": [
            "Mạng nơ-ron nhân tạo hoạt động mô phỏng theo não bộ thế nào",
            "Ứng dụng học sâu deep learning xử lý tập dữ liệu hình ảnh lớn",
            "Thuật toán thị giác máy tính hoạt động trên xe tự hành ra sao",
            "Mô hình ngôn ngữ lớn LLM tự tạo văn bản tự nhiên tiếng Việt",
            "Định nghĩa về trí tuệ nhân tạo tổng hợp AGI tương lai"
        ]
    },
    "Năng lượng tái tạo": {
        "facts": [
            "Nhà máy điện mặt trời và điện gió tránh phát thải khí nhà kính gây ô nhiễm.",
            "Tuabin gió quy mô lớn chuyển đổi động năng của gió thành điện năng đưa vào lưới quốc gia.",
            "Giảm phát thải carbon đạt Net-Zero vào năm 2050 là cam kết chung của quốc tế về nhiệt độ.",
            "Pin lưu trữ điện có năng lực tích trữ điện mặt trời để tiếp tục phát vào ban đêm không nắng.",
            "Hiệu ứng nha kính làm trái đất nóng lên gây ra biến đổi khí hậu trên toàn cầu.",
            "Năng lượng thủy triều và sinh học cũng là hướng đi bền vững thay thế nhiệt điện."
        ],
        "base_queries": [
            "Điện mặt trời và điện gió giúp giảm phát thải khí nhà kính",
            "Hoạt động của tuabin gió giúp tạo điện sống xanh lưới quốc gia",
            "Cam kết Net-Zero năm 2050 giảm phát thải carbon trên thế giới",
            "Hệ thống pin lưu trữ điện năng lượng mặt trời ban đêm",
            "Hiệu ứng nhà kính ảnh hưởng gây biến đổi khí hậu ra sao"
        ]
    },
    "Vũ trụ học": {
        "facts": [
            "Hố đen siêu khối nằm ở trung tâm các thiên hà có lực hấp dẫn lớn không ánh sáng nào thoát được.",
            "Vụ nổ lớn Big Bang cách đây 13.8 tỷ nam đã khai sinh ra không gian thời gian và vật chất.",
            "Bức xạ nền vũ trụ là tàn dư năng lượng từ thuở vũ trụ sơ khai còn sống đến nay.",
            "Thiên hà Andromeda là thiên hà láng giềng đang trên đà va chạm với Ngân Hà của chúng ta.",
            "Tốc độ ánh sáng đạt xấp xỉ 300,000 km/s là giới hạn tốc độ di chuyển trong vũ trụ.",
            "Hành tinh ngoại hệ mặt trời như Kepler đang được săn tìm để tìm kiếm sự sống ngoài trái đất."
        ],
        "base_queries": [
            "Hố đen siêu khối hút ánh sáng bên trong như thế nào",
            "Thuyết vụ nổ lớn Big Bang khởi nguồn khai sinh vũ trụ",
            "Phát hiện bức xạ nền vũ trụ để chứng minh lịch sử vụ nổ",
            "Va chạm thiên hà Andromeda và mặt trời ngân hà chúng ta",
            "Tốc độ ánh sáng và hành trình săn tìm hành tinh Kepler"
        ]
    },
    "Thể thao Olympic": {
        "facts": [
            "Huy chương vàng là phần thưởng vinh quang cao nhất dành cho các vận động viên hàng đầu.",
            "Kỷ lục thế giới mới luôn đòi hỏi chế độ luyện tập và dinh dưỡng y học nghiêm ngặt.",
            "Món thể dục dụng cụ yêu cầu kỹ thuật thăng bằng, sức mạnh cơ bắp và tính ưu việt biểu diễn.",
            "Thể lực bền bỉ góp phần quyết định vào chiến thắng các môn chạy marathon cự ly dài.",
            "Tinh thần thể thao cao đẹp thể hiện qua sự tôn trọng đối thủ và công bằng trung thực.",
            "Thế vận hội mùa hè quy tụ hàng chục nghìn vận động viên tranh tài tại các thành phố."
        ],
        "base_queries": [
            "Giá trị của tấm huy chương vàng Olympic danh giá",
            "Chế độ dinh dưỡng và tập luyện đạt kỷ lục thế giới",
            "Kỹ thuật biểu diễn môn thể dục dụng cụ ở Olympic",
            "Bí quyết luyện thể lực marathon cự ly dài chạy dài",
            "Tinh thần thể thao cao thượng tôn trọng đối thủ trận đấu"
        ]
    },
    "Âm nhạc cổ điển": {
        "facts": [
            "Bản giao hưởng hoành tráng đòi hỏi sự phối hợp chặt chẽ của cả dàn nhạc giao hưởng.",
            "Thiên tài Mozart đã sáng tác nhiều bản nhạc huyền thoại từ khi còn rất nhỏ tuổi.",
            "Nhịp điệu sonata tạo nên cấu trúc nhạc kịch tính với ba phần riêng biệt.",
            "Đàn piano cổ điển có khả năng bao phủ dày dặn âm huyền ảo mà không cần nhạc cụ phụ trợ.",
            "Hợp âm phức tạp và các nốt nhạc vang lên tạo cảm giác thư thái kích thích trí não.",
            "Beethoven tuy bị điếc tai nhưng vẫn viết nên bản giao hưởng số 9 bất hủ của nhân loại."
        ],
        "base_queries": [
            "Sự điều phối trong dàn nhạc giao hưởng cho bản giao hưởng",
            "Sáng tác thời thơ ấu của thiên tài tí hon Mozart",
            "Cấu trúc ba phần của nhịp điệu sonata trong âm nhạc",
            "Ưu điểm của âm hưởng piano cổ điển độc lập",
            "Nghị lực Beethoven khi điếc vẫn viết giao hương số 9"
        ]
    },
    "Hội họa Phục Hưng": {
        "facts": [
            "Họa sĩ Leonardo da Vinci gieo vào hội họa Phục Hưng kỹ thuật sfumato làm mờ ranh giới đầy bất ngờ.",
            "Bức tranh Mona Lisa luôn cuốn hút với nụ cười bí ẩn và cấu trúc tỉ lệ vàng hình học.",
            "Nghệ thuật thời kỳ Phục Hưng tập trung vào kiến trúc người và thiên nhiên sống động chân thực.",
            "Hội họa phương Tây đã chuyển biến mạnh mẽ từ phong cách tôn giáo sang chủ nghĩa nhân văn.",
            "Điêu khắc gia Michelangelo tạo nên kiệt tác tượng David bằng đá cẩm thạch đẹp tuyệt trần.",
            "Các phòng triển lãm lớn trên thế giới tranh nhau trưng bày bảo vệ bản gốc lúc xưa."
        ],
        "base_queries": [
            "Kỹ thuật sfumato của Leonardo da Vinci trong tranh cổ",
            "Nụ cười bí ẩn và tỉ lệ vàng của bức họa Mona Lisa",
            "Chủ nghĩa nhân văn và con người thiên nhiên trong hội họa Phục Hưng",
            "Tượng Michelangelo điêu khắc tượng David đá cẩm thạch",
            "Bảo tồn tranh gốc Phục Hưng tại các phòng triển lãm nghệ thuật"
        ]
    },
    "Toán học rời rạc": {
        "facts": [
            "Lý thuyết đồ thị nghiên cứu cấu trúc gồm các đỉnh và cạnh liên kết giữa chúng.",
            "Tổ hợp và xác suất giúp giải quyết các bài toán đếm và dự đoán tỷ lệ may rủi logic.",
            "Thuật toán Dijkstra tìm đường đi ngắn nhất phù hợp cho định vị bản đồ vệ tinh.",
            "Mã hóa RSA sử dụng cặp khóa công khai và khóa bí mật luôn dựa trên toán học modulo lớn.",
            "Ma trận kề biểu diễn quan hệ kết nối của đồ thị làm đầu vào cho máy tính.",
            "Toán học rời rạc là nền tảng cốt lõi để phát triển khoa học máy tính và lập trình."
        ],
        "base_queries": [
            "Ứng dụng của lý thuyết đồ thị đỉnh và cạnh trong lập trình",
            "Cách tính toán tổ hợp xác suất để có thí điểm",
            "Thuật toán Dijkstra tìm đường đi ngắn nhất bản đồ",
            "Nguyên lý mã hóa bảo mật RSA khóa công khai toán học",
            "Tại sao toán rời rạc là nền tảng học coding"
        ]
    },
    "Sinh học phân tử": {
        "facts": [
            "Chuỗi ADN là bản thiết kế di truyền quy định mọi đặc điểm protein của tế bào sinh vật.",
            "Đột biến gen xảy ra tự nhiên hoặc do hóa chất gây ra làm biến đổi chuỗi nucleotide.",
            "Tế bào gốc có khả năng đặc biệt phân chia và biến đổi thành mọi loại tế bào chuyên biệt.",
            "Quá trình phiên mã và dịch mã giúp thông tin từ gen chuyển hóa thành enzyme thiết thực.",
            "Cải tạo di truyền bằng công nghệ CRISPR cho phép chỉnh sửa danh sách ADN cốt lõi sinh động.",
            "Nghien cứu sinh học phân tử mở ra kỷ nguyên y học tái tạo điều trị ung thư tận gốc."
        ],
        "base_queries": [
            "Cấu trúc và chức năng chuỗi ADN chứa mã di truyền",
            "Nguyên nhân và hậu quả của đột biến gen sinh học",
            "Ứng dụng y học của tế bào gốc trong điều trị bệnh nan y",
            "Quá trình phiên mã và dịch mã tạo enzyme cho tế bào",
            "Công nghệ CRISPR can thiệp và chỉnh sửa ADN chính xác"
        ]
    },
    "Triết học phương Đông": {
        "facts": [
            "Triết học Lão Tử trong Đạo Đức Kinh nhắc đến đạo vô vi sống hợp thuận tự nhiên.",
            "Thuyết âm dương lý giải sự vận động của vạn vật qua sự tương tác và chuyển hóa khác nhau.",
            "Ngũ hành tương sinh tương khắc gồm Kim, Mộc, Thủy, Hỏa, Thổ hình thành nên vật chất.",
            "Nho giáo Khổng Tử đặt nặng luân lý tam cương ngũ thường và đạo làm người.",
            "Thiền tông Phật giáo hướng tâm con người trở về sự tĩnh lặng tỉnh thức ngay hiện tại.",
            "Triết học phương Đông đi tìm sự hài hòa giữa con người tự nhiên hơn là chinh phục thiên nhiên."
        ],
        "base_queries": [
            "Tư tưởng vô vi thuận tự nhiên trong triết học Lão Tử",
            "Thuyết âm dương tương sinh tương khắc về chuyển hóa thế giới",
            "Mối quan hệ tương sinh tương khắc của ngũ hành quan",
            "Đạo làm người và tư tưởng Nho giáo của Đức Khổng Tử",
            "Sự tương đồng thiền tông phật giáo và sự tĩnh tâm"
        ]
    }
}

# 1.2 HÀM SINH DỮ LIỆU ĐA DẠNG NGỮ NGHĨA
def generate_massive_corpus(num_topics=20, chunks_per_topic=50, questions_per_topic=20):
    corpus, queries = [], []
    topic_list = list(TOPIC_DATABASE.keys())[:num_topics]

    # Các câu đệm đa dạng để tránh các mảnh văn bản (Chunks) có chung cấu trúc
    intro_scenarios = [
        "Dưới đây là báo cáo xác thực:",
        "Trong nghiên cứu gần nhất,",
        "Tài liệu thu thập cho thấy,",
        "Theo nhận định từ chuyên gia,",
        "Hệ thống ghi nhận rằng,",
        "Đặc điểm thực tế là",
        "Một số nguồn tin tuyên bố",
        "Khảo sát thực tế cho thấy",
        "Nhìn chung,",
        "Ngoài ra,"
    ]
    
    extra_sentences = [
        "Dữ liệu này được nghiên cứu độc lập và công bố rộng rãi.",
        "Quy trình đo lường cần thiết cần được thực hiện cẩn thận.",
        "Người ta thường kết hợp các kỹ thuật cổ điển và hiện đại.",
        "Các kết luận nêu trên đã được kiểm thủy chặt chẽ.",
        "Kết quả kiểm nghiệm năm 2024 cung cấp bằng chứng rất rõ nét.",
        "Hệ thống ghi nhận phân phối hiệu suất ổn định.",
        "Đây là trường hợp đặc biệt cần được lưu tâm.",
        "Có thể áp dụng trong cả nghiên cứu lẫn thực tiễn."
    ]

    question_annexes = [
        "làm sao để hiểu rõ?",
        "cho biết thông tin chi tiết.",
        "hãy phân tích rõ.",
        "nêu ví dụ chứng minh.",
        "có đúng không?",
        "tại sao lại như vậy?",
        "hãy tóm tắt ý chính."
    ]

    for t_id, topic_name in enumerate(topic_list):
        topic_info = TOPIC_DATABASE[topic_name]
        facts = topic_info["facts"]
        base_queries = topic_info["base_queries"]

        # --- Sinh Chunks tự nhiên ---
        for c_id in range(chunks_per_topic):
            # Chọn ngẫu nhiên 2 facts khác nhau của chủ đề này
            selected_facts = random.sample(facts, 2)
            
            # Kết hợp ngẫu nhiên các câu đệm
            content = f"{random.choice(intro_scenarios)} {selected_facts[0]} {random.choice(extra_sentences)} Tiếp đó, {selected_facts[1]}"
            content = content[0].upper() + content[1:]

            corpus.append(Document(
                page_content=f"[{topic_name}-Chunk-{c_id+1}] {content}",
                metadata={
                    "topic_id": t_id,
                    "topic_name": topic_name
                }
            ))

        # --- Sinh Câu hỏi tự nhiên ---
        # Đảm bảo mỗi câu hỏi có tới 50 đáp án tương đương trong corpus (mỗi topic có 50 chunks đáp án liên quan)
        for q_id in range(questions_per_topic):
            base_q = random.choice(base_queries)
            
            style = random.randint(1, 4)
            if style == 1:
                question_text = f"Cho tôi hỏi: {base_q}?"
            elif style == 2:
                question_text = f"{base_q}, {random.choice(question_annexes)}"
            elif style == 3:
                question_text = f"Dựa vào tài liệu, hãy cho biết {base_q[0].lower() + base_q[1:]}?"
            else:
                question_text = f"Hãy viết báo cáo tóm tắt: {base_q}."

            queries.append({
                "query": question_text,
                "target_topic": t_id,
                "target_topic_name": topic_name,
                "question_id": q_id
            })

    return corpus, queries

# ĐẢM BẢO CONFIG ĐÚNG YÊU CẦU: 20 Topics, 50 Chunks/Topic, 20 Questions/Topic
NUM_TOPICS = 20
CHUNKS_PER_TOPIC = 50
QUESTIONS_PER_TOPIC = 20

corpus_documents, eval_queries = generate_massive_corpus(NUM_TOPICS, CHUNKS_PER_TOPIC, QUESTIONS_PER_TOPIC)

# ===== [BÁO CÁO 1] THÔNG TIN TỔNG QUAN DATASET =====
print(f"\n{'='*80}\n📦 THÔNG TIN DATASET (SCALED UP - NATURAL Q&A)\n{'='*80}")
print(f"- Số topic               : {NUM_TOPICS}")
print(f"- Số chunk / topic        : {CHUNKS_PER_TOPIC} (Mỗi câu hỏi có {CHUNKS_PER_TOPIC} chunks đúng tương ứng)")
print(f"- Số câu hỏi / topic      : {QUESTIONS_PER_TOPIC}")
print(f"- Tổng số document        : {len(corpus_documents)}")
print(f"- Tổng số câu query       : {len(eval_queries)}")

print(f"\n--- Mẫu 3 document đầu tiên trong corpus ---")
for doc in corpus_documents[:3]:
    print(f"  [topic_id={doc.metadata['topic_id']:2d}] {doc.page_content}")

print(f"\n--- Danh sách 20 Topic kiểm thử ---")
for t_id, topic_name in enumerate(TOPIC_DATABASE.keys()):
    print(f"  Topic [{t_id:02d}]: {topic_name}")

# Tải mô hình Embedding E5
embedding_model = get_embedding_model()

# ===== [BÁO CÁO 2] EMBEDDING CORPUS (CÓ CHIA BATCH ĐỂ HIỂN THỊ TIẾN ĐỘ) =====
print(f"\n{'='*80}\n🧩 TIẾN HÀNH VECTOR HÓA {len(corpus_documents)} DOCUMENTS (CHIA BATCH ON STAGE)\n{'='*80}")
start_embed = time.time()
embedded_docs = []
batch_size = 100

for i in range(0, len(corpus_documents), batch_size):
    batch = [doc.page_content for doc in corpus_documents[i:i+batch_size]]
    print(f"   -> Embedding batch {i//batch_size + 1}/{len(corpus_documents)//batch_size} ({len(batch)} chunks)...")
    batch_embeds = embedding_model.embed_documents(batch)
    embedded_docs.extend(batch_embeds)

dur_embed = time.time() - start_embed
embed_dim = len(embedded_docs[0])
print(f"✅ Embedding hoàn thành.")
print(f"- Tổng thời gian embed: {dur_embed:.2f} giây")
print(f"- Thời gian embed TB/doc: {dur_embed / len(corpus_documents) * 1000:.2f} ms\n")

embedded_docs_np = np.array(embedded_docs)
doc_norms = np.linalg.norm(embedded_docs_np, axis=1)

K = 5

precision_at_k = []
mrr_list = []
latencies = []

per_topic_metrics = {
    t_id: {
        "p": [],
        "mrr": []
    }
    for t_id in range(NUM_TOPICS)
}

print(f"{'='*80}\n🔍 BẮT ĐẦU SO SÁNH VECTOR HÀNG LOẠT (NUMPY VECTORIZED)\n{'='*80}")

for q_idx, item in enumerate(eval_queries):
    t_start = time.perf_counter()

    # Embed query
    q_vec = np.array(embedding_model.embed_query(item["query"]))
    q_norm = np.linalg.norm(q_vec)

    # Cosine similarity
    scores = np.dot(embedded_docs_np, q_vec) / (doc_norms * q_norm)

    latency_ms = (time.perf_counter() - t_start) * 1000
    latencies.append(latency_ms)

    # Top-K
    indexed_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    top_k = indexed_scores[:K]
    top_k_indices = [i[0] for i in top_k]

    # Kiểm tra đúng topic
    hits = [
        corpus_documents[idx].metadata["topic_id"] == item["target_topic"]
        for idx in top_k_indices
    ]

    # Precision@K
    p_k = sum(hits) / K
    precision_at_k.append(p_k)

    # MRR
    first_hit = next((i for i, ok in enumerate(hits, 1) if ok), None)
    mrr_score = 1.0 / first_hit if first_hit else 0.0
    mrr_list.append(mrr_score)

    pm = per_topic_metrics[item["target_topic"]]
    pm["p"].append(p_k)
    pm["mrr"].append(mrr_score)

    if q_idx % 20 == 0:
        print(f"  [Progress {q_idx}/{len(eval_queries)}] Query: '{item['query'][:60]}...'")
        print(f"   -> Latency: {latency_ms:.2f} ms | P@{K}: {p_k*100:.1f}% | MRR: {mrr_score:.3f}")

# ===== [BÁO CÁO 4] METRICS TRUNG BÌNH THEO TỪNG TOPIC =====
print(f"\n{'='*80}\n📈 METRICS TRUNG BÌNH THEO TỪNG TOPIC (trên {QUESTIONS_PER_TOPIC} câu hỏi/topic)\n{'='*80}")
print(f"{'Topic':<26}{'P@'+str(K):>10}{'MRR':>10}{'#Q':>8}")

for t_id in range(NUM_TOPICS):
    pm = per_topic_metrics[t_id]
    topic_name = list(TOPIC_DATABASE.keys())[t_id]

    print(
        f"{topic_name:<26}"
        f"{np.mean(pm['p'])*100:9.1f}%"
        f"{np.mean(pm['mrr']):10.3f}"
        f"{len(pm['p']):8d}"
    )

# ===== [BÁO CÁO 5] TỔNG HỢP KẾT QUẢ CUỐI CÙNG =====
print(f"\n{'='*80}\n📊 BÁO CÁO ĐÁNH GIÁ RAG\n{'='*80}")
print(f"- Tổng document trong corpus : {len(corpus_documents)}")
print(f"- Tổng query đánh giá        : {len(eval_queries)}")
print(f"- Chiều vector embedding     : {embed_dim}")
print(f"- Thời gian embed TB/doc     : {dur_embed / len(corpus_documents) * 1000:.2f} ms")
print(f"- Latency truy vấn (Avg)     : {np.mean(latencies):.2f} ms")
print(f"- Latency truy vấn (Min)     : {np.min(latencies):.2f} ms")
print(f"- Latency truy vấn (Max)     : {np.max(latencies):.2f} ms")
print(f"- Precision@{K}              : {np.mean(precision_at_k)*100:.1f}%")
print(f"- MRR                        : {np.mean(mrr_list):.3f}")
print(f"{'='*80}")