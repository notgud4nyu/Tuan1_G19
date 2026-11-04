# NHÓM 19 – BÀI TẬP LỚN PHƯƠNG PHÁP TÍNH

## Đề tài 19: Tìm cực trị của đường xu thế bằng phương pháp Newton


### 1. Dữ liệu sử dụng

Dữ liệu lấy từ `analysis_snapshot.csv` (200 dòng, 22 cột) của bộ dữ liệu camera giao thông. Mỗi đoạn tương ứng một `recording_id` (khớp với cột `analysis_segment` trong snapshot).

| Thông tin | Đoạn A | Đoạn B |
|---|---|---|
| Camera | camnutgiaocaygo3 | camnutgiaocaygo3 |
| Recording ID | camnutgiaocaygo3_2026-07-13_R01 | camnutgiaocaygo3_2026-07-16_R01 |
| Số quan sát | 100 | 100 |
| Thời gian bắt đầu | 2026-07-13 06:08:41 (+07:00) | 2026-07-16 00:00:22 (+07:00) |
| Độ dài đoạn | 68,47 phút | 48,55 phút |
| Gap nhỏ nhất / trung vị / lớn nhất | 36 / 37 / 74 giây | 24 / 25 / 50 giây |
| Ngưỡng gap (3 × trung vị) | 111 giây | 75 giây |
| Số gap vượt ngưỡng | 0 | 0 |
| `total_count` nhỏ nhất / lớn nhất | 5 / 75 | 0 / 12 |
| Trạng thái nhãn | unreviewed_prelabel | unreviewed_prelabel |


- Hai đoạn có nhãn chưa được rà soát và nghiệm thu, chỉ dùng để chạy thử chương trình, không xem là dữ liệu đã xác minh chính thức.
- Chương trình **không tái lấy mẫu** dữ liệu: cột `is_resampled` của cả 200 dòng đều là `False`, các mốc cách nhau không đều (24–74 giây).

### 2. Cấu trúc thư mục

```text
PPT_G19_T19/
├── G19.py                      # chương trình chính (có thể đặt cạnh snapshot hoặc trong thư mục con)
├── analysis_snapshot.csv       # dữ liệu nguồn
├── README.md
├── data/
│   ├── segment_A.csv           # đoạn A đã tách (dùng để đối chiếu nguồn)
│   └── segment_B.csv           # đoạn B đã tách (dùng để đối chiếu nguồn)
└── results/                    # tạo tự động khi chạy
    ├── data_check_summary.csv  # kết quả kiểm tra dữ liệu A/B
    ├── validation_summary.csv  # bảng kiểm chứng Bước 4
    ├── validation.png          # đồ thị kiểm chứng Bước 4
    ├── newton_starts.csv       # bảng 5 điểm đầu Newton của đoạn A/B
    ├── extrema_table.csv       # bảng điểm dừng + biên, phân loại, timestamp thực
    ├── sensitivity.csv         # bảng so với cực trị quan sát, độ nhạy cửa sổ/bậc
    ├── trend_A.png             # đường xu thế và các điểm dừng đoạn A
    └── trend_B.png             # đường xu thế và các điểm dừng đoạn B
```

### 3. Cấu trúc và chức năng của `G19.py`

| Phần | Nội dung |
|---|---|
| Cấu hình | `SEED = 2026`; `REC_A`, `REC_B`; 5 điểm đầu Newton (`N_START`); tối đa 100 vòng (`MAX_ITER`); dung sai bước `STEP_TOL = 1e-10`; dung sai gộp nghiệm `MERGE_TOL = 1e-6`; cửa sổ khảo sát `WINDOWS = [80, 100]`; bậc `DEGREES = [2, 3]` |
| Đọc dữ liệu, chuẩn hóa thời gian | Sắp xếp theo timestamp thật, đổi về phút từ mốc đầu rồi chuẩn hóa `s ∈ [-1, 1]` theo thời gian thật (không theo chỉ số mẫu); `total_count` đổi sang `float64`; hàm đổi `s` → phút → timestamp thực (múi giờ Asia/Ho_Chi_Minh) |
| Kiểm tra dữ liệu (`check_data`) | Số quan sát 80–300, kiểu `float64`, giá trị hợp lệ, gap > 3 × trung vị, trùng `image_id`, trùng recording/timestamp, một camera/một recording, nhãn nhất quán, hai đoạn độc lập và không trùng `image_id`, đối chiếu từng dòng với snapshot (và với `data/segment_A.csv`, `data/segment_B.csv` nếu có) |
| Newton (`newton_stationary`) | Giải `p'(s) = 0` bằng `s_{k+1} = s_k − p'(s_k)/p''(s_k)` từ 5 điểm đầu trải đều; ghi trạng thái từng điểm đầu: hội tụ / p''≈0 / phân kỳ / không hội tụ sau 100 vòng / hội tụ nhưng ra khỏi miền |
| Gộp và phân loại | Gộp nghiệm gần nhau theo dung sai; phân loại bằng dấu `p''`; nếu `p''` ≈ 0 thì xét dấu `p'` ở hai phía; so cả giá trị tại hai đầu mút để chọn cực đại/cực tiểu toàn đoạn; báo đúng khi không có điểm dừng trong miền |
| Mở rộng | So nghiệm Newton với công thức nghiệm đại số của `p'` (bậc 1 hoặc bậc 2) |
| Bước 4: kiểm chứng | `p(s) = −(s−0,3)² + 10` và `p(s) = s³ − 3s` trên [−2, 2]: so nghiệm thật, residual `|p'|`, loại cực trị |
| Bước 5: đoạn dữ liệu thật | Khớp bậc 3 (bậc 2 chỉ để đối chứng), bảng cực trị, đổi sang timestamp thực, so với cực trị đếm quan sát, đổi cỡ cửa sổ và bậc 2/3 để khảo sát độ nhạy, vẽ đồ thị |

Ghi chú về cách lấy cực trị quan sát: nếu nhiều mốc cùng giá trị cực trị thì lấy mốc xuất hiện đầu tiên (đoạn A có 3 mốc `total_count = 5`, đoạn B có 2 mốc `total_count = 12`).

### 4. Hướng dẫn chạy chương trình

Yêu cầu: Python, pandas, NumPy và matplotlib.

```powershell
python -m pip install pandas numpy matplotlib
```

Tại thư mục chứa `G19.py` (hoặc thư mục con của nơi có `analysis_snapshot.csv`), chạy:

```powershell
python G19.py
```

Toàn bộ kết quả được in ra màn hình và lưu trong thư mục `results/`.

### 5. Kết quả của lần chạy

**Kiểm tra dữ liệu:** cả hai đoạn đạt các kiểm tra; số dòng A, B không khớp nguồn đều bằng 0; `image_id` trùng giữa A và B bằng 0; hai đoạn cùng camera, recording độc lập.

**Kiểm chứng Bước 4:** Newton tìm đúng nghiệm với sai số bằng 0 (làm tròn số máy) và đúng loại cực trị: `s = 0,3` (cực đại, p = 10) cho hàm bậc hai; `s = −1` (cực đại, p = 2) và `s = 1` (cực tiểu, p = −2) cho hàm bậc ba. Với `s³ − 3s`, điểm đầu `s = 0` dừng vì `p''(0) = 0`, đúng như dự kiến.

**Đa thức bậc 3 khớp trên toàn đoạn (hệ số theo thứ tự `s³, s², s, 1`):**

| | Hệ số |
|---|---|
| Đoạn A | 4,26621071; 3,97293092; 0,29881959; 19,63402899 |
| Đoạn B | −2,12531827; 0,52175551; 1,11424889; 4,92582219 |

**Điểm dừng và cực trị toàn đoạn (bậc 3, cả hai đoạn Newton trùng công thức nghiệm với sai khác ≈ 1,1·10⁻¹⁶):**

| Đoạn | Điểm | s | Thời điểm (phút / timestamp) | p(s) | Loại |
|---|---|---|---|---|---|
| A | Điểm dừng 1 | −0,5806 | 14,36 / 2026-07-13 06:23:02 | 19,9648 | Cực đại địa phương |
| A | Điểm dừng 2 | −0,0402 | 32,86 / 2026-07-13 06:41:32 | 19,6282 | Cực tiểu địa phương |
| A | Biên trái | −1 | 0 / 2026-07-13 06:08:41 | 19,0419 | Cực tiểu toàn đoạn |
| A | Biên phải | 1 | 68,47 / 2026-07-13 07:17:09 | 28,1720 | Cực đại toàn đoạn |
| B | Điểm dừng 1 | −0,3441 | 15,92 / 2026-07-16 00:16:17 | 4,6908 | Cực tiểu địa phương |
| B | Điểm dừng 2 | 0,5078 | 36,60 / 2026-07-16 00:36:58 | 5,3479 | Cực đại địa phương |
| B | Biên trái | −1 | 0 / 2026-07-16 00:00:22 | 6,4586 | Cực đại toàn đoạn |
| B | Biên phải | 1 | 48,55 / 2026-07-16 00:48:55 | 4,4365 | Cực tiểu toàn đoạn |

Ở cả hai đoạn, cực trị toàn đoạn của đường xu thế nằm ở biên; các điểm dừng bên trong chỉ là cực trị địa phương.

**So với cực trị đếm quan sát (cửa sổ 100 mốc = toàn đoạn):** đoạn A quan sát max = 75 tại phút 63,37 và min = 5 tại phút 38,92; đoạn B quan sát max = 12 tại phút 4,12 và min = 0 tại phút 43,18. Giá trị của đường xu thế lệch nhiều so với các mốc cực trị này (xem `results/sensitivity.csv`), vì đa thức bậc 2/3 không đi qua các mốc đỉnh nhọn.

**Độ nhạy theo cỡ cửa sổ (80, 100) và bậc (2, 3):** vị trí cực trị của mô hình thay đổi khi đổi cửa sổ hoặc bậc. Ví dụ ở đoạn A bậc 3, cực đại toàn đoạn nằm trong miền (s = 0,859) với cửa sổ 80 nhưng ở biên phải với cửa sổ 100. Chi tiết xem `results/sensitivity.csv`.
