import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(2026)
df = pd.read_csv('analysis_snapshot.csv')

rec_A = 'camnutgiaocaygo3_2026-07-13_R01'
rec_B = 'camnutgiaocaygo3_2026-07-16_R01'

data_A = df[df['recording_id'] == rec_A].sort_values('timestamp').copy()
data_B = df[df['recording_id'] == rec_B].sort_values('timestamp').copy()

def process_segment(sub_df, segment_name):
    print(f"\n--- PHÂN TÍCH ĐOẠN: {segment_name} ---")
    y = sub_df['total_count'].astype(np.float64).values
    n = len(y)
    
    s = np.linspace(-1.0, 1.0, n, dtype=np.float64)
    
    poly3_coeffs = np.polyfit(s, y, 3)
    poly2_coeffs = np.polyfit(s, y, 2)
    
    p3 = np.poly1d(poly3_coeffs)
    dp3 = np.polyder(p3, 1) 
    ddp3 = np.polyder(p3, 2)  
    
    print(f"Hệ số đa thức bậc 3: {poly3_coeffs}")
    print(f"Hệ số đa thức bậc 2 (đối chứng): {poly2_coeffs}")
    
    init_points = np.linspace(-1.0, 1.0, 5, dtype=np.float64)
    roots = []
    
    for x0 in init_points:
        xk = x0
        converged = False
        for iteration in range(100):
            val_dp = dp3(xk)
            val_ddp = ddp3(xk)
            
            if abs(val_ddp) < 1e-12:
                break
                
            xk_next = xk - val_dp / val_ddp
            
            if abs(xk_next - xk) < 1e-8:
                xk = xk_next
                converged = True
                break
            xk = xk_next
            
        if converged and -1.0 <= xk <= 1.0:
            roots.append(xk)
            
    roots = np.unique(np.round(roots, 6))
    valid_extremums = []
    
    print("\nKết quả tìm nghiệm và phân loại cực trị:")
    for r in roots:
        val_ddp = ddp3(r)
        val_p = p3(r)
        
        if abs(val_ddp) > 1e-6:
            ext_type = "Cực đại" if val_ddp < 0 else "Cực tiểu"
        else:
            ext_type = "Điểm uốn / Cần kiểm tra thêm"
            
        valid_extremums.append((r, val_p, ext_type, val_ddp))
        print(f" - Nghiệm s = {r:.4f}, Giá trị p(s) = {val_p:.4f}, p''(s) = {val_ddp:.4f} -> {ext_type}")
        
    edge_vals = [p3(-1.0), p3(1.0)]
    print(f" - Giá trị tại biên trái (s=-1): {edge_vals[0]:.4f}")
    print(f" - Giá trị tại biên phải (s=1): {edge_vals[1]:.4f}")

process_segment(data_A, "Đoạn A (R01 - 13/07)")
process_segment(data_B, "Đoạn B (R01 - 16/07)")