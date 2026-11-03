# ĐỀ TÀI 19: TÌM CỰC TRỊ CỦA ĐƯỜNG XU THẾ BẰNG PHƯƠNG PHÁP NEWTON

## 1. Thông Tin Nhóm & Thành Viên
* **Tên nhóm / Số hiệu nhóm:** [ĐIỀN TÊN/SỐ HIỆU NHÓM TẠI ĐÂY - Ví dụ: Nhóm 19]
* **Danh sách thành viên:**
  * [Thành viên 1] - [MSSV] - Phụ trách: [Mảng công việc]
  * [Thành viên 2] - [MSSV] - Phụ trách: [Mảng công việc]
  * [Thành viên 3] - [MSSV] - Phụ trách: [Mảng công việc]

---

## 2. Nguồn Dữ Liệu & Đoạn Dữ Liệu Lựa Chọn (A/B)

### Nguồn dữ liệu chung:
* Dữ liệu đầu vào được mở trực tiếp từ bảng phân tích chung: `shared/analysis_snapshot.csv`
* Biến số quan sát: `total_count` (tái lấy mẫu chuẩn gap $h_0 = 30$s).

### Trích xuất 2 đoạn dữ liệu A và B:
Dữ liệu được lọc từ tập `analysis_snapshot.csv` dựa trên `recording_id`:
1. **Đoạn A:** 
   * `recording_id`: `camnutgiaocaygo3_2026-07-13_R01`
   * Số lượng mốc quan sát: 100 mốc liên tục (nằm trong khoảng 80–300 mốc chuẩn gap).
2. **Đoạn B:** 
   * `recording_id`: `camnutgiaocaygo3_2026-07-16_R01`
   * Số lượng mốc quan sát: 100 mốc liên tục (nằm trong khoảng 80–300 mốc chuẩn gap).

---

## 3. Cấu Trúc Mã Nguồn & Phương Pháp Kỹ Thuật

* **Tệp thi hành chính:** `G19.py`
* **Kiểu dữ liệu xử lý:** `float64`
* **Cố định hạt giống:** `np.random.seed(2026)`

### Quy trình các bước xử lý trong `G19.py`:
1. **Chuẩn hóa thời gian:** Đưa trục thời gian thực về đoạn không chiều $s \in [-1, 1]$.
2. **Khớp đa thức xu thế:** 
   * Khớp đa thức bậc 3: $p(s) = c_3 s^3 + c_2 s^2 + c_1 s + c_0$.
   * Khớp đa thức bậc 2 làm đối chứng.
   * Tính các đạo hàm $p'(s)$ và $p''(s)$.
3. **Tìm cực trị bằng thuật toán Newton:**
   * Giải phương trình $p'(s) = 0$ thông qua công thức lặp: $s_{k+1} = s_k - \frac{p'(s_k)}{p''(s_k)}$.
   * Khởi tạo 5 điểm xuất phát rải đều trên $[-1, 1]$, tối đa 100 vòng lặp.
   * Kiểm tra điều kiện dừng và phát hiện các trường hợp chia cho $0$ ($|p''(s)| < 10^{-12}$) hoặc nghiệm ra khỏi miền $[-1, 1]$.
4. **Phân loại cực trị:**
   * Dùng dấu của $p''(s)$ tại nghiệm tìm được: $p''(s) < 0 \rightarrow$ Cực đại, $p''(s) > 0 \rightarrow$ Cực tiểu.
   * So sánh giá trị cực trị với giá trị tại hai biên $s = -1$ và $s = 1$.

---

## 4. Hướng Dẫn Cách Chạy Code

### Yêu cầu môi trường:
* Python phiên bản 3.8+
* Các thư viện cần thiết: `numpy`, `pandas`, `matplotlib`

### Cài đặt thư viện phụ thuộc (nếu chưa có):
```bash
pip install numpy pandas matplotlib
```

### Cấu trúc thư mục chạy code:
Đảm bảo tệp dữ liệu `analysis_snapshot.csv` nằm trong cùng thư mục (hoặc chuẩn bị đường dẫn `shared/analysis_snapshot.csv` phù hợp).

```text
├── analysis_snapshot.csv
├── G19.py
└── README.md
```

### Lệnh thực thi:
Mở terminal / command prompt tại thư mục chứa dự án và chạy câu lệnh:
```bash
python G19.py
```

---

## 5. Kết Quả Dự Kiến Khi Chạy Code
Chương trình sẽ in trực tiếp ra màn hình console:
* Các hệ số đa thức bậc 3 và bậc 2 của đoạn A và B.
* Các nghiệm $s$ thỏa mãn $p'(s) = 0$ tìm được bằng phương pháp Newton.
* Phân loại nghiệm (Cực đại / Cực tiểu / Điểm uốn) kèm giá trị $p(s)$ và $p''(s)$.
* Giá trị đa thức tại các biên $s = -1$ và $s = 1$.