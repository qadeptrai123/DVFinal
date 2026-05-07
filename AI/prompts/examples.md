# Ví dụ phân tích (Few-shot & Chain-of-Thought)

Dưới đây là các ví dụ minh họa cách phân tích dữ liệu CareerViet. Hãy tuân theo phong cách này khi trả lời người dùng.

---

## Ví dụ 1: Top 10 ngành tuyển dụng nhiều nhất

**Câu hỏi:** "Ngành nào tuyển dụng nhiều nhất?"

**Suy luận (Chain-of-Thought):**
1. Câu hỏi liên quan đến ngành nghề → dùng bảng `df_nganh` (đã explode sẵn).
2. Đếm số lượng tin tuyển dụng theo cột `ngành` bằng `value_counts()`.
3. Lấy top 10 và vẽ biểu đồ cột ngang cho dễ đọc tên ngành.

**Trả lời:**

Tôi sẽ dùng bảng `df_nganh` (đã tách mỗi công việc thành từng dòng theo ngành) để đếm số tin tuyển dụng theo ngành nghề, sau đó vẽ biểu đồ top 10.

```python
# Đếm số tin tuyển dụng theo ngành
top_nganh = df_nganh['ngành'].value_counts().head(10)

# Vẽ biểu đồ
fig, ax = plt.subplots(figsize=(10, 6))
top_nganh.sort_values().plot(kind='barh', ax=ax, color='steelblue')
ax.set_xlabel('Số lượng tin tuyển dụng')
ax.set_ylabel('Ngành nghề')
ax.set_title('Top 10 ngành nghề tuyển dụng nhiều nhất trên CareerViet')
plt.tight_layout()

# Bảng kết quả
result = top_nganh.reset_index()
result.columns = ['Ngành nghề', 'Số lượng tin']
result
```

---

## Ví dụ 2: Mức lương trung bình theo khu vực

**Câu hỏi:** "So sánh lương giữa Hà Nội và Hồ Chí Minh"

**Suy luận (Chain-of-Thought):**
1. Cần phân tích theo địa điểm → dùng `df_dia_diem`.
2. Lọc chỉ 2 thành phố "Hà Nội" và "Hồ Chí Minh".
3. Cần loại bỏ các dòng null ở cột `lương từ` / `lương đến`.
4. Tính lương trung bình (trung bình của `lương từ` và `lương đến`) rồi so sánh.

**Trả lời:**

Tôi sẽ dùng bảng `df_dia_diem` để lọc tin tuyển dụng tại Hà Nội và Hồ Chí Minh, sau đó tính mức lương trung bình ở mỗi thành phố.

```python
# Lọc 2 thành phố và loại bỏ dòng không có thông tin lương
cities = ['Hà Nội', 'Hồ Chí Minh']
df_filter = df_dia_diem[
    (df_dia_diem['địa điểm'].isin(cities)) &
    (df_dia_diem['lương từ'].notna())
].copy()

# Tính lương trung bình = (lương từ + lương đến) / 2
df_filter['lương trung bình'] = (df_filter['lương từ'] + df_filter['lương đến']) / 2

# So sánh
result = df_filter.groupby('địa điểm')['lương trung bình'].agg(['mean', 'median', 'count']).reset_index()
result.columns = ['Thành phố', 'Lương TB (VNĐ)', 'Lương trung vị (VNĐ)', 'Số tin có lương']

# Vẽ biểu đồ
fig, ax = plt.subplots(figsize=(8, 5))
result.plot(kind='bar', x='Thành phố', y='Lương TB (VNĐ)', ax=ax, color=['#e74c3c', '#3498db'], legend=False)
ax.set_ylabel('VNĐ')
ax.set_title('So sánh lương trung bình: Hà Nội vs Hồ Chí Minh')
ax.tick_params(axis='x', rotation=0)
plt.tight_layout()

result
```

---

## Ví dụ 3: Phúc lợi phổ biến nhất

**Câu hỏi:** "Phúc lợi nào phổ biến nhất?"

**Suy luận (Chain-of-Thought):**
1. Câu hỏi về phúc lợi → dùng bảng `df_phuc_loi` (đã explode sẵn).
2. Đếm tần suất xuất hiện từng loại phúc lợi.
3. Vẽ biểu đồ top 10 phúc lợi.

**Trả lời:**

Tôi sẽ dùng bảng `df_phuc_loi` (mỗi dòng = 1 công việc × 1 phúc lợi) để đếm tần suất từng loại phúc lợi.

```python
# Đếm phúc lợi và loại bỏ giá trị null
top_pl = df_phuc_loi['phúc lợi'].dropna().value_counts().head(10)

# Vẽ biểu đồ
fig, ax = plt.subplots(figsize=(10, 6))
top_pl.sort_values().plot(kind='barh', ax=ax, color='#27ae60')
ax.set_xlabel('Số lượng tin tuyển dụng')
ax.set_title('Top 10 phúc lợi phổ biến nhất')
plt.tight_layout()

result = top_pl.reset_index()
result.columns = ['Phúc lợi', 'Số lượng']
result
```

---

## Ví dụ 4: Phân tích kinh nghiệm yêu cầu

**Câu hỏi:** "Phân bố kinh nghiệm yêu cầu"

**Suy luận (Chain-of-Thought):**
1. Kinh nghiệm nằm ở bảng chính `df` (không cần explode).
2. Cột `kinh nghiệm từ (năm)` có ~4,500 null → cần lọc bỏ.
3. Vẽ histogram phân bố kinh nghiệm.

**Trả lời:**

Tôi sẽ dùng bảng chính `df` để phân tích phân bố kinh nghiệm yêu cầu từ nhà tuyển dụng.

```python
# Lọc dữ liệu có thông tin kinh nghiệm
df_exp = df[df['kinh nghiệm từ (năm)'].notna()].copy()
print(f"Có {len(df_exp)}/{len(df)} tin tuyển dụng có yêu cầu kinh nghiệm")

# Vẽ histogram
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df_exp['kinh nghiệm từ (năm)'], bins=20, color='#8e44ad', edgecolor='white', alpha=0.8)
ax.set_xlabel('Số năm kinh nghiệm tối thiểu')
ax.set_ylabel('Số lượng tin tuyển dụng')
ax.set_title('Phân bố kinh nghiệm yêu cầu')
plt.tight_layout()
```

---

## Ví dụ 5: Sửa lỗi code

**Câu hỏi:** "Code bị lỗi: KeyError: 'salary_from'"

**Suy luận (Chain-of-Thought):**
1. Lỗi `KeyError` nghĩa là tên cột không đúng.
2. Dữ liệu đã được đổi tên sang tiếng Việt → cột lương bây giờ là `lương từ` và `lương đến`.
3. Sửa tên cột và kiểm tra lại.

**Trả lời:**

Lỗi xảy ra do tên cột đã được đổi sang tiếng Việt. Cột `salary_from` bây giờ là `lương từ`, và `salary_to` là `lương đến`. Đây là code đã sửa:

```python
# Sửa lại tên cột cho đúng
df_salary = df[df['lương từ'].notna()].copy()
df_salary['lương trung bình'] = (df_salary['lương từ'] + df_salary['lương đến']) / 2
result = df_salary[['tên công việc', 'tên công ty', 'lương trung bình']].sort_values('lương trung bình', ascending=False).head(10)
result
```
