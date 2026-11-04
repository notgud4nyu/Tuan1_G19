import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SEED = 2026
np.random.seed(SEED)  
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
SNAPSHOT = next(
    (p for p in (HERE / "analysis_snapshot.csv", HERE.parent / "analysis_snapshot.csv") if p.is_file()),
    None,
)
if SNAPSHOT is None:
    raise FileNotFoundError("Không tìm thấy analysis_snapshot.csv (cạnh G19.py hoặc ở thư mục cha).")
OUT = SNAPSHOT.parent / "results"
OUT.mkdir(exist_ok=True)

REC_A = "camnutgiaocaygo3_2026-07-13_R01"
REC_B = "camnutgiaocaygo3_2026-07-16_R01"

N_START = 5          
MAX_ITER = 100       
STEP_TOL = 1e-10    
D2_ZERO = 1e-12      
MERGE_TOL = 1e-6    
WINDOWS = [80, 100]       
REQUIRED_COLS = [         
    "image_id", "camera_id", "recording_id", "timestamp", "total_count", "label_status",
]
DEGREES = [2, 3]



def add_normalized_time(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm t_min (phút từ mốc đầu) và s in [-1, 1] theo timestamp thật."""
    df["t_min"] = (df["dt"] - df["dt"].iloc[0]).dt.total_seconds() / 60.0
    t_max = df["t_min"].iloc[-1]
    df["s"] = 0.0 if t_max <= 1e-12 else 2.0 * df["t_min"] / t_max - 1.0
    return df


def prepare_segment(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["dt"] = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    df["total_count"] = pd.to_numeric(df["total_count"], errors="raise").astype(np.float64)
    df = df.sort_values("dt").reset_index(drop=True)
    return add_normalized_time(df)


def extract_window(df: pd.DataFrame, window_size: int) -> pd.DataFrame:
    if window_size > len(df):
        raise ValueError(f"window_size {window_size} vượt quá số quan sát {len(df)}")
    sub = df.iloc[:window_size].copy().reset_index(drop=True)
    return add_normalized_time(sub)


def s_to_t(s, t_min_val, t_max_val):
    return t_min_val + (s + 1.0) / 2.0 * (t_max_val - t_min_val)


def s_to_timestamp(s, t_min_val, t_max_val, start_dt) -> str:
    minutes = s_to_t(s, t_min_val, t_max_val)
    return (start_dt + pd.Timedelta(seconds=float(minutes * 60.0))).tz_convert("Asia/Ho_Chi_Minh").isoformat()


def check_segment(name: str, seg: pd.DataFrame) -> dict:
    y = seg["total_count"].to_numpy(dtype=np.float64)
    gaps = seg["dt"].diff().dt.total_seconds().dropna()
    gaps = gaps[gaps > 0]
    med = gaps.median()
    res = {
        "segment": name,
        "n_obs": len(seg),
        "count_ok": 80 <= len(seg) <= 300,
        "dtype": str(y.dtype),
        "valid_values": bool(np.isfinite(y).all() and (y >= 0).all()),
        "gap_min_s": gaps.min(), "gap_median_s": med, "gap_max_s": gaps.max(),
        "gap_threshold_s": 3 * med,
        "gaps_over_threshold": int((gaps > 3 * med).sum()),
        "dup_image_id": int(seg["image_id"].duplicated().sum()),
        "dup_recording_time": int(seg.duplicated(subset=["recording_id", "dt"]).sum()),
        "n_recording": seg["recording_id"].nunique(),
        "n_camera": seg["camera_id"].nunique(),
        "label_status": ",".join(sorted(seg["label_status"].dropna().unique())),
        "label_consistent": bool(seg["label_status"].notna().all() and seg["label_status"].nunique() == 1),
    }
    res["passed"] = bool(
        res["count_ok"] and res["valid_values"] and res["gaps_over_threshold"] == 0
        and res["dup_image_id"] == 0 and res["dup_recording_time"] == 0
        and res["n_recording"] == 1 and res["n_camera"] == 1 and res["label_consistent"]
    )
    return res


def check_data(seg_a, seg_b, snapshot) -> bool:
    print("=" * 60 + "\nKIỂM TRA DỮ LIỆU A/B\n" + "=" * 60)
    ra, rb = check_segment("A", seg_a), check_segment("B", seg_b)
    summary = pd.DataFrame([ra, rb])
    print(summary.T.to_string(header=False))

    overlap = len(set(seg_a["image_id"]) & set(seg_b["image_id"]))
    same_cam = set(seg_a["camera_id"]) == set(seg_b["camera_id"])
    indep = set(seg_a["recording_id"]).isdisjoint(set(seg_b["recording_id"]))
    same_label = set(seg_a["label_status"]) == set(seg_b["label_status"])
    print(f"\nImage ID trùng giữa A/B: {overlap} | cùng camera: {same_cam} | "
          f"recording độc lập: {indep} | cùng trạng thái nhãn: {same_label}")

   
    cols = ["image_id", "camera_id", "recording_id", "timestamp", "total_count", "label_status"]
    src = snapshot[cols].copy()
    src["timestamp"] = pd.to_datetime(src["timestamp"], utc=True)
    src["total_count"] = src["total_count"].astype(np.float64)
    src = src.drop_duplicates()
    mismatches = 0
    for nm, seg, fname in (("A", seg_a, "segment_A.csv"), ("B", seg_b, "segment_B.csv")):
        f = SNAPSHOT.parent / "data" / fname
        to_check = seg[cols].copy()
        to_check["timestamp"] = seg["dt"]
        if f.is_file():
            to_check = pd.read_csv(f, dtype={"image_id": str})[cols]
            to_check["timestamp"] = pd.to_datetime(to_check["timestamp"], utc=True)
            to_check["total_count"] = to_check["total_count"].astype(np.float64)
            same_set = set(to_check["image_id"]) == set(seg["image_id"])
            print(f"(đối chiếu thêm file {f.name}) cùng tập image_id với đoạn {nm} tách từ snapshot: {same_set}")
            mismatches += 0 if same_set else 1
        m = to_check.merge(src, on=cols, how="left", indicator=True, validate="many_to_one")
        bad = int((m["_merge"] != "both").sum())
        mismatches += bad
        print(f"Số dòng {nm} không khớp nguồn: {bad}")

    ok = ra["passed"] and rb["passed"] and overlap == 0 and same_cam and indep and same_label and mismatches == 0
    print("\nKẾT LUẬN:", "ĐẠT - A/B hợp lệ, độc lập, khớp nguồn" if ok else "CHƯA ĐẠT - xem các mục trên")
    print("Lưu ý: nhãn 'unreviewed_prelabel' chưa được rà soát, chỉ dùng để chạy thử.\n")
    summary.to_csv(OUT / "data_check_summary.csv", index=False, encoding="utf-8-sig")
    return ok


def newton_stationary(p: np.poly1d, lo: float, hi: float) -> pd.DataFrame:
    """Chạy Newton từ N_START điểm đầu trải đều trên [lo, hi]; ghi lại trạng thái từng điểm đầu."""
    dp, ddp = np.polyder(p, 1), np.polyder(p, 2)
    rows = []
    for x0 in np.linspace(lo, hi, N_START, dtype=np.float64):
        xk, status, it = float(x0), "không hội tụ sau 100 vòng", 0
        for it in range(1, MAX_ITER + 1):
            d2 = ddp(xk)
            if abs(d2) < D2_ZERO:
                status = "dừng: p''≈0"
                break
            xn = xk - dp(xk) / d2
            if not np.isfinite(xn) or abs(xn) > 1e6:
                status, xk = "phân kỳ", float("nan")
                break
            step = abs(xn - xk)
            xk = xn
            if step < STEP_TOL:
                status = "hội tụ"
                break
        if status == "hội tụ" and not (lo - 1e-9 <= xk <= hi + 1e-9):
            status = "hội tụ nhưng ra khỏi miền"
        rows.append({
            "s_dau": x0, "s_cuoi": xk, "so_vong": it, "trang_thai": status,
            "|p'(s_cuoi)|": abs(dp(xk)) if np.isfinite(xk) else np.nan,
        })
    return pd.DataFrame(rows)


def merge_roots(roots, tol=MERGE_TOL):
    """Gộp nghiệm gần nhau theo dung sai (nhóm các nghiệm đã sắp xếp có khoảng cách <= tol)."""
    roots = sorted(roots)
    groups = []
    for r in roots:
        if groups and abs(r - groups[-1][-1]) <= tol:
            groups[-1].append(r)
        else:
            groups.append([r])
    return [float(np.mean(g)) for g in groups]


def classify(p: np.poly1d, r: float, lo: float, hi: float):
    """Phân loại bằng dấu p''; nếu p''≈0 thì xét dấu p' ở hai phía."""
    dp, ddp = np.polyder(p, 1), np.polyder(p, 2)
    scale = max(1.0, float(np.max(np.abs(p.coeffs))))
    d2 = float(ddp(r))
    if abs(d2) > 1e-8 * scale:
        return ("Cực đại" if d2 < 0 else "Cực tiểu"), d2
    h = 1e-3 * (hi - lo)
    left, right = dp(r - h), dp(r + h)
    if left > 0 > right:
        return "Cực đại (p''=0, p' đổi dấu +→-)", d2
    if left < 0 < right:
        return "Cực tiểu (p''=0, p' đổi dấu -→+)", d2
    return "Không phải cực trị (p' không đổi dấu)", d2


def analyze_poly(p: np.poly1d, lo: float, hi: float):
    """Trả về (bảng điểm đầu, bảng cực trị gồm cả biên, thông tin cực đại/tiểu toàn đoạn)."""
    starts = newton_stationary(p, lo, hi)
    good = starts.loc[starts["trang_thai"] == "hội tụ", "s_cuoi"].tolist()
    roots = [min(max(r, lo), hi) for r in merge_roots(good)]

    rows = []
    for r in roots:
        kind, d2 = classify(p, r, lo, hi)
        rows.append({"s": r, "p(s)": float(p(r)), "p''(s)": d2, "loai": kind})
    rows.append({"s": lo, "p(s)": float(p(lo)), "p''(s)": float(np.polyder(p, 2)(lo)), "loai": "Biên trái"})
    rows.append({"s": hi, "p(s)": float(p(hi)), "p''(s)": float(np.polyder(p, 2)(hi)), "loai": "Biên phải"})
    ext = pd.DataFrame(rows)

    cand = ext[~ext["loai"].str.startswith("Không phải")].copy()
    tol = 1e-9 * max(1.0, cand["p(s)"].abs().max())
    gmax_val, gmin_val = cand["p(s)"].max(), cand["p(s)"].min()
    ext["toan_doan"] = ""
    ext.loc[ext["p(s)"].sub(gmax_val).abs().le(tol) & ext.index.isin(cand.index), "toan_doan"] += "MAX "
    ext.loc[ext["p(s)"].sub(gmin_val).abs().le(tol) & ext.index.isin(cand.index), "toan_doan"] += "MIN "
    info = {"has_interior": len(roots) > 0, "max": gmax_val, "min": gmin_val}
    return starts, ext, info


def closed_form_stationary(p: np.poly1d):
    """Mở rộng: nghiệm p'(s)=0 bằng công thức đại số (p' bậc 1 hoặc bậc 2)."""
    dp = np.polyder(p, 1).coeffs
    if len(dp) == 2:
        return [-dp[1] / dp[0]]
    if len(dp) == 3:
        a, b, c = dp
        disc = b * b - 4 * a * c
        if disc < 0:
            return []
        sq = np.sqrt(disc)
        # công thức ổn định số học (tránh triệt tiêu)
        q = -0.5 * (b + np.copysign(sq, b))
        r1, r2 = q / a, (c / q if q != 0 else q / a)
        return sorted({float(r1), float(r2)})
    return list(np.roots(dp).real)


def run_validation():
    print("=" * 60 + "\nBƯỚC 4: KIỂM CHỨNG\n" + "=" * 60)
    cases = [
        ("p(s) = -(s-0.3)^2 + 10 trên [-2,2]", np.poly1d([-1.0, 0.6, 9.91]), -2.0, 2.0,
         [(0.3, "Cực đại", 10.0)]),
        ("p(s) = s^3 - 3s trên [-2,2]", np.poly1d([1.0, 0.0, -3.0, 0.0]), -2.0, 2.0,
         [(-1.0, "Cực đại", 2.0), (1.0, "Cực tiểu", -2.0)]),
    ]
    out_rows = []
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (name, p, lo, hi, exact) in zip(axes, cases):
        starts, ext, _ = analyze_poly(p, lo, hi)
        print(f"\n--- {name} ---")
        print(starts.to_string(index=False))
        print(ext.to_string(index=False))
        interior = ext[~ext["loai"].isin(["Biên trái", "Biên phải"])]
        for (r_true, kind_true, v_true) in exact:
            j = (interior["s"] - r_true).abs().idxmin() if len(interior) else None
            if j is None:
                out_rows.append({"ham": name, "nghiem_that": r_true, "nghiem_newton": np.nan})
                continue
            r_num = interior.loc[j, "s"]
            out_rows.append({
                "ham": name, "nghiem_that": r_true, "nghiem_newton": r_num,
                "sai_so_nghiem": abs(r_num - r_true),
                "residual |p'|": abs(np.polyder(p, 1)(r_num)),
                "loai_that": kind_true, "loai_tim_duoc": interior.loc[j, "loai"],
                "p_that": v_true, "p_newton": interior.loc[j, "p(s)"],
            })
        kinds = interior["loai"].tolist()
        print("Phân loại các nghiệm p'=0:", kinds)
        xs = np.linspace(lo, hi, 400)
        ax.plot(xs, p(xs), "b-", label="p(s)")
        for _, r in ext.iterrows():
            mk = {"Cực đại": "^", "Cực tiểu": "v"}.get(r["loai"].split(" (")[0], "s")
            ax.plot(r["s"], r["p(s)"], mk, color="red" if "MAX" in r["toan_doan"] else "k", ms=8)
        ax.set_title(name, fontsize=9)
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "validation.png", dpi=130)
    plt.close(fig)
    val = pd.DataFrame(out_rows)
    print("\nBẢNG KIỂM CHỨNG:\n", val.to_string(index=False))
    val.to_csv(OUT / "validation_summary.csv", index=False, encoding="utf-8-sig")
    return val


def fit_poly(win: pd.DataFrame, degree: int) -> np.poly1d:
    return np.poly1d(np.polyfit(win["s"].to_numpy(np.float64), win["total_count"].to_numpy(np.float64), degree))


def analyze_segment(name: str, seg: pd.DataFrame):
    print("\n" + "=" * 60 + f"\nPHÂN TÍCH ĐOẠN {name}\n" + "=" * 60)
    p3, p2 = fit_poly(seg, 3), fit_poly(seg, 2)
    print("Hệ số bậc 3 (s^3..1):", p3.coeffs)
    print("Hệ số bậc 2 (đối chứng):", p2.coeffs)
    print("p'(s)  =", np.polyder(p3, 1).coeffs, "| p''(s) =", np.polyder(p3, 2).coeffs)

    starts, ext, info = analyze_poly(p3, -1.0, 1.0)
    print("\nBảng điểm đầu Newton:\n", starts.to_string(index=False))
    if not info["has_interior"]:
        print("\n>>> KHÔNG có điểm dừng (p'=0) trong miền [-1,1]: xu thế đơn điệu/phẳng, chỉ có cực trị ở biên.")
    t_max = seg["t_min"].iloc[-1]
    start_dt = seg["dt"].iloc[0]
    ext["t_phut"] = [s_to_t(s, 0.0, t_max) for s in ext["s"]]
    ext["timestamp"] = [s_to_timestamp(s, 0.0, t_max, start_dt) for s in ext["s"]]
    print("\nBảng cực trị (gồm biên) bậc 3:\n", ext.to_string(index=False))

    cf = [r for r in closed_form_stationary(p3) if -1 <= r <= 1]
    newton_in = ext[~ext["loai"].isin(["Biên trái", "Biên phải"])]["s"].tolist()
    print("\nNghiệm công thức (trong miền):", cf, "| Newton:", newton_in)
    if cf and len(cf) == len(newton_in):
        print("Sai khác lớn nhất Newton - công thức:", max(abs(a - b) for a, b in zip(sorted(cf), sorted(newton_in))))
    elif cf or newton_in:
        print("CẢNH BÁO: số nghiệm trong miền của Newton và công thức khác nhau -> kiểm tra điểm đầu!")

    starts2, ext2, info2 = analyze_poly(p2, -1.0, 1.0)
    print("\nĐối chứng bậc 2 - điểm dừng trong miền:")
    if info2["has_interior"]:
        print(ext2[~ext2["loai"].isin(["Biên trái", "Biên phải"])].to_string(index=False))
    else:
        print("(không có điểm dừng trong [-1,1]: xu thế đơn điệu/phẳng, chỉ có cực trị ở biên)")

    ext.insert(0, "doan", name)
    starts.insert(0, "doan", name)
    return p3, p2, ext, starts


def sensitivity(name: str, seg: pd.DataFrame) -> pd.DataFrame:
    """Bước 5: so cực trị mô hình với cực trị đếm quan sát; đổi cỡ cửa sổ và bậc."""
    rows = []
    for w in WINDOWS:
        if w > len(seg):
            continue
        win = extract_window(seg, w)
        t_max, start_dt = win["t_min"].iloc[-1], win["dt"].iloc[0]
        i_max, i_min = win["total_count"].idxmax(), win["total_count"].idxmin()
        for deg in DEGREES:
            p = fit_poly(win, deg)
            _, ext, _ = analyze_poly(p, -1.0, 1.0)
            for tag, i_obs, key in (("MAX", i_max, "MAX"), ("MIN", i_min, "MIN")):
                hit = ext[ext["toan_doan"].str.contains(key)]
                if hit.empty:
                    continue
                r = hit.iloc[0]
                t_model = s_to_t(r["s"], 0.0, t_max)
                rows.append({
                    "doan": name, "cua_so": w, "bac": deg, "loai": tag,
                    "s_mo_hinh": r["s"], "vi_tri": r["loai"],
                    "t_mo_hinh_phut": t_model,
                    "timestamp_mo_hinh": s_to_timestamp(r["s"], 0.0, t_max, start_dt),
                    "p_mo_hinh": r["p(s)"],
                    "t_quan_sat_phut": win.loc[i_obs, "t_min"],
                    "timestamp_quan_sat": win.loc[i_obs, "dt"].tz_convert("Asia/Ho_Chi_Minh").isoformat(),
                    "y_quan_sat": win.loc[i_obs, "total_count"],
                    "lech_thoi_gian_phut": abs(t_model - win.loc[i_obs, "t_min"]),
                    "lech_gia_tri": abs(r["p(s)"] - win.loc[i_obs, "total_count"]),
                })
    return pd.DataFrame(rows)


def plot_segment(name, seg, p3, p2, ext):
    t_max = seg["t_min"].iloc[-1]
    ss = np.linspace(-1, 1, 400)
    tt = s_to_t(ss, 0.0, t_max)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.scatter(seg["t_min"], seg["total_count"], s=14, c="gray", alpha=0.7, label="total_count (quan sát)")
    ax.plot(tt, p3(ss), "b-", lw=2, label="Xu thế bậc 3")
    ax.plot(tt, p2(ss), "g--", lw=1.5, label="Bậc 2 (đối chứng)")
    for _, r in ext.iterrows():
        t = s_to_t(r["s"], 0.0, t_max)
        if r["loai"] in ("Biên trái", "Biên phải"):
            ax.plot(t, r["p(s)"], "ks", ms=7, label="Biên" if r["loai"] == "Biên trái" else None)
        else:
            col = "red" if r["loai"].startswith("Cực đại") else "orange"
            ax.plot(t, r["p(s)"], "o", color=col, ms=9, label=r["loai"].split(" (")[0] + f" (s={r['s']:.3f})")
    ax.set_xlabel("Thời gian từ mốc đầu (phút)")
    ax.set_ylabel("total_count")
    ax.set_title(f"Đoạn {name}: đường xu thế và các điểm dừng")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT / f"trend_{name}.png", dpi=130)
    plt.close(fig)


def main():
    snapshot = pd.read_csv(SNAPSHOT, dtype={"image_id": str})
    missing = [c for c in REQUIRED_COLS if c not in snapshot.columns]
    if missing:
        raise ValueError(f"analysis_snapshot.csv thiếu cột: {missing}")
    seg_a = prepare_segment(snapshot[snapshot["recording_id"] == REC_A])
    seg_b = prepare_segment(snapshot[snapshot["recording_id"] == REC_B])

    check_data(seg_a, seg_b, snapshot)
    run_validation()

    all_ext, all_starts, all_sens = [], [], []
    for name, seg in (("A", seg_a), ("B", seg_b)):
        p3, p2, ext, starts = analyze_segment(name, seg)
        plot_segment(name, seg, p3, p2, ext)
        all_ext.append(ext)
        all_starts.append(starts)
        all_sens.append(sensitivity(name, seg))

    sens = pd.concat(all_sens, ignore_index=True)
    print("\n" + "=" * 60 + "\nBƯỚC 5: ĐỘ NHẠY THEO CỬA SỔ VÀ BẬC\n" + "=" * 60)
    print(sens.drop(columns=["timestamp_mo_hinh", "timestamp_quan_sat"]).to_string(index=False))

    pd.concat(all_starts).to_csv(OUT / "newton_starts.csv", index=False, encoding="utf-8-sig")
    pd.concat(all_ext).to_csv(OUT / "extrema_table.csv", index=False, encoding="utf-8-sig")
    sens.to_csv(OUT / "sensitivity.csv", index=False, encoding="utf-8-sig")
    print(f"\nĐã lưu kết quả và biểu đồ tại: {OUT}")


if __name__ == "__main__":
    main()
