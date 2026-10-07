## Bài báo nói gì (3 câu)

Tinh chỉnh mô hình ngôn ngữ nhỏ tốn nhiều lượt cập nhật cho những mẫu mà mô hình đã học xong. Tác giả đề xuất SCS: theo dõi giá trị mất mát của từng mẫu bằng trung bình trượt hàm mũ, rồi lấy mẫu khó thường xuyên hơn mà vẫn giữ xác suất nhỏ cho mẫu dễ. Trên ba tập dữ liệu phân loại văn bản, SCS giữ nguyên độ chính xác nhưng cần ít hơn 38% số lượt cập nhật.

## Đóng góp chính

- Một quy tắc lấy mẫu không thêm tham số: điểm độ khó s_i cập nhật theo phương trình (1), xác suất lấy mẫu tỉ lệ với (s_i + eps)^alpha theo phương trình (2).
- Bằng chứng thực nghiệm: cùng độ chính xác với ít lượt cập nhật hơn (32.2k so với 52.0k) và phương sai giữa các seed thấp hơn.
- Phân tích trường hợp thất bại: alpha quá lớn (alpha = 2) làm giảm độ chính xác; nhãn nhiễu có thể bị lấy mẫu lặp lại.

## Phương pháp

Mỗi mẫu có một điểm độ khó, là trung bình trượt của giá trị mất mát với hệ số beta = 0.9. Xác suất chọn một mẫu tỉ lệ với điểm độ khó lũy thừa alpha: alpha = 0 là lấy mẫu đều như thường lệ, alpha càng lớn thì càng dồn vào mẫu khó. Hằng số eps giúp mẫu dễ không bao giờ bị loại hẳn.

## Kết quả

| Cấu hình | Dữ liệu A | Dữ liệu B | Dữ liệu C | Số cập nhật (k) |
|---|---|---|---|---|
| Lấy mẫu đều | 86.1 ± 0.9 | 90.4 ± 0.5 | 93.2 ± 0.3 | 52.0 |
| SCS (alpha = 1) | 86.3 ± 0.6 | 90.6 ± 0.4 | 93.1 ± 0.2 | 32.2 |
| SCS (alpha = 2) | 85.2 ± 1.1 | 89.9 ± 0.7 | 92.8 ± 0.4 | 30.5 |

Với alpha = 1, SCS nhỉnh hơn trên A và B, kém 0.1 điểm trên C, nhưng tiết kiệm khoảng 38% số lượt cập nhật.

## Hạn chế

- Chỉ thử trên tác vụ phân loại và một kích thước mô hình (110M tham số); chưa biết có đúng với sinh văn bản hay mô hình lớn hơn.
- Dễ khuếch đại nhãn nhiễu vì mẫu gán nhãn sai luôn có giá trị mất mát cao.
- Chênh lệch độ chính xác rất nhỏ so với độ lệch chuẩn, nên "ngang bằng" là cách diễn đạt hợp lý hơn "tốt hơn".

## Câu hỏi nên đặt ra khi đọc

- Chi phí tính toán thêm để cập nhật s_i là bao nhiêu so với phần tiết kiệm được?
- Kết quả có giữ nguyên nếu đổi alpha theo thời gian thay vì cố định?

> Lưu ý: đây là bài báo hư cấu dùng để minh hoạ PaperViet; mọi con số đều là giả định.
