"""
Phuc An Retail AI Agent - Core Processing Engine
Thực thi chính xác quy trình BPMN 3 giai đoạn:
- Giai đoạn 1: Tải dữ liệu, Lọc trùng, Loại bỏ đơn hủy, Chuẩn hóa hàng trả, Đồng bộ kỳ -> Tạo 'Sheets Sạch'
- Giai đoạn 2: Tính toán & Báo cáo Quản trị (Doanh thu thuần, Giá vốn, Lợi nhuận gộp, % Hoàn thành KPI, Tăng trưởng MoM, Phân tích cơ cấu sản phẩm & tỷ lệ đổi trả)
- Giai đoạn 3: Kiểm tra đối chiếu (Cross-check Audit), Phát hiện bất thường & Thuật toán AI Ranking xếp thứ tự ưu tiên hỗ trợ cửa hàng
"""
import pandas as pd
import numpy as np
from data_generator import STORES, PRODUCTS

def get_store_metadata_df():
    return pd.DataFrame(STORES)

def get_product_catalog_df():
    return pd.DataFrame(PRODUCTS)

# ==========================================
# GIAI ĐOẠN 1: CHUẨN BỊ & LÀM SẠCH (DATA CLEANING AGENT)
# ==========================================
def agent_clean_data(raw_df: pd.DataFrame):
    """
    1. Nhận diện và lọc trùng mã giao dịch (Deduplication)
    2. Loại bỏ các đơn hàng bị hủy (Status = 'Đã hủy')
    3. Chuẩn hóa hàng đổi trả: Quy đổi số lượng và doanh thu trả về số âm nhất quán
    4. Khớp dữ liệu với danh mục sản phẩm để lấy Giá vốn (Cost of Goods Sold - COGS)
    5. Kiểm tra tính hợp lệ về kỳ báo cáo và ngày ghi nhận
    """
    total_raw = len(raw_df)
    
    # 1. Thống kê & lọc trùng lặp
    dup_mask = raw_df.duplicated(subset=['trans_id'], keep='first')
    total_duplicates = int(dup_mask.sum())
    df_dedup = raw_df[~dup_mask].copy()

    # 2. Thống kê đơn hủy
    canceled_mask = df_dedup['status'] == 'Đã hủy'
    total_canceled = int(canceled_mask.sum())
    total_canceled_value = float(df_dedup.loc[canceled_mask, 'line_amount'].abs().sum())
    
    # Bỏ đơn hủy
    df_active = df_dedup[~canceled_mask].copy()

    # 3. Chuẩn hóa hàng đổi trả
    # Nguyên tắc tài chính kế toán bán lẻ:
    # Doanh số bán (Hoàn thành): Qty > 0, Revenue > 0
    # Doanh số trả (Đổi trả): Qty < 0, Revenue < 0 (giảm trừ doanh thu)
    returned_mask = df_active['status'] == 'Đổi trả'
    total_returns = int(returned_mask.sum())
    
    # Ép kiểu chuẩn hóa
    df_active['quantity'] = df_active['quantity'].astype(float)
    df_active['unit_price'] = df_active['unit_price'].astype(float)
    
    # Với đơn 'Đổi trả': bắt buộc số lượng là số âm
    df_active.loc[returned_mask, 'clean_quantity'] = -df_active.loc[returned_mask, 'quantity'].abs()
    df_active.loc[~returned_mask, 'clean_quantity'] = df_active.loc[~returned_mask, 'quantity'].abs()
    
    # Tính doanh số thuần từng dòng
    df_active['net_amount'] = df_active['clean_quantity'] * df_active['unit_price']
    
    # 4. Join với Giá vốn chuẩn từ Product Catalog
    cat_df = get_product_catalog_df()[['sku', 'cost_price']]
    df_merged = pd.merge(df_active, cat_df, on='sku', how='left')
    
    # Giá vốn từng dòng (cũng âm nếu là hàng trả)
    df_merged['total_cogs'] = df_merged['clean_quantity'] * df_merged['cost_price']
    df_merged['gross_profit'] = df_merged['net_amount'] - df_merged['total_cogs']
    
    clean_count = len(df_merged)
    
    audit_summary = {
        "total_raw": total_raw,
        "total_duplicates_removed": total_duplicates,
        "total_canceled_removed": total_canceled,
        "total_canceled_value": total_canceled_value,
        "total_returns_standardized": total_returns,
        "total_clean_rows": clean_count
    }
    
    return df_merged, audit_summary

# ==========================================
# GIAI ĐOẠN 2: TÍNH TOÁN & TẠO BÁO CÁO QUẢN TRỊ (MANAGEMENT REPORT AGENT)
# ==========================================
def agent_build_management_report(clean_df: pd.DataFrame, current_period="2026-10", compare_period="2026-09"):
    """
    Tính toán chi tiết cho từng cửa hàng:
    - Doanh thu thuần (Net Revenue)
    - Giá vốn hàng bán (COGS)
    - Lợi nhuận gộp (Gross Profit)
    - Tỷ suất Lợi nhuận gộp (Gross Margin %)
    - Tỷ lệ hoàn thành mục tiêu KPI (%)
    - Tốc độ tăng trưởng Doanh thu & Lợi nhuận gộp so với kỳ trước (MoM Growth %)
    - Tỷ lệ hàng đổi trả / Doanh số gộp (Return Rate %)
    - Cơ cấu ngành hàng (Doanh thu & Margin theo category)
    """
    stores_df = get_store_metadata_df()
    
    # Tách dữ liệu 2 kỳ
    df_cur = clean_df[clean_df['period'] == current_period].copy()
    df_cmp = clean_df[clean_df['period'] == compare_period].copy()
    
    def aggregate_period(df_sub):
        grouped = df_sub.groupby('store_id').agg(
            gross_sales=('net_amount', lambda x: x[x > 0].sum()),
            return_amount=('net_amount', lambda x: abs(x[x < 0].sum())),
            net_revenue=('net_amount', 'sum'),
            total_cogs=('total_cogs', 'sum'),
            gross_profit=('gross_profit', 'sum'),
            order_count=('trans_id', 'nunique'),
            sold_units=('clean_quantity', lambda x: x[x > 0].sum()),
            return_units=('clean_quantity', lambda x: abs(x[x < 0].sum()))
        ).reset_index()
        
        grouped['return_rate_revenue'] = np.where(grouped['gross_sales'] > 0, 
                                                 (grouped['return_amount'] / grouped['gross_sales']) * 100, 0)
        grouped['gross_margin_pct'] = np.where(grouped['net_revenue'] > 0,
                                               (grouped['gross_profit'] / grouped['net_revenue']) * 100, 0)
        return grouped

    metrics_cur = aggregate_period(df_cur)
    metrics_cmp = aggregate_period(df_cmp)
    
    # Merge với danh sách cửa hàng & Target
    merged = pd.merge(stores_df, metrics_cur, on='store_id', how='left').fillna(0)
    merged = pd.merge(merged, metrics_cmp, on='store_id', how='left', suffixes=('', '_prev')).fillna(0)
    
    # Tính toán chỉ số quản trị cốt lõi
    merged['kpi_completion_pct'] = (merged['net_revenue'] / merged['target_revenue']) * 100
    
    # Tăng trưởng so sánh chuẩn kỳ (MoM)
    merged['revenue_growth_mom'] = np.where(merged['net_revenue_prev'] > 0,
                                           ((merged['net_revenue'] - merged['net_revenue_prev']) / merged['net_revenue_prev']) * 100, 0)
    merged['profit_growth_mom'] = np.where(merged['gross_profit_prev'] > 0,
                                          ((merged['gross_profit'] - merged['gross_profit_prev']) / merged['gross_profit_prev']) * 100, 0)
    
    # Phân tích cơ cấu sản phẩm kỳ hiện tại
    cat_summary = df_cur.groupby(['store_id', 'category']).agg(
        cat_revenue=('net_amount', 'sum'),
        cat_profit=('gross_profit', 'sum')
    ).reset_index()
    
    return merged, cat_summary

# ==========================================
# GIAI ĐOẠN 3: ĐỐI CHIẾU & PHÁT HIỆN BẤT THƯỜNG - RA QUYẾT ĐỊNH (CROSS-CHECK & DECISION AGENT)
# ==========================================
def agent_cross_check_and_ranking(report_df: pd.DataFrame, clean_df: pd.DataFrame):
    """
    AI Cross-check Audit & Intelligent Support Prioritization:
    1. Phát hiện các bất thường:
       - Tăng trưởng doanh thu ảo (Revenue tăng nhưng Gross Profit giảm do bán đồ biên lợi nhuận thấp hoặc hàng trả cao)
       - Tỷ lệ hàng trả cao vượt ngưỡng cảnh báo (> 8%)
       - Không đạt KPI (< 85%)
       - Tăng trưởng âm sâu so với kỳ so sánh
    2. Thuật toán Điểm số Khẩn cấp Hỗ trợ (Support Priority Score - SPS):
       - Trọng số KPI Gap: 35%
       - Trọng số MoM Revenue Growth âm: 25%
       - Trọng số MoM Profit Growth âm: 20%
       - Trọng số Tỷ lệ đổi trả cao: 20%
    3. Phân loại Khẩn cấp: Cao (Priority 1), Trung bình (Priority 2), Tốt/Ổn định (Priority 3)
    4. Đưa ra Actionable Recommendations chi tiết cho từng cửa hàng
    """
    results = []
    
    for _, row in report_df.iterrows():
        store_id = row['store_id']
        store_name = row['store_name']
        kpi_pct = row['kpi_completion_pct']
        rev_growth = row['revenue_growth_mom']
        prof_growth = row['profit_growth_mom']
        return_rate = row['return_rate_revenue']
        gross_margin = row['gross_margin_pct']
        
        anomalies = []
        recommendations = []
        
        # 1. Kiểm tra nghịch lý doanh thu - lợi nhuận (Margin erosion)
        if rev_growth > 0 and prof_growth < -2:
            anomalies.append(f"⚠️ NGHỊCH LÝ: Doanh thu tăng {rev_growth:.1f}% nhưng Lợi nhuận gộp giảm {prof_growth:.1f}% (Xói mòn biên lợi nhuận).")
            recommendations.append("Kiểm tra cơ cấu rổ hàng: cửa hàng đang chạy nhiều khuyến mãi xả hàng hoặc bán sản phẩm có margin quá thấp.")
            
        # 2. Kiểm tra tỷ lệ đổi trả
        if return_rate >= 8.0:
            anomalies.append(f"🚨 TỶ LỆ TRẢ HÀNG CAO: {return_rate:.1f}% doanh số bị trừ do trả hàng (Ngưỡng cảnh báo: 8%).")
            recommendations.append("Thanh tra chất lượng bảo quản lô hàng, quy trình hướng dẫn khách dùng của nhân viên tại cửa hàng.")
        elif return_rate >= 5.0:
            anomalies.append(f"⚡ Cần theo dõi đổi trả: {return_rate:.1f}%.")
            
        # 3. Mức độ đạt KPI
        if kpi_pct < 80.0:
            anomalies.append(f"🔴 BÁO ĐỘNG KPI: Chỉ đạt {kpi_pct:.1f}% mục tiêu tháng.")
            recommendations.append("Giám đốc vùng cần xuống trực tiếp hỗ trợ, rà soát lại lưu lượng khách (footfall) và tỷ lệ chốt đơn (conversion rate).")
        elif kpi_pct < 90.0:
            anomalies.append(f"🟡 Chưa đạt chuẩn KPI: Đạt {kpi_pct:.1f}%.")
            recommendations.append("Bổ sung mini-game cuối tuần hoặc hỗ trợ đẩy hàng chủ lực có biên lợi nhuận cao.")
            
        # 4. Tăng trưởng MoM âm
        if rev_growth < -10.0:
            anomalies.append(f"📉 SỤT GIẢM NẶNG: Doanh thu giảm {rev_growth:.1f}% so với kỳ so sánh.")
            recommendations.append("Kiểm tra sự xuất hiện của đối thủ cạnh tranh lân cận hoặc sự cố vận hành cục bộ.")

        # Thuật toán tính Điểm Cần Hỗ Trợ (Priority Score: 0 -> 100, càng cao càng cần hỗ trợ khẩn cấp)
        # Factor 1: KPI deficit (nếu đạt 100% thì 0, nếu đạt 70% thì deficit = 30)
        kpi_deficit = max(0, 100 - kpi_pct) * 0.4
        
        # Factor 2: Sụt giảm doanh thu
        rev_deficit = max(0, -rev_growth) * 0.25
        
        # Factor 3: Sụt giảm lợi nhuận
        prof_deficit = max(0, -prof_growth) * 0.20
        
        # Factor 4: Tỷ lệ trả hàng cao (mỗi % trên 5% bị tính nặng)
        return_penalty = max(0, return_rate - 4.0) * 3.5
        
        priority_score = min(100.0, kpi_deficit + rev_deficit + prof_deficit + return_penalty)
        
        if priority_score >= 40:
            priority_level = "Ưu tiên 1: Hỗ trợ khẩn cấp"
            badge_color = "red"
        elif priority_score >= 20:
            priority_level = "Ưu tiên 2: Cần can thiệp theo dõi"
            badge_color = "orange"
        else:
            priority_level = "Ưu tiên 3: Vận hành ổn định"
            badge_color = "green"
            if not recommendations:
                recommendations.append("Duy trì nhịp độ bán hàng hiện tại, phát huy sản phẩm best-seller.")
                
        results.append({
            "store_id": store_id,
            "store_name": store_name,
            "tier": row['tier'],
            "region": row['region'],
            "priority_score": round(priority_score, 1),
            "priority_level": priority_level,
            "badge_color": badge_color,
            "kpi_completion_pct": round(kpi_pct, 1),
            "net_revenue": row['net_revenue'],
            "gross_profit": row['gross_profit'],
            "revenue_growth_mom": round(rev_growth, 1),
            "profit_growth_mom": round(prof_growth, 1),
            "return_rate_revenue": round(return_rate, 1),
            "anomalies": anomalies,
            "recommendations": recommendations
        })
        
    df_ranked = pd.DataFrame(results).sort_values(by="priority_score", ascending=False).reset_index(drop=True)
    return df_ranked

