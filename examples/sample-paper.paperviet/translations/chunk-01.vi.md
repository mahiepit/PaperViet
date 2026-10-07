<!-- paperviet chunk-01 | bản dịch tiếng Việt -->

<!-- b1 | title | p1 -->
Sparse Curriculum Sampling: lấy mẫu theo giáo trình thưa để tinh chỉnh hiệu quả các mô hình ngôn ngữ nhỏ

<!-- b2 | authors | keep | p1 -->

<!-- b3 | heading 1 | p1 -->
Tóm tắt

<!-- b4 | abstract | p1 -->
Tinh chỉnh (fine-tuning) một mô hình ngôn ngữ (language model) đã tiền huấn luyện cho một tác vụ mới thường đòi hỏi duyệt qua tập huấn luyện (training set) nhiều lượt, dù phần lớn mẫu đã được mô hình xử lý tốt ngay sau epoch đầu tiên. Chúng tôi đề xuất Sparse Curriculum Sampling (SCS), một phương pháp chọn lọc dữ liệu (data selection) đơn giản: ước lượng độ khó của từng mẫu dựa trên giá trị mất mát gần nhất của mẫu đó, rồi lấy mẫu khó thường xuyên hơn nhưng vẫn quay lại các mẫu dễ. SCS không thêm tham số huấn luyện nào và có thể cài đặt chỉ bằng vài dòng mã. Trên ba bộ đánh giá phân loại văn bản (text classification), SCS đạt độ chính xác (accuracy) ngang với tinh chỉnh thông thường nhưng dùng ít hơn 38% số lượt cập nhật gradient, đồng thời giảm phương sai (variance) giữa các seed ngẫu nhiên (random seed). Chúng tôi cũng thảo luận khi nào phương pháp thất bại và vì sao lợi ích của nó có thể không chuyển sang các tác vụ sinh văn bản.

<!-- b5 | heading 1 | p1 -->
1 Giới thiệu

<!-- b6 | paragraph | p1 -->
Các mô hình ngôn ngữ nhỏ, với dưới một tỷ tham số, vẫn hấp dẫn đối với các phòng thí nghiệm và doanh nghiệp có ngân sách tính toán hạn chế. Tuy nhiên, tinh chỉnh một mô hình như vậy vẫn buộc phải đánh đổi (trade-off) giữa chi phí và độ chính xác: huấn luyện thêm nhiều epoch thường cải thiện điểm số cuối cùng, nhưng phần lớn lượng tính toán tăng thêm lại dồn vào những mẫu mà mô hình đã học được.

<!-- b7 | paragraph | p1 -->
Học theo giáo trình (curriculum learning) [2] giải quyết một vấn đề gần với vấn đề này bằng cách đưa các mẫu vào huấn luyện theo một trình tự có ý nghĩa, thường là từ dễ đến khó. Trên thực tế, một giáo trình cố định cần có thước đo độ khó xác định từ trước khi huấn luyện, điều mà các tập dữ liệu (dataset) mới thường không có. Trong bài báo này, chúng tôi tiếp cận theo hướng khác: thay vì sắp xếp dữ liệu một lần, chúng tôi để chính tín hiệu huấn luyện của mô hình quyết định mỗi mẫu cần được xem bao nhiêu lần.

<!-- b8 | paragraph | p1 -->
Bài báo có ba đóng góp. Thứ nhất, chúng tôi giới thiệu SCS, một quy tắc lấy mẫu dựa trên trung bình trượt hàm mũ (exponential moving average) của giá trị mất mát trên từng mẫu. Thứ hai, chúng tôi chỉ ra bằng thực nghiệm rằng SCS giảm số lượt cập nhật gradient mà không làm giảm độ chính xác. Thứ ba, chúng tôi phân tích các trường hợp phương pháp thất bại; theo hiểu biết của chúng tôi, những trường hợp này chưa từng được báo cáo với các cách tiếp cận tương tự.
