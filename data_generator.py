"""
Phuc An Retail - Data Generator & Analytics Core
Tạo dữ liệu thực tế mẫu cho 18 cửa hàng, ~60.000 giao dịch/tháng gồm đơn hàng, đơn hủy, đơn hoàn trả, danh mục sản phẩm, mục tiêu KPI.
"""
import random
import datetime
import pandas as pd
import numpy as np

# Danh sách 18 cửa hàng Phúc An Retail
STORES = [
    {"store_id": "CH01", "store_name": "Phúc An - Quận 1 (Nguyễn Huệ)", "region": "Miền Nam", "tier": "A", "target_revenue": 2800000000},
    {"store_id": "CH02", "store_name": "Phúc An - Quận 3 (Võ Văn Tần)", "region": "Miền Nam", "tier": "A", "target_revenue": 2400000000},
    {"store_id": "CH03", "store_name": "Phúc An - Quận 7 (Phú Mỹ Hưng)", "region": "Miền Nam", "tier": "A", "target_revenue": 2600000000},
    {"store_id": "CH04", "store_name": "Phúc An - Bình Thạnh (Điện Biên Phủ)", "region": "Miền Nam", "tier": "B", "target_revenue": 1900000000},
    {"store_id": "CH05", "store_name": "Phúc An - Tân Bình (Cộng Hòa)", "region": "Miền Nam", "tier": "B", "target_revenue": 1850000000},
    {"store_id": "CH06", "store_name": "Phúc An - Gò Vấp (Quang Trung)", "region": "Miền Nam", "tier": "B", "target_revenue": 1750000000},
    {"store_id": "CH07", "store_name": "Phúc An - TP. Thủ Đức (Thảo Điền)", "region": "Miền Nam", "tier": "A", "target_revenue": 2500000000},
    {"store_id": "CH08", "store_name": "Phúc An - Quận 10 (Sư Vạn Hạnh)", "region": "Miền Nam", "tier": "B", "target_revenue": 1800000000},
    {"store_id": "CH09", "store_name": "Phúc An - Hoàn Kiếm (Tràng Tiền)", "region": "Miền Bắc", "tier": "A", "target_revenue": 2700000000},
    {"store_id": "CH10", "store_name": "Phúc An - Ba Đình (Liễu Giai)", "region": "Miền Bắc", "tier": "A", "target_revenue": 2300000000},
    {"store_id": "CH11", "store_name": "Phúc An - Cầu Giấy (Xuân Thủy)", "region": "Miền Bắc", "tier": "B", "target_revenue": 1950000000},
    {"store_id": "CH12", "store_name": "Phúc An - Đống Đa (Chùa Bộc)", "region": "Miền Bắc", "tier": "B", "target_revenue": 1850000000},
    {"store_id": "CH13", "store_name": "Phúc An - Hà Đông (Trần Phú)", "region": "Miền Bắc", "tier": "C", "target_revenue": 1400000000},
    {"store_id": "CH14", "store_name": "Phúc An - Long Biên (Nguyễn Văn Cừ)", "region": "Miền Bắc", "tier": "C", "target_revenue": 1350000000},
    {"store_id": "CH15", "store_name": "Phúc An - Hải Châu (Đà Nẵng)", "region": "Miền Trung", "tier": "A", "target_revenue": 2200000000},
    {"store_id": "CH16", "store_name": "Phúc An - Thanh Khê (Đà Nẵng)", "region": "Miền Trung", "tier": "B", "target_revenue": 1600000000},
    {"store_id": "CH17", "store_name": "Phúc An - Nha Trang (Trần Phú)", "region": "Miền Trung", "tier": "B", "target_revenue": 1700000000},
    {"store_id": "CH18", "store_name": "Phúc An - TP. Cần Thơ (30 Tháng 4)", "region": "Miền Nam", "tier": "C", "target_revenue": 1450000000},
]

# Danh mục sản phẩm & giá vốn
PRODUCTS = [
    {"sku": "SKU001", "name": "Nồi chiên không dầu 6.5L SmartLock", "category": "Gia dụng", "cost_price": 850000, "sale_price": 1450000},
    {"sku": "SKU002", "name": "Máy xay sinh tố đa năng 3 cối Pro", "category": "Gia dụng", "cost_price": 420000, "sale_price": 790000},
    {"sku": "SKU003", "name": "Robot hút bụi lau nhà RoboSweep X5", "category": "Gia dụng thông minh", "cost_price": 3100000, "sale_price": 5490000},
    {"sku": "SKU004", "name": "Máy lọc không khí Plasma AirClean", "category": "Gia dụng thông minh", "cost_price": 1950000, "sale_price": 3290000},
    {"sku": "SKU005", "name": "Bình giữ nhiệt Inox 316 Cao cấp 1000ml", "category": "Đời sống", "cost_price": 110000, "sale_price": 280000},
    {"sku": "SKU006", "name": "Bàn chải điện Sonic Clean 5 chế độ", "category": "Chăm sóc cá nhân", "cost_price": 190000, "sale_price": 450000},
    {"sku": "SKU007", "name": "Máy sấy tóc ion âm tốc độ cao Pro", "category": "Chăm sóc cá nhân", "cost_price": 380000, "sale_price": 890000},
    {"sku": "SKU008", "name": "Bếp điện từ đơn cảm ứng siêu mỏng", "category": "Gia dụng", "cost_price": 450000, "sale_price": 890000},
    {"sku": "SKU009", "name": "Chảo chống dính tổ ong Ceramic 28cm", "category": "Gia dụng", "cost_price": 160000, "sale_price": 390000},
    {"sku": "SKU010", "name": "Bộ hộp cơm giữ nhiệt văn phòng LockPlus", "category": "Đời sống", "cost_price": 140000, "sale_price": 320000},
    {"sku": "SKU011", "name": "Cân điện tử sức khỏe thông minh Bluetooth", "category": "Chăm sóc cá nhân", "cost_price": 120000, "sale_price": 290000},
    {"sku": "SKU012", "name": "Quạt tháp lọc không khí Ion Tower", "category": "Gia dụng thông minh", "cost_price": 1200000, "sale_price": 2190000},
]

def generate_sample_raw_data(period_current="2026-10", period_compare="2026-09", total_rows=60000):
    """
    Tạo dữ liệu giao dịch thô mô phỏng các lỗi thực tế:
    1. Trùng lặp mã giao dịch (do sync mạng, nhân viên quét trùng)
    2. Đơn hàng ở các trạng thái: 'Hoàn thành', 'Đã hủy', 'Đổi trả'
    3. Hàng đổi trả ghi âm hoặc dương tùy chi nhánh
    4. Giao dịch lệch kỳ hoặc thiếu ngày
    """
    random.seed(42)
    np.random.seed(42)

    rows = []
    
    # Phân chia kỳ: 55% kỳ hiện tại, 45% kỳ so sánh
    current_count = int(total_rows * 0.55)
    compare_count = total_rows - current_count

    # Kỳ hiện tại (Tháng 10/2026)
    start_cur = datetime.date(2026, 10, 1)
    end_cur = datetime.date(2026, 10, 31)
    days_cur = (end_cur - start_cur).days + 1

    # Kỳ so sánh (Tháng 09/2026)
    start_cmp = datetime.date(2026, 9, 1)
    end_cmp = datetime.date(2026, 9, 30)
    days_cmp = (end_cmp - start_cmp).days + 1

    # Một số cửa hàng có đặc thù (VD: CH13, CH18 tỷ lệ trả hàng cao hoặc tụt giảm nghiêm trọng)
    for i in range(total_rows):
        is_current = (i < current_count)
        if is_current:
            trans_date = start_cur + datetime.timedelta(days=random.randint(0, days_cur - 1))
            period = period_current
        else:
            trans_date = start_cmp + datetime.timedelta(days=random.randint(0, days_cmp - 1))
            period = period_compare

        # Chọn cửa hàng
        store = random.choice(STORES)
        store_id = store["store_id"]

        # Chọn sản phẩm
        prod = random.choice(PRODUCTS)
        sku = prod["sku"]

        # Số lượng thông thường 1-4
        qty = random.choices([1, 2, 3, 4, 5], weights=[0.65, 0.20, 0.08, 0.04, 0.03])[0]

        # Trạng thái đơn hàng:
        # Cửa hàng CH13 hoặc CH18 có vấn đề: tỷ lệ đổi trả & huỷ cao hơn
        if store_id in ["CH13", "CH18"]:
            status = random.choices(
                ["Hoàn thành", "Đã hủy", "Đổi trả"],
                weights=[0.76, 0.12, 0.12]
            )[0]
        elif store_id in ["CH01", "CH09"]:
            status = random.choices(
                ["Hoàn thành", "Đã hủy", "Đổi trả"],
                weights=[0.92, 0.04, 0.04]
            )[0]
        else:
            status = random.choices(
                ["Hoàn thành", "Đã hủy", "Đổi trả"],
                weights=[0.87, 0.07, 0.06]
            )[0]

        # Quy ước doanh số bán ra
        unit_price = prod["sale_price"]
        line_amount = qty * unit_price

        # Giả lập lỗi thực tế: một số cửa hàng ghi hàng trả với số lượng âm, một số ghi số lượng dương kèm trạng thái "Đổi trả"
        # Một số giao dịch chiết khấu hoặc ghi nhận lỗi
        raw_qty = qty
        raw_amount = line_amount
        if status == "Đổi trả":
            # 50% chi nhánh ghi âm, 50% ghi dương nhưng status là Đổi trả
            if random.random() < 0.5:
                raw_qty = -qty
                raw_amount = -line_amount

        trans_id = f"TXN-{trans_date.strftime('%Y%m')}-{i+1:06d}"

        rows.append({
            "trans_id": trans_id,
            "trans_date": trans_date.strftime("%Y-%m-%d"),
            "period": period,
            "store_id": store_id,
            "store_name": store["store_name"],
            "sku": sku,
            "product_name": prod["name"],
            "category": prod["category"],
            "quantity": raw_qty,
            "unit_price": unit_price,
            "line_amount": raw_amount,
            "status": status,
            "payment_method": random.choice(["Chuyển khoản QR", "Tiền mặt", "Thẻ tín dụng", "Ví điện tử"]),
            "note": "Khách hoàn trả do lỗi kỹ thuật" if status == "Đổi trả" and random.random() < 0.3 else ""
        })

    # Tạo cố ý 1.200 dòng TRÙNG LẶP (Duplicate Transactions)
    dup_indices = random.sample(range(len(rows)), 1200)
    for idx in dup_indices:
        dup_row = dict(rows[idx])
        # Đôi khi thêm tiền tố hoặc giữ nguyên trans_id
        rows.append(dup_row)

    # Đảo lộn ngẫu nhiên
    random.shuffle(rows)

    df_raw = pd.DataFrame(rows)
    return df_raw

if __name__ == "__main__":
    print("Generating 60,000 raw sales records for Phuc An Retail...")
    df = generate_sample_raw_data()
    print(f"Total raw records created (including duplicates): {len(df)}")
    df.to_parquet("phucan_raw_data.parquet", index=False)
    print("Saved to phucan_raw_data.parquet successfully!")

