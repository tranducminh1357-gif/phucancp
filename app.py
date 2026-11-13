import streamlit as st
import pandas as pd
import numpy as np
import datetime
import io
from data_generator import generate_sample_raw_data, STORES, PRODUCTS
from agent_core import agent_clean_data, agent_build_management_report, agent_cross_check_and_ranking, get_store_metadata_df, get_product_catalog_df

# Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống AI Agent - Phúc An Retail",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #4B5563;
        margin-bottom: 16px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .badge-p1 {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    .badge-p2 {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    .badge-p3 {
        background-color: #DCFCE7;
        color: #166534;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    .bpmn-step {
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Session State
if "raw_data" not in st.session_state:
    try:
        st.session_state.raw_data = pd.read_parquet("phucan_raw_data.parquet")
    except Exception:
        st.session_state.raw_data = generate_sample_raw_data()
        st.session_state.raw_data.to_parquet("phucan_raw_data.parquet", index=False)

if "clean_data" not in st.session_state:
    st.session_state.clean_data = None
    st.session_state.audit_summary = None

if "human_approved" not in st.session_state:
    st.session_state.human_approved = False

if "report_data" not in st.session_state:
    st.session_state.report_data = None
    st.session_state.cat_summary = None

if "ranking_data" not in st.session_state:
    st.session_state.ranking_data = None

# Sidebar - Điều khiển Quy trình BPMN
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shop.png", width=60)
    st.markdown("### **PHÚC AN RETAIL**")
    st.markdown("**Hệ thống Điều hành 18 Cửa Hàng**")
    st.write("---")
    
    st.markdown("#### ⚙️ Cài đặt Kỳ Báo Cáo")
    period_cur = st.selectbox("Kỳ Báo Cáo (Hiện tại):", ["2026-10 (Tháng 10/2026)"], index=0)
    period_cmp = st.selectbox("Kỳ So Sánh (Chuẩn đối sánh):", ["2026-09 (Tháng 09/2026)"], index=0)
    
    st.write("---")
    st.markdown("#### 🔄 Nguồn Dữ Liệu Thô")
    st.info(f"Tổng số bản ghi thô nạp sẵn: **{len(st.session_state.raw_data):,} dòng** (gồm 18 cửa hàng)")
    
    if st.button("🎲 Tái tạo dữ liệu thô mới"):
        with st.spinner("Đang tạo 60.000 dòng dữ liệu mới..."):
            st.session_state.raw_data = generate_sample_raw_data()
            st.session_state.raw_data.to_parquet("phucan_raw_data.parquet", index=False)
            st.session_state.clean_data = None
            st.session_state.human_approved = False
            st.session_state.report_data = None
            st.session_state.ranking_data = None
            st.rerun()

    st.write("---")
    st.markdown("#### 📌 Tiến độ Quy trình BPMN:")
    p1_done = "✅" if st.session_state.clean_data is not None else "⚪"
    p2_done = "✅" if st.session_state.human_approved else "⚪"
    p3_done = "✅" if st.session_state.report_data is not None else "⚪"
    p4_done = "✅" if st.session_state.ranking_data is not None else "⚪"
    
    st.markdown(f"{p1_done} **GĐ 1A:** Agent làm sạch & lọc lỗi")
    st.markdown(f"{p2_done} **GĐ 1B:** Con người kiểm tra (Human Verification)")
    st.markdown(f"{p3_done} **GĐ 2:** Agent lập Báo cáo Quản trị")
    st.markdown(f"{p4_done} **GĐ 3:** AI Cross-check & Xếp hạng ưu tiên")

# MAIN CONTENT TABS THEO 3 GIAI ĐOẠN BPMN
st.markdown('<div class="main-header">🏪 AI Agent Quản Trị & Đối Soát Bán Lẻ - Phúc An Retail</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Tự động hóa toàn diện quy trình 3 giai đoạn: Làm sạch dữ liệu thô -> Lập Báo cáo Quản trị -> Kiểm tra đối chiếu & Gợi ý quyết định hỗ trợ cửa hàng</div>', unsafe_allow_html=True)

tabs = st.tabs([
    "📍 Sơ đồ Quy trình BPMN",
    "🧹 Giai đoạn 1: Chuẩn bị & Làm sạch",
    "📊 Giai đoạn 2: Báo cáo Quản trị",
    "🎯 Giai đoạn 3: Đối chiếu & Ra quyết định",
    "🏬 Xem chi tiết Cửa hàng"
])

# TAB 0: Sơ đồ BPMN
with tabs[0]:
    st.markdown("### 📋 Kiến trúc Quy trình Vận hành Chuẩn Phúc An Retail")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div style="background-color:#EBF8FF; border:1px solid #BEE3F8; border-radius:8px; padding:15px;">
            <h4 style="color:#2B6CB0; margin-top:0;">GIAI ĐOẠN 1: CHUẨN BỊ & LÀM SẠCH</h4>
            <b>1. Con người:</b> Nạp dữ liệu thô (60.000 dòng gồm đơn, giá vốn, KPI).<br>
            <b>2. AI Agent:</b> Lọc trùng giao dịch, bỏ đơn hủy, quy chuẩn doanh thu hoàn trả, đồng bộ kỳ.<br>
            <b>3. Con người (Human Verification):</b> Kiểm tra và phê duyệt Sheets sạch trước khi sang GĐ 2.
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:15px;">
            <h4 style="color:#15803D; margin-top:0;">GIAI ĐOẠN 2: BÁO CÁO QUẢN TRỊ</h4>
            <b>1. AI Agent:</b> Tự động tính toán các chỉ số kinh doanh:<br>
            • Doanh thu thuần (đã trừ trả hàng chuẩn xác)<br>
            • Giá vốn hàng bán (COGS) & Lợi nhuận gộp<br>
            • Tỷ lệ đạt KPI mục tiêu tháng<br>
            • So sánh chuẩn xác 2 kỳ (MoM Growth)<br>
            • Phân tích cơ cấu sản phẩm & tỷ lệ trả hàng.
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style="background-color:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:15px;">
            <h4 style="color:#B91C1C; margin-top:0;">GIAI ĐOẠN 3: ĐỐI CHIẾU & QUYẾT ĐỊNH</h4>
            <b>1. Cross-check Audit:</b> AI đối chiếu tự động, tìm nghịch lý tăng trưởng ảo, trả hàng cao.<br>
            <b>2. Thuật toán Xếp hạng Ưu tiên:</b> Xác định Top cửa hàng cần hỗ trợ khẩn cấp nhất.<br>
            <b>3. Giám đốc Kinh doanh:</b> Đánh giá báo cáo và ra quyết định can thiệp kịp thời.
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("#### 📂 Dữ liệu đầu vào hiện tại (Raw Data Preview - Mẫu 10 dòng thô):")
    st.dataframe(st.session_state.raw_data.head(10), use_container_width=True)

# TAB 1: Giai đoạn 1 - Làm sạch dữ liệu
with tabs[1]:
    st.markdown("### 🧹 GIAI ĐOẠN 1: Chuẩn bị & Làm sạch Dữ liệu (AI Cleaning Agent)")
    st.info("Nhân viên nghiệp vụ trước đây ghép bằng tay dễ bị: Trùng đơn, cộng cả đơn hủy, tính hàng trả sai âm/dương, so sánh lệch kỳ.")
    
    col_act1, col_act2 = st.columns([1, 2])
    with col_act1:
        st.markdown("#### Bắt đầu quy trình làm sạch:")
        if st.button("🚀 Chạy AI Agent: Lọc & Làm Sạch Dữ Liệu", type="primary", use_container_width=True):
            with st.spinner("AI Agent đang quét 60.000 dòng, đối soát trùng lặp, chuẩn hóa đơn hủy & đổi trả..."):
                clean_df, audit = agent_clean_data(st.session_state.raw_data)
                st.session_state.clean_data = clean_df
                st.session_state.audit_summary = audit
                st.session_state.human_approved = False
                st.success("AI Agent đã xử lý xong!")
    
    if st.session_state.clean_data is not None:
        audit = st.session_state.audit_summary
        st.write("---")
        st.markdown("#### 📊 Kết Quả Báo Cáo Đối Soát Dữ Liệu Thô (Data Cleaning Audit Log)")
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Tổng dòng thô ban đầu", f"{audit['total_raw']:,}")
        m2.metric("Số giao dịch trùng bị loại", f"{audit['total_duplicates_removed']:,}", delta=f"-{audit['total_duplicates_removed']}", delta_color="inverse")
        m3.metric("Số đơn hủy đã loại bỏ", f"{audit['total_canceled_removed']:,}", delta=f"-{audit['total_canceled_removed']}", delta_color="inverse")
        m4.metric("Doanh thu đơn hủy loại bỏ", f"{audit['total_canceled_value']/1e9:.2f} Tỷ VNĐ")
        m5.metric("Số đơn đổi trả đã chuẩn hóa", f"{audit['total_returns_standardized']:,}")

        st.markdown(f"**🎯 Tổng số dòng dữ liệu SẠCH đạt chuẩn:** <span style='font-size:20px; font-weight:bold; color:#15803D;'>{audit['total_clean_rows']:,} dòng</span>", unsafe_allow_html=True)
        
        st.write("---")
        st.markdown("#### 📑 Xem mẫu 'Sheets Dữ Liệu Đã Làm Sạch' (Cleaned Sheets Preview):")
        st.dataframe(
            st.session_state.clean_data[['trans_id', 'trans_date', 'period', 'store_id', 'store_name', 'product_name', 'clean_quantity', 'unit_price', 'net_amount', 'cost_price', 'gross_profit', 'status']].head(15),
            use_container_width=True
        )

        st.write("---")
        st.markdown("### 👤 Bước Kiểm Duyệt Của Con Người (Human Verification - Gatekeeper)")
        st.markdown("Theo quy trình BPMN: *'Con người kiểm tra lại (Human Verification) -> Dữ liệu OK? -> Đáp Sheets dữ liệu sạch cho Agent'*. Sau khi xác nhận, Agent mới được phép tính toán Giai đoạn 2.")
        
        hv_col1, hv_col2 = st.columns([2, 1])
        with hv_col1:
            check_ok = st.checkbox("✅ Tôi (Chuyên viên Báo cáo/Kinh doanh) đã rà soát: Các đơn trùng, đơn hủy và giá vốn đã được đối soát chuẩn xác.", value=st.session_state.human_approved)
        with hv_col2:
            if st.button("📤 Phê Duyệt & Chuyển Dữ Liệu Sang GĐ 2", type="secondary", disabled=not check_ok, use_container_width=True):
                st.session_state.human_approved = True
                # Tự động chạy luôn Giai đoạn 2
                with st.spinner("Đang chuyển dữ liệu sạch cho Agent tạo Báo cáo Quản trị..."):
                    rep_df, cat_df = agent_build_management_report(st.session_state.clean_data, "2026-10", "2026-09")
                    st.session_state.report_data = rep_df
                    st.session_state.cat_summary = cat_df
                    # Chạy luôn Giai đoạn 3
                    st.session_state.ranking_data = agent_cross_check_and_ranking(rep_df, st.session_state.clean_data)
                st.success("Đã phê duyệt và tạo báo cáo thành công! Mời bạn mở Tab Giai đoạn 2 và 3.")
                st.rerun()

# TAB 2: Giai đoạn 2 - Báo cáo Quản trị
with tabs[2]:
    st.markdown("### 📊 GIAI ĐOẠN 2: Báo cáo Quản trị Tự Động (Management Dashboard)")
    if not st.session_state.human_approved or st.session_state.report_data is None:
        st.warning("⚠️ Vui lòng hoàn thành **Giai đoạn 1: Làm sạch & Phê duyệt dữ liệu (Human Verification)** trước khi xem Báo cáo Quản trị!")
    else:
        rep_df = st.session_state.report_data
        
        # Tổng quan toàn chuỗi 18 cửa hàng
        total_rev = rep_df['net_revenue'].sum()
        total_profit = rep_df['gross_profit'].sum()
        total_target = rep_df['target_revenue'].sum()
        overall_kpi = (total_rev / total_target) * 100
        overall_margin = (total_profit / total_rev) * 100
        
        # MoM Growth toàn hệ thống
        total_rev_prev = rep_df['net_revenue_prev'].sum()
        overall_mom = ((total_rev - total_rev_prev) / total_rev_prev) * 100 if total_rev_prev > 0 else 0
        
        st.markdown("#### 📈 Tổng Quan Toàn Hệ Thống Phúc An Retail (Tháng 10/2026)")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Doanh thu thuần", f"{total_rev/1e9:.2f} Tỷ VNĐ", f"{overall_mom:+.1f}% MoM")
        kpi2.metric("Lợi nhuận gộp", f"{total_profit/1e9:.2f} Tỷ VNĐ")
        kpi3.metric("Tỷ suất LN gộp", f"{overall_margin:.1f}%")
        kpi4.metric("Mục tiêu Doanh thu", f"{total_target/1e9:.2f} Tỷ VNĐ")
        kpi5.metric("Mức độ hoàn thành KPI", f"{overall_kpi:.1f}%", f"{overall_kpi-100:+.1f}% so KPI")

        st.write("---")
        st.markdown("#### 📋 Bảng Báo Cáo Chi Tiết 18 Cửa Hàng (Đã So Sánh Chuẩn Kỳ)")
        
        # Chuẩn bị bảng hiển thị đẹp
        display_rep = rep_df[[
            'store_id', 'store_name', 'region', 'tier',
            'net_revenue', 'target_revenue', 'kpi_completion_pct',
            'gross_profit', 'gross_margin_pct',
            'revenue_growth_mom', 'profit_growth_mom',
            'return_rate_revenue'
        ]].copy()
        
        display_rep['Doanh thu thuần (Tr.đ)'] = (display_rep['net_revenue'] / 1e6).round(1)
        display_rep['Mục tiêu (Tr.đ)'] = (display_rep['target_revenue'] / 1e6).round(1)
        display_rep['LN gộp (Tr.đ)'] = (display_rep['gross_profit'] / 1e6).round(1)
        display_rep['% Đạt KPI'] = display_rep['kpi_completion_pct'].round(1)
        display_rep['Biên LN %'] = display_rep['gross_margin_pct'].round(1)
        display_rep['Tăng trưởng DThu MoM %'] = display_rep['revenue_growth_mom'].round(1)
        display_rep['Tăng trưởng LN MoM %'] = display_rep['profit_growth_mom'].round(1)
        display_rep['Tỷ lệ đổi trả %'] = display_rep['return_rate_revenue'].round(1)
        
        st.dataframe(
            display_rep[['store_id', 'store_name', 'region', 'tier', 'Doanh thu thuần (Tr.đ)', 'Mục tiêu (Tr.đ)', '% Đạt KPI', 'LN gộp (Tr.đ)', 'Biên LN %', 'Tăng trưởng DThu MoM %', 'Tăng trưởng LN MoM %', 'Tỷ lệ đổi trả %']],
            use_container_width=True
        )

        st.write("---")
        st.markdown("#### 📊 Biểu đồ So Sánh Doanh Thu Thuần vs Mục Tiêu KPI")
        chart_df = rep_df[['store_id', 'net_revenue', 'target_revenue']].copy()
        chart_df = chart_df.set_index('store_id')
        chart_df.columns = ['Doanh thu thuần thực tế (VNĐ)', 'Mục tiêu KPI (VNĐ)']
        st.bar_chart(chart_df)

# TAB 3: Giai đoạn 3 - Đối chiếu & Ra quyết định
with tabs[3]:
    st.markdown("### 🎯 GIAI ĐOẠN 3: Đối Chiếu, Phát Hiện Bất Thường & Ra Quyết Định")
    if st.session_state.ranking_data is None:
        st.warning("⚠️ Vui lòng thực hiện hoàn tất Giai đoạn 1 & 2 trước!")
    else:
        rank_df = st.session_state.ranking_data
        
        st.markdown("""
        > 💡 **Cross-check Audit & Intelligent Support Prioritization:**
        > Hệ thống AI Agent đã thực hiện đối chiếu chéo (Cross-check Audit) giữa Sheets Sạch và Báo cáo Quản trị để tìm các bất thường:
        > 1. **Nghịch lý Doanh thu - Lợi nhuận:** Tăng trưởng doanh thu ảo (Doanh thu tăng nhưng lợi nhuận giảm).
        > 2. **Tỷ lệ đổi trả bất thường:** Vượt ngưỡng cảnh báo > 8% (ảnh hưởng nghiêm trọng tới uy tín & chi phí kho vận).
        > 3. **Khoảng cách KPI (KPI Gap):** Đánh giá mức độ sụt giảm so với kỳ vọng tháng.
        """)

        st.write("---")
        st.markdown("### 🚨 BẢNG XẾP HẠNG CỬA HÀNG CẦN HỖ TRỢ THEO THỨ TỰ ƯU TIÊN")
        
        # Thống kê nhanh số lượng theo nhóm ưu tiên
        p1_cnt = len(rank_df[rank_df['priority_level'].str.contains('Ưu tiên 1')])
        p2_cnt = len(rank_df[rank_df['priority_level'].str.contains('Ưu tiên 2')])
        p3_cnt = len(rank_df[rank_df['priority_level'].str.contains('Ưu tiên 3')])
        
        rc1, rc2, rc3 = st.columns(3)
        rc1.markdown(f"<div class='metric-card' style='border-top: 4px solid #DC2626;'><h4>🚨 Ưu Tiên 1 (Khẩn Cấp)</h4><h2>{p1_cnt} Cửa Hàng</h2>Cần can thiệp ngay trong tuần</div>", unsafe_allow_html=True)
        rc2.markdown(f"<div class='metric-card' style='border-top: 4px solid #F59E0B;'><h4>⚠️ Ưu Tiên 2 (Theo Dõi)</h4><h2>{p2_cnt} Cửa Hàng</h2>Cần điều chỉnh kinh doanh</div>", unsafe_allow_html=True)
        rc3.markdown(f"<div class='metric-card' style='border-top: 4px solid #10B981;'><h4>✅ Ưu Tiên 3 (Ổn Định)</h4><h2>{p3_cnt} Cửa Hàng</h2>Đạt chuẩn & tăng trưởng tốt</div>", unsafe_allow_html=True)
        
        st.write("---")
        
        for idx, row in rank_df.iterrows():
            badge_class = "badge-p1" if "Ưu tiên 1" in row['priority_level'] else ("badge-p2" if "Ưu tiên 2" in row['priority_level'] else "badge-p3")
            
            with st.expander(f"#{idx+1}. [{row['store_id']}] {row['store_name']} — Điểm khẩn cấp: {row['priority_score']}/100 — {row['priority_level']}", expanded=(idx < 3)):
                ec1, ec2, ec3, ec4 = st.columns(4)
                ec1.metric("Doanh thu thuần", f"{row['net_revenue']/1e6:,.1f} Tr")
                ec2.metric("Hoàn thành KPI", f"{row['kpi_completion_pct']}%")
                ec3.metric("Tăng trưởng Doanh thu MoM", f"{row['revenue_growth_mom']:+}%")
                ec4.metric("Tỷ lệ đổi trả hàng", f"{row['return_rate_revenue']}%", delta="Rất cao" if row['return_rate_revenue'] >= 8 else None, delta_color="inverse")
                
                st.markdown("**🔍 Phát hiện bất thường qua đối soát (Audit Findings):**")
                if row['anomalies']:
                    for an in row['anomalies']:
                        st.markdown(f"- {an}")
                else:
                    st.markdown("- *Không phát hiện bất thường nghiêm trọng.*")
                    
                st.markdown("**🎯 Đề xuất hành động cho Giám đốc Kinh doanh (AI Actionable Plan):**")
                for rec in row['recommendations']:
                    st.markdown(f"- **Khuyến nghị:** {rec}")

# TAB 4: Xem chi tiết Cửa Hàng & Cơ cấu Sản phẩm
with tabs[4]:
    st.markdown("### 🏬 Phân Tích Chuyên Sâu Từng Cửa Hàng & Cơ Cấu Sản Phẩm")
    if st.session_state.report_data is None:
        st.info("Vui lòng kích hoạt Giai đoạn 1 & 2 để xem phân tích chi tiết.")
    else:
        stores = get_store_metadata_df()
        store_choice = st.selectbox("Chọn cửa hàng cần phân tích chi tiết:", options=stores['store_id'] + " - " + stores['store_name'])
        selected_id = store_choice.split(" - ")[0]
        
        rep_row = st.session_state.report_data[st.session_state.report_data['store_id'] == selected_id].iloc[0]
        
        st.markdown(f"#### Thông tin chi tiết: **{rep_row['store_name']}** (Khu vực: {rep_row['region']} | Phân hạng: Hạng {rep_row['tier']})")
        
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Doanh thu thuần", f"{rep_row['net_revenue']/1e6:,.1f} Triệu")
        d2.metric("Mục tiêu KPI", f"{rep_row['target_revenue']/1e6:,.1f} Triệu")
        d3.metric("Lợi nhuận gộp", f"{rep_row['gross_profit']/1e6:,.1f} Triệu")
        d4.metric("Tỷ suất Lợi nhuận gộp", f"{rep_row['gross_margin_pct']:.1f}%")
        
        st.write("---")
        st.markdown("#### 📦 Cơ Cấu Doanh Thu & Lợi Nhuận Theo Nhóm Ngành Hàng (Kỳ Báo Cáo)")
        cat_df = st.session_state.cat_summary
        store_cat = cat_df[cat_df['store_id'] == selected_id].copy()
        store_cat['cat_revenue_mil'] = (store_cat['cat_revenue'] / 1e6).round(1)
        store_cat['cat_profit_mil'] = (store_cat['cat_profit'] / 1e6).round(1)
        store_cat['profit_margin'] = ((store_cat['cat_profit'] / store_cat['cat_revenue']) * 100).round(1)
        
        store_cat_display = store_cat[['category', 'cat_revenue_mil', 'cat_profit_mil', 'profit_margin']].copy()
        store_cat_display.columns = ['Ngành hàng', 'Doanh thu thuần (Tr.đ)', 'Lợi nhuận gộp (Tr.đ)', 'Biên LN %']
        
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.dataframe(store_cat_display, use_container_width=True)
        with c_right:
            chart_cat = store_cat.set_index('category')[['cat_revenue_mil', 'cat_profit_mil']]
            chart_cat.columns = ['Doanh thu (Triệu)', 'Lợi nhuận gộp (Triệu)']
            st.bar_chart(chart_cat)

st.write("---")
st.caption("Phuc An Retail AI Agent Management System • Bản quyền thuộc Công ty Bán lẻ Phúc An • Vận hành chuẩn BPMN 3 Giai Đoạn")

