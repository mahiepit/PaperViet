# Văn phong khoa học tiếng Việt khi dịch bài báo

Tài liệu này dành cho agent (và người đọc) khi dịch bài báo tiếng Anh sang tiếng Việt.
Mục tiêu: bản dịch **đọc như do một nhà nghiên cứu Việt Nam viết**, chính xác về nội dung,
thống nhất về thuật ngữ, không mang dấu vết "dịch máy".

## 1. Nguyên tắc chung

1. **Dịch ý, không dịch chữ.** Đọc trọn câu (thậm chí cả đoạn) rồi mới viết lại bằng tiếng Việt.
   Được phép tách câu dài, đảo trật tự mệnh đề, đổi bị động thành chủ động, miễn là không thêm
   hay bớt ý.
2. **Trung thành tuyệt đối với nội dung khoa học**: số liệu, đơn vị, chiều hướng (tăng/giảm,
   tốt hơn/kém hơn), mức độ chắc chắn (xem mục 4), phạm vi khẳng định ("trên hai trong ba tập dữ
   liệu" không được thành "trên mọi tập dữ liệu").
3. **Khách quan, ngắn gọn.** Không thêm bình luận của người dịch vào phần dịch. Nếu cần giải
   thích, đặt trong ghi chú riêng (`notes.vi.md`) hoặc trong ngoặc vuông `[ND: ...]` thật hạn chế.
4. **Câu ngắn hơn bản gốc là bình thường.** Một câu tiếng Anh 40 từ có ba mệnh đề quan hệ thường
   nên thành hai câu tiếng Việt.

## 2. Những thứ KHÔNG dịch

| Giữ nguyên | Ví dụ |
|---|---|
| Công thức, LaTeX, biến, ký hiệu | `$\mathcal{L}(\theta)$`, `x_i`, `alpha`, `O(n log n)` |
| Mã nguồn, tên hàm, lệnh, đường dẫn, URL | `torch.nn.Linear`, `https://...` |
| Trích dẫn | `[12]`, `[3, 5]`, `(Nguyen et al., 2021)` (có thể viết "Nguyen và cộng sự (2021)" khi trích trong câu) |
| Tên riêng: người, tổ chức, mô hình, tập dữ liệu, phương pháp do tác giả đặt tên | BERT, ResNet-50, ImageNet, "Sparse Curriculum Sampling" |
| Từ viết tắt | giữ dạng tiếng Anh: LLM, CNN, RCT, GDP; lần đầu ghi "mô hình ngôn ngữ lớn (large language model, LLM)" |
| Danh sách tài liệu tham khảo | giữ nguyên toàn bộ |
| Số liệu, đơn vị | 87.4%, 2e-5, 12 ms, 3.2 GB, p < 0.05 |

Tên phương pháp do tác giả đặt: giữ nguyên tên, lần đầu có thể kèm dịch nghĩa, ví dụ
"Sparse Curriculum Sampling (SCS), tạm dịch là lấy mẫu theo giáo trình thưa".

## 3. Thuật ngữ

- **Lần đầu** một thuật ngữ xuất hiện trong phần thân: tiếng Việt trước, tiếng Anh trong ngoặc:
  "học tăng cường (reinforcement learning)". Có viết tắt thì gộp: "học tăng cường (reinforcement
  learning, RL)".
- **Các lần sau**: chỉ dùng tiếng Việt (hoặc viết tắt). Không đổi qua lại giữa hai cách dịch.
- **Tiêu đề và đề mục**: không thêm ngoặc tiếng Anh.
- Thuật ngữ mà giới nghiên cứu Việt Nam thường giữ tiếng Anh (epoch, dropout, token, prompt,
  embedding, Transformer, softmax...) thì giữ tiếng Anh, không cố "Việt hoá" gượng ép.
- Mỗi bài có một tệp `glossary.csv` riêng trong thư mục làm việc: **mỗi dòng một thuật ngữ, một
  cách dịch**. Đây là "hợp đồng" để mọi đoạn dịch thống nhất. Gặp thuật ngữ mới thì thêm vào.
- Khi bảng thuật ngữ có nhiều phương án (cột `vi` có dấu `|`), chọn phương án đầu tiên trừ khi
  ngữ cảnh đòi hỏi khác, rồi ghi lựa chọn vào `glossary.csv` của bài.
- Chính tả: chọn một kiểu đặt dấu và dùng nhất quán trong cả bài ("hóa"/"hoá", "lý"/"lí").
  Bảng thuật ngữ có sẵn dùng kiểu "hóa", "lý", "tỷ". Công cụ kiểm tra coi hai kiểu là như nhau.

## 4. Mức độ chắc chắn (hedging) – không làm mạnh hay yếu đi

| Tiếng Anh | Tiếng Việt nên dùng |
|---|---|
| demonstrate, prove | chứng minh, chứng tỏ |
| show | cho thấy, chỉ ra |
| indicate | cho thấy, chỉ ra |
| suggest | gợi ý, cho thấy (mức yếu) |
| may / can (khả năng) | có thể |
| might / could (khả năng thấp) | có lẽ, có khả năng |
| likely / unlikely | nhiều khả năng / ít có khả năng |
| appear to, seem to | dường như |
| it is possible that | có khả năng là |
| we hypothesize that | chúng tôi giả thuyết rằng / chúng tôi đặt giả thuyết rằng |
| to some extent | ở một mức độ nào đó |
| significantly (thống kê) | có ý nghĩa thống kê |
| significantly (thông thường) | đáng kể, rõ rệt |
| slightly | một chút, nhỉnh hơn |
| comparable to | tương đương, ngang với |

"significantly" là bẫy hay gặp: nếu bài có kiểm định thống kê (p-value, khoảng tin cậy) thì
dịch "có ý nghĩa thống kê"; nếu không thì "đáng kể".

## 5. Lỗi "văn dịch máy" cần tránh

### 5.1 "một cách + tính từ" (dịch từ trạng từ -ly)

- ✗ Phương pháp này cải thiện độ chính xác **một cách đáng kể**.
- ✓ Phương pháp này cải thiện độ chính xác **đáng kể**. / ...**làm tăng rõ rệt** độ chính xác.
- ✗ Mô hình được huấn luyện **một cách hiệu quả**. → ✓ Mô hình huấn luyện **nhanh** / **tốn ít tài nguyên**.

### 5.2 Bị động "được ... bởi"

Tiếng Việt chuộng câu chủ động; "bị/được" mang sắc thái tốt/xấu, không trung tính như passive
voice tiếng Anh.

- ✗ Tập dữ liệu **được thu thập bởi** các tác giả.
- ✓ Các tác giả **đã thu thập** tập dữ liệu. / Tập dữ liệu **do** các tác giả thu thập.
- ✗ Kết quả **được thể hiện** trong Bảng 2. → ✓ Bảng 2 **trình bày** kết quả. / Kết quả **ở** Bảng 2.
- ✗ Các tham số **được khởi tạo** ngẫu nhiên. → ✓ Các tham số **khởi tạo** ngẫu nhiên. (bỏ "được" khi không cần)

### 5.3 Lạm dụng danh từ hóa "việc", "sự"

- ✗ **Việc sử dụng** dropout giúp **sự giảm** hiện tượng quá khớp.
- ✓ **Dùng** dropout giúp **giảm** quá khớp.
- ✗ **Sự** gia tăng của kích thước lô dẫn tới **sự** suy giảm của độ chính xác.
- ✓ Tăng kích thước lô làm độ chính xác giảm.

### 5.4 Đại từ "nó" cho sự vật, "điều này" nối chuỗi

- ✗ **Nó** đạt độ chính xác 91%. → ✓ **Mô hình** đạt độ chính xác 91%.
- ✗ ...**Điều này** cho thấy... **Điều này** có nghĩa là... → lặp lại chủ ngữ cụ thể hoặc nối câu.

### 5.5 Mạo từ và số nhiều

- Không dịch "the/a/an" thành "cái", "một" khi không cần: "the model" → "mô hình" (hoặc
  "mô hình này"), không phải "cái mô hình".
- Không thêm "các/những" máy móc cho mọi danh từ số nhiều: "Experiments show..." → "Thực nghiệm cho thấy...".

### 5.6 Chuỗi "của"

- ✗ độ chính xác **của** mô hình **của** chúng tôi **trên** tập kiểm tra **của** ImageNet
- ✓ độ chính xác của mô hình chúng tôi trên tập kiểm tra ImageNet

### 5.7 Từ nối dịch thẳng

| Tiếng Anh | Tránh | Nên dùng |
|---|---|---|
| while (đối lập) | trong khi | còn, trong khi đó, nhưng |
| In order to | Để mà | Để |
| Moreover / Furthermore | Hơn thế nữa (lặp lại) | Ngoài ra, Bên cạnh đó, Hơn nữa (luân phiên) |
| However, | Tuy nhiên thì | Tuy nhiên, |
| Note that | Lưu ý rằng là | Cần lưu ý rằng / Lưu ý: |
| respectively | một cách tương ứng | lần lượt (đặt trước danh sách) |
| i.e. / e.g. | i.e. | tức là / ví dụ, chẳng hạn |
| et al. | và những người khác | và cộng sự (hoặc giữ "et al.") |

## 6. Mẫu câu thường gặp trong bài báo

| Tiếng Anh | Tiếng Việt |
|---|---|
| In this paper, we propose ... | Trong bài báo này, chúng tôi đề xuất ... |
| We show that ... | Chúng tôi chỉ ra rằng ... |
| We find that ... | Chúng tôi nhận thấy ... |
| Our contributions are threefold. | Bài báo có ba đóng góp chính. |
| To the best of our knowledge, ... | Theo hiểu biết của chúng tôi, ... |
| outperforms X by 3 points | vượt X 3 điểm / cao hơn X 3 điểm |
| achieves state-of-the-art results | đạt kết quả tốt nhất hiện nay |
| is on par with / comparable to | ngang với / tương đương |
| We leave X for future work. | Chúng tôi để X cho các nghiên cứu sau. |
| Without loss of generality, | Không mất tính tổng quát, |
| As shown in Figure 3, | Như Hình 3 cho thấy, / Hình 3 cho thấy |
| Section 4 / Table 2 / Figure 3 / Eq. (5) | Mục 4 / Bảng 2 / Hình 3 / phương trình (5) |
| Appendix A / Algorithm 1 / Theorem 2 | Phụ lục A / Thuật toán 1 / Định lý 2 |
| Lemma / Corollary / Proof | Bổ đề / Hệ quả / Chứng minh |

"We" của tác giả dịch là **"chúng tôi"**. Chỉ dùng "chúng ta" khi tác giả rõ ràng gộp cả người
đọc ("we can see from Eq. (2) that..." → "từ phương trình (2) có thể thấy...", thường tốt hơn là
bỏ chủ ngữ).

## 7. Số, đơn vị, dấu câu

- **Mặc định giữ nguyên cách viết số của bản gốc** (dấu chấm thập phân: 0.9, 87.4%) để người đọc
  đối chiếu với bảng, hình, công thức. Nếu người dùng yêu cầu chuẩn trình bày Việt Nam thì đổi
  sang dấu phẩy thập phân (0,9; 87,4%) **trong câu văn**, không bao giờ đổi trong công thức, mã,
  bảng số liệu. Công cụ kiểm tra chấp nhận cả hai cách.
- 12k, 110M, 2e-5: giữ nguyên. Có thể diễn giải "12k" thành "12 nghìn" nếu người dùng muốn.
- Đơn vị SI giữ nguyên ký hiệu: ms, GB, °C, mg/kg.
- Ngoặc kép tiếng Việt: “...” hoặc "..." – thống nhất trong bài. Không đặt dấu cách trước dấu
  câu (`,` `.` `:` `;` `?` `!`).
- Đề mục viết hoa chữ cái đầu câu: "Kết quả thực nghiệm", không viết "Kết Quả Thực Nghiệm".
- Đánh số mục giữ nguyên: "3.2 Thiết lập thực nghiệm".

## 8. Ví dụ trước / sau

> EN: The proposed approach is shown to significantly reduce the training time while being robust to the choice of hyperparameters.

- ✗ Cách tiếp cận được đề xuất được chỉ ra là làm giảm một cách đáng kể thời gian huấn luyện trong khi mạnh mẽ đối với sự lựa chọn của các siêu tham số.
- ✓ Cách tiếp cận đề xuất giảm đáng kể thời gian huấn luyện và ít nhạy cảm với việc chọn siêu tham số.

> EN: It is worth noting that these gains might not hold for larger models.

- ✗ Nó đáng để lưu ý rằng những lợi ích này có thể không giữ cho các mô hình lớn hơn.
- ✓ Cần lưu ý rằng mức cải thiện này có lẽ không còn đúng với các mô hình lớn hơn.

> EN: Patients in the treatment group were followed up for 12 months, and adverse events were recorded by the investigators.

- ✗ Các bệnh nhân trong nhóm điều trị đã được theo dõi trong 12 tháng, và các biến cố bất lợi đã được ghi lại bởi các nhà nghiên cứu.
- ✓ Bệnh nhân nhóm can thiệp được theo dõi 12 tháng; nghiên cứu viên ghi nhận mọi biến cố bất lợi.

> EN: A one-unit increase in the interest rate is associated with a 0.4 percentage point decline in investment.

- ✗ Một sự tăng một đơn vị trong lãi suất là được liên kết với một sự suy giảm 0.4 điểm phần trăm trong đầu tư.
- ✓ Lãi suất tăng một đơn vị gắn với mức giảm 0.4 điểm phần trăm của đầu tư.

(Chú ý: "is associated with" chỉ là tương quan – không dịch thành "gây ra" hay "dẫn đến".)

## 9. Tự kiểm tra trước khi giao

- [ ] Mọi số liệu, trích dẫn `[n]`, công thức, tên riêng còn nguyên.
- [ ] Thuật ngữ khớp `glossary.csv` của bài; lần đầu có tiếng Anh trong ngoặc.
- [ ] Không còn "một cách", "được ... bởi", câu mở đầu bằng "Nó", chuỗi "việc/sự".
- [ ] Mức độ chắc chắn giữ đúng (suggest ≠ prove; correlation ≠ causation).
- [ ] Đọc lại thành tiếng một đoạn bất kỳ: nghe có tự nhiên không?
- [ ] Chạy `glossary.py check <thư mục làm việc>` và sửa mọi cảnh báo `WARN`.
