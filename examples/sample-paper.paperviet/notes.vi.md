### Giải thích phương trình (2)

> p_i = (s_i + eps)^alpha / sum_j (s_j + eps)^alpha

Hiểu đơn giản: mẫu nào đang "khó" (giá trị mất mát gần đây cao, nên s_i lớn) thì được bốc thăm nhiều hơn.

- **Tử số** `(s_i + eps)^alpha` là "trọng số" của mẫu i. Cộng thêm eps để mẫu dễ (s_i gần 0) vẫn có trọng số dương.
- **Mẫu số** `sum_j (s_j + eps)^alpha` là tổng trọng số của mọi mẫu, dùng để chuẩn hoá cho tổng các p_i bằng 1.
- **alpha** điều chỉnh mức "thiên vị": alpha = 0 thì mọi trọng số bằng 1, tức lấy mẫu đều; alpha = 1 thì xác suất tỉ lệ thuận với độ khó; alpha = 2 thì mẫu khó được ưu tiên rất mạnh. Bảng 1 cho thấy alpha = 2 đã ưu tiên quá đà.

Ví dụ nhỏ: có hai mẫu với s_1 = 0.1 và s_2 = 0.9, eps rất nhỏ. Với alpha = 1, mẫu 2 được chọn với xác suất khoảng 0.9; với alpha = 2, khoảng 0.99, nên mẫu 1 gần như không bao giờ được xem lại.
