# Sparse Curriculum Sampling: lấy mẫu theo giáo trình thưa để tinh chỉnh hiệu quả các mô hình ngôn ngữ nhỏ

*Sparse Curriculum Sampling for Efficient Fine-Tuning of Small Language Models*

An Tran and Laura Hayes  
Demo Institute of Computing (fictional affiliation)

> Bản dịch tiếng Việt của `sample-paper.pdf` (21/21 khối đã dịch), tạo bằng [PaperViet](https://github.com/mahiepit/PaperViet). Bản dịch do AI thực hiện; hãy đối chiếu bản gốc khi trích dẫn.

## Đọc nhanh

### Bài báo nói gì (3 câu)

Tinh chỉnh mô hình ngôn ngữ nhỏ tốn nhiều lượt cập nhật cho những mẫu mà mô hình đã học xong. Tác giả đề xuất SCS: theo dõi giá trị mất mát của từng mẫu bằng trung bình trượt hàm mũ, rồi lấy mẫu khó thường xuyên hơn mà vẫn giữ xác suất nhỏ cho mẫu dễ. Trên ba tập dữ liệu phân loại văn bản, SCS giữ nguyên độ chính xác nhưng cần ít hơn 38% số lượt cập nhật.

### Đóng góp chính

- Một quy tắc lấy mẫu không thêm tham số: điểm độ khó s_i cập nhật theo phương trình (1), xác suất lấy mẫu tỉ lệ với (s_i + eps)^alpha theo phương trình (2).
- Bằng chứng thực nghiệm: cùng độ chính xác với ít lượt cập nhật hơn (32.2k so với 52.0k) và phương sai giữa các seed thấp hơn.
- Phân tích trường hợp thất bại: alpha quá lớn (alpha = 2) làm giảm độ chính xác; nhãn nhiễu có thể bị lấy mẫu lặp lại.

### Phương pháp

Mỗi mẫu có một điểm độ khó, là trung bình trượt của giá trị mất mát với hệ số beta = 0.9. Xác suất chọn một mẫu tỉ lệ với điểm độ khó lũy thừa alpha: alpha = 0 là lấy mẫu đều như thường lệ, alpha càng lớn thì càng dồn vào mẫu khó. Hằng số eps giúp mẫu dễ không bao giờ bị loại hẳn.

### Kết quả

| Cấu hình | Dữ liệu A | Dữ liệu B | Dữ liệu C | Số cập nhật (k) |
|---|---|---|---|---|
| Lấy mẫu đều | 86.1 ± 0.9 | 90.4 ± 0.5 | 93.2 ± 0.3 | 52.0 |
| SCS (alpha = 1) | 86.3 ± 0.6 | 90.6 ± 0.4 | 93.1 ± 0.2 | 32.2 |
| SCS (alpha = 2) | 85.2 ± 1.1 | 89.9 ± 0.7 | 92.8 ± 0.4 | 30.5 |

Với alpha = 1, SCS nhỉnh hơn trên A và B, kém 0.1 điểm trên C, nhưng tiết kiệm khoảng 38% số lượt cập nhật.

### Hạn chế

- Chỉ thử trên tác vụ phân loại và một kích thước mô hình (110M tham số); chưa biết có đúng với sinh văn bản hay mô hình lớn hơn.
- Dễ khuếch đại nhãn nhiễu vì mẫu gán nhãn sai luôn có giá trị mất mát cao.
- Chênh lệch độ chính xác rất nhỏ so với độ lệch chuẩn, nên "ngang bằng" là cách diễn đạt hợp lý hơn "tốt hơn".

### Câu hỏi nên đặt ra khi đọc

- Chi phí tính toán thêm để cập nhật s_i là bao nhiêu so với phần tiết kiệm được?
- Kết quả có giữ nguyên nếu đổi alpha theo thời gian thay vì cố định?

> Lưu ý: đây là bài báo hư cấu dùng để minh hoạ PaperViet; mọi con số đều là giả định.

## Tóm tắt

Tinh chỉnh (fine-tuning) một mô hình ngôn ngữ (language model) đã tiền huấn luyện cho một tác vụ mới thường đòi hỏi duyệt qua tập huấn luyện (training set) nhiều lượt, dù phần lớn mẫu đã được mô hình xử lý tốt ngay sau epoch đầu tiên. Chúng tôi đề xuất Sparse Curriculum Sampling (SCS), một phương pháp chọn lọc dữ liệu (data selection) đơn giản: ước lượng độ khó của từng mẫu dựa trên giá trị mất mát gần nhất của mẫu đó, rồi lấy mẫu khó thường xuyên hơn nhưng vẫn quay lại các mẫu dễ. SCS không thêm tham số huấn luyện nào và có thể cài đặt chỉ bằng vài dòng mã. Trên ba bộ đánh giá phân loại văn bản (text classification), SCS đạt độ chính xác (accuracy) ngang với tinh chỉnh thông thường nhưng dùng ít hơn 38% số lượt cập nhật gradient, đồng thời giảm phương sai (variance) giữa các seed ngẫu nhiên (random seed). Chúng tôi cũng thảo luận khi nào phương pháp thất bại và vì sao lợi ích của nó có thể không chuyển sang các tác vụ sinh văn bản.

## 1 Giới thiệu

Các mô hình ngôn ngữ nhỏ, với dưới một tỷ tham số, vẫn hấp dẫn đối với các phòng thí nghiệm và doanh nghiệp có ngân sách tính toán hạn chế. Tuy nhiên, tinh chỉnh một mô hình như vậy vẫn buộc phải đánh đổi (trade-off) giữa chi phí và độ chính xác: huấn luyện thêm nhiều epoch thường cải thiện điểm số cuối cùng, nhưng phần lớn lượng tính toán tăng thêm lại dồn vào những mẫu mà mô hình đã học được.

Học theo giáo trình (curriculum learning) [2] giải quyết một vấn đề gần với vấn đề này bằng cách đưa các mẫu vào huấn luyện theo một trình tự có ý nghĩa, thường là từ dễ đến khó. Trên thực tế, một giáo trình cố định cần có thước đo độ khó xác định từ trước khi huấn luyện, điều mà các tập dữ liệu (dataset) mới thường không có. Trong bài báo này, chúng tôi tiếp cận theo hướng khác: thay vì sắp xếp dữ liệu một lần, chúng tôi để chính tín hiệu huấn luyện của mô hình quyết định mỗi mẫu cần được xem bao nhiêu lần.

Bài báo có ba đóng góp. Thứ nhất, chúng tôi giới thiệu SCS, một quy tắc lấy mẫu dựa trên trung bình trượt hàm mũ (exponential moving average) của giá trị mất mát trên từng mẫu. Thứ hai, chúng tôi chỉ ra bằng thực nghiệm rằng SCS giảm số lượt cập nhật gradient mà không làm giảm độ chính xác. Thứ ba, chúng tôi phân tích các trường hợp phương pháp thất bại; theo hiểu biết của chúng tôi, những trường hợp này chưa từng được báo cáo với các cách tiếp cận tương tự.

## 2 Phương pháp

Gọi D = {(x_i, y_i)}, i = 1..N, là tập huấn luyện và f(x; w) là bộ phân loại (classifier) với trọng số w. Tại bước t, chúng tôi lưu một điểm độ khó s_i cho mỗi mẫu và cập nhật điểm này mỗi khi mẫu được duyệt tới:

```text
s_i <- beta * s_i + (1 - beta) * L(f(x_i; w), y_i)  (1)
```

trong đó L là hàm mất mát entropy chéo (cross-entropy loss) và beta là hệ số làm trơn, đặt bằng 0.9 trong mọi thí nghiệm. Sau đó, các mẫu được rút ra với xác suất (probability)

```text
p_i = (s_i + eps)^alpha / sum_j (s_j + eps)^alpha  (2)
```

Số mũ alpha quyết định mức độ bộ lấy mẫu (sampler) tập trung vào các mẫu khó: alpha = 0 cho lại cách lấy mẫu đều (uniform sampling), còn giá trị lớn sẽ dồn khối lượng xác suất vào một tập con nhỏ. Hằng số nhỏ eps bảo đảm mọi mẫu luôn có xác suất được chọn khác 0, nhờ đó các mẫu dễ vẫn được xem lại và mô hình không quên chúng. Chúng tôi tối ưu trọng số bằng Adam [4] và áp dụng dropout [3] với tỉ lệ 0.1, như khi tinh chỉnh thông thường các bộ mã hóa (encoder) Transformer [1].

<small>* Đây là bài báo hư cấu, viết riêng cho bản demo của PaperViet. Phương pháp và mọi con số đều là giả định; chỉ có các tài liệu tham khảo là có thật.</small>

## 3 Thực nghiệm

Chúng tôi tinh chỉnh một bộ mã hóa 110M tham số trên ba tập dữ liệu phân loại văn bản công khai, ký hiệu là A, B và C, lần lượt gồm 12k, 45k và 120k mẫu huấn luyện. Mỗi cấu hình được lặp lại với năm seed ngẫu nhiên; chúng tôi báo cáo độ chính xác trung bình trên tập kiểm tra (test set) kèm độ lệch chuẩn (standard deviation). Phương pháp cơ sở dùng cách lấy mẫu đều với cùng tốc độ học (learning rate) 2e-5 và kích thước lô (batch size) 32.

*Bảng 1: Độ chính xác trên tập kiểm tra (%) và số lượt cập nhật gradient (nghìn lượt) trên ba tập dữ liệu. Giá trị là trung bình ± độ lệch chuẩn qua năm seed.*

```text
Phương pháp  Dữ liệu A  Dữ liệu B  Dữ liệu C  Số cập nhật (k)
Lấy mẫu đều  86.1 ± 0.9  90.4 ± 0.5  93.2 ± 0.3  52.0
SCS (alpha = 1)  86.3 ± 0.6  90.6 ± 0.4  93.1 ± 0.2  32.2
SCS (alpha = 2)  85.2 ± 1.1  89.9 ± 0.7  92.8 ± 0.4  30.5
```

Như Bảng 1 cho thấy, SCS với alpha = 1 ngang bằng hoặc nhỉnh hơn một chút so với phương pháp cơ sở trên hai trong ba tập dữ liệu và chỉ kém không quá 0.1 điểm trên tập còn lại, trong khi cần ít hơn 38% số lượt cập nhật (32.2k so với 52.0k). Độ lệch chuẩn thấp hơn gợi ý rằng khi tập trung vào các mẫu giàu thông tin, quá trình huấn luyện cũng ổn định hơn. Tuy nhiên, với alpha = 2, độ chính xác giảm trên mọi tập dữ liệu, cho thấy một bộ lấy mẫu tập trung quá mức đã bỏ qua các mẫu dễ trong thời gian quá dài.

## 4 Hạn chế

Nghiên cứu của chúng tôi có một số hạn chế. Mọi thí nghiệm đều dùng tác vụ phân loại và một kích thước mô hình duy nhất, nên chưa rõ lợi ích này có còn đúng với bài toán sinh văn bản (text generation) hay với các mô hình hàng tỷ tham số hay không. Ngoài ra, các nhãn nhiễu (noisy label) có thể liên tục nhận giá trị mất mát cao; khi đó, SCS có thể lặp đi lặp lại việc lấy những mẫu bị gán nhãn sai và khuếch đại nhiễu.

## 5 Kết luận

Chúng tôi đã trình bày Sparse Curriculum Sampling, một phương pháp gọn nhẹ tận dụng lại giá trị mất mát huấn luyện để quyết định những mẫu nào cần được chú ý nhiều hơn. Trong thiết lập của chúng tôi, phương pháp này giảm chi phí tinh chỉnh và dễ kết hợp với các quy trình huấn luyện sẵn có. Hướng nghiên cứu tiếp theo sẽ xem xét các giá trị alpha thích nghi và khả năng chống chịu nhiễu nhãn (robustness to label noise).

## Tài liệu tham khảo

- [1] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin. Attention is all you need. In Advances in Neural Information Processing Systems, 2017.

- [2] Y. Bengio, J. Louradour, R. Collobert, and J. Weston. Curriculum learning. In Proceedings of the 26th International Conference on Machine Learning, 2009.

- [3] N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. Dropout: A simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15:1929-1958, 2014.

- [4] D. P. Kingma and J. Ba. Adam: A method for stochastic optimization. In International Conference on Learning Representations, 2015.

## Ghi chú & giải thích

#### Giải thích phương trình (2)

> p_i = (s_i + eps)^alpha / sum_j (s_j + eps)^alpha

Hiểu đơn giản: mẫu nào đang "khó" (giá trị mất mát gần đây cao, nên s_i lớn) thì được bốc thăm nhiều hơn.

- **Tử số** `(s_i + eps)^alpha` là "trọng số" của mẫu i. Cộng thêm eps để mẫu dễ (s_i gần 0) vẫn có trọng số dương.
- **Mẫu số** `sum_j (s_j + eps)^alpha` là tổng trọng số của mọi mẫu, dùng để chuẩn hoá cho tổng các p_i bằng 1.
- **alpha** điều chỉnh mức "thiên vị": alpha = 0 thì mọi trọng số bằng 1, tức lấy mẫu đều; alpha = 1 thì xác suất tỉ lệ thuận với độ khó; alpha = 2 thì mẫu khó được ưu tiên rất mạnh. Bảng 1 cho thấy alpha = 2 đã ưu tiên quá đà.

Ví dụ nhỏ: có hai mẫu với s_1 = 0.1 và s_2 = 0.9, eps rất nhỏ. Với alpha = 1, mẫu 2 được chọn với xác suất khoảng 0.9; với alpha = 2, khoảng 0.99, nên mẫu 1 gần như không bao giờ được xem lại.

## Thuật ngữ

| English | Tiếng Việt |
|---|---|
| accuracy | độ chính xác |
| batch size | kích thước lô |
| classifier | bộ phân loại |
| cross-entropy loss | hàm mất mát entropy chéo |
| curriculum learning | học theo giáo trình |
| data selection | chọn lọc dữ liệu |
| dataset | tập dữ liệu |
| dropout | dropout |
| encoder | bộ mã hóa |
| epoch | epoch |
| exponential moving average | trung bình trượt hàm mũ |
| fine-tuning | tinh chỉnh |
| gradient | gradient |
| label noise | nhiễu nhãn |
| language model | mô hình ngôn ngữ |
| learning rate | tốc độ học |
| noisy label | nhãn nhiễu |
| probability | xác suất |
| random seed | seed ngẫu nhiên |
| robustness | khả năng chống chịu |
| sampler | bộ lấy mẫu |
| sampling | lấy mẫu |
| standard deviation | độ lệch chuẩn |
| test set | tập kiểm tra |
| text classification | phân loại văn bản |
| text generation | sinh văn bản |
| trade-off | đánh đổi |
| training set | tập huấn luyện |
| transformer | Transformer |
| uniform sampling | lấy mẫu đều |
| variance | phương sai |
| classification | phân loại |
| future work | hướng nghiên cứu tiếp theo |
| subset | tập con |
