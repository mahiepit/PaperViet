<!-- paperviet chunk-02 | bản dịch tiếng Việt -->

<!-- b9 | heading 1 | p1 -->
2 Phương pháp

<!-- b10 | paragraph | p1 -->
Gọi D = {(x_i, y_i)}, i = 1..N, là tập huấn luyện và f(x; w) là bộ phân loại (classifier) với trọng số w. Tại bước t, chúng tôi lưu một điểm độ khó s_i cho mỗi mẫu và cập nhật điểm này mỗi khi mẫu được duyệt tới:

<!-- b11 | equation | keep | p1 -->

<!-- b12 | paragraph | p1 -->
trong đó L là hàm mất mát entropy chéo (cross-entropy loss) và beta là hệ số làm trơn, đặt bằng 0.9 trong mọi thí nghiệm. Sau đó, các mẫu được rút ra với xác suất (probability)

<!-- b13 | equation | keep | p1 -->

<!-- b14 | paragraph | p1 -->
Số mũ alpha quyết định mức độ bộ lấy mẫu (sampler) tập trung vào các mẫu khó: alpha = 0 cho lại cách lấy mẫu đều (uniform sampling), còn giá trị lớn sẽ dồn khối lượng xác suất vào một tập con nhỏ. Hằng số nhỏ eps bảo đảm mọi mẫu luôn có xác suất được chọn khác 0, nhờ đó các mẫu dễ vẫn được xem lại và mô hình không quên chúng. Chúng tôi tối ưu trọng số bằng Adam [4] và áp dụng dropout [3] với tỉ lệ 0.1, như khi tinh chỉnh thông thường các bộ mã hóa (encoder) Transformer [1].

<!-- b15 | footnote | p1 -->
* Đây là bài báo hư cấu, viết riêng cho bản demo của PaperViet. Phương pháp và mọi con số đều là giả định; chỉ có các tài liệu tham khảo là có thật.

<!-- b16 | heading 1 | p2 -->
3 Thực nghiệm

<!-- b17 | paragraph | p2 -->
Chúng tôi tinh chỉnh một bộ mã hóa 110M tham số trên ba tập dữ liệu phân loại văn bản công khai, ký hiệu là A, B và C, lần lượt gồm 12k, 45k và 120k mẫu huấn luyện. Mỗi cấu hình được lặp lại với năm seed ngẫu nhiên; chúng tôi báo cáo độ chính xác trung bình trên tập kiểm tra (test set) kèm độ lệch chuẩn (standard deviation). Phương pháp cơ sở dùng cách lấy mẫu đều với cùng tốc độ học (learning rate) 2e-5 và kích thước lô (batch size) 32.

<!-- b18 | caption | p2 -->
Bảng 1: Độ chính xác trên tập kiểm tra (%) và số lượt cập nhật gradient (nghìn lượt) trên ba tập dữ liệu. Giá trị là trung bình ± độ lệch chuẩn qua năm seed.

<!-- b19 | table | keep | p2 -->
Phương pháp  Dữ liệu A  Dữ liệu B  Dữ liệu C  Số cập nhật (k)
Lấy mẫu đều  86.1 ± 0.9  90.4 ± 0.5  93.2 ± 0.3  52.0
SCS (alpha = 1)  86.3 ± 0.6  90.6 ± 0.4  93.1 ± 0.2  32.2
SCS (alpha = 2)  85.2 ± 1.1  89.9 ± 0.7  92.8 ± 0.4  30.5

<!-- b20 | paragraph | p2 -->
Như Bảng 1 cho thấy, SCS với alpha = 1 ngang bằng hoặc nhỉnh hơn một chút so với phương pháp cơ sở trên hai trong ba tập dữ liệu và chỉ kém không quá 0.1 điểm trên tập còn lại, trong khi cần ít hơn 38% số lượt cập nhật (32.2k so với 52.0k). Độ lệch chuẩn thấp hơn gợi ý rằng khi tập trung vào các mẫu giàu thông tin, quá trình huấn luyện cũng ổn định hơn. Tuy nhiên, với alpha = 2, độ chính xác giảm trên mọi tập dữ liệu, cho thấy một bộ lấy mẫu tập trung quá mức đã bỏ qua các mẫu dễ trong thời gian quá dài.
