<!-- paperviet chunk-03 | bản dịch tiếng Việt -->

<!-- b21 | heading 1 | p2 -->
4 Hạn chế

<!-- b22 | paragraph | p2 -->
Nghiên cứu của chúng tôi có một số hạn chế. Mọi thí nghiệm đều dùng tác vụ phân loại và một kích thước mô hình duy nhất, nên chưa rõ lợi ích này có còn đúng với bài toán sinh văn bản (text generation) hay với các mô hình hàng tỷ tham số hay không. Ngoài ra, các nhãn nhiễu (noisy label) có thể liên tục nhận giá trị mất mát cao; khi đó, SCS có thể lặp đi lặp lại việc lấy những mẫu bị gán nhãn sai và khuếch đại nhiễu.

<!-- b23 | heading 1 | p2 -->
5 Kết luận

<!-- b24 | paragraph | p2 -->
Chúng tôi đã trình bày Sparse Curriculum Sampling, một phương pháp gọn nhẹ tận dụng lại giá trị mất mát huấn luyện để quyết định những mẫu nào cần được chú ý nhiều hơn. Trong thiết lập của chúng tôi, phương pháp này giảm chi phí tinh chỉnh và dễ kết hợp với các quy trình huấn luyện sẵn có. Hướng nghiên cứu tiếp theo sẽ xem xét các giá trị alpha thích nghi và khả năng chống chịu nhiễu nhãn (robustness to label noise).

<!-- b25 | heading 1 | p2 -->
Tài liệu tham khảo
