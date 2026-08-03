# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Dương  
**Mã sinh viên:** 2A202601400  
**Nhóm:** K4-02  
**Ngày:** 2026-08-03  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Độ tương tự cosine cao cho thấy hai vector embedding có góc giữa chúng rất nhỏ (hướng trùng nhau), phản ánh hai đoạn văn bản có mức độ tương đồng lớn về ngữ nghĩa dù từ ngữ thể hiện có thể khác nhau. Giá trị nằm trong khoảng [-1, 1], càng gần 1 thì càng tương đồng.*

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể đổi trả hàng trong vòng 15 ngày.
- Câu B: Sản phẩm giao lỗi được hỗ trợ hoàn tiền trong 15 ngày kể từ khi nhận.
- Tại sao tương đồng: Cả hai câu đều đề cập đến chính sách và thời hạn trả hàng/hoàn tiền của sàn TMĐT.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Quy trình đăng bán sản phẩm mới dành cho người bán.
- Câu B: Chính sách bảo mật dữ liệu và thông tin cá nhân của người dùng.
- Tại sao khác: Hai câu thuộc hai phạm vi nghiệp vụ hoàn toàn khác nhau (Vận hành bán hàng vs An toàn thông tin).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Cosine similarity chỉ quan tâm đến hướng (chủ đề/ngữ nghĩa) của vector mà không bị ảnh hưởng bởi độ dài (magnitude) của vector đó. Vì các đoạn văn ngắn/dài khác nhau tạo ra độ dài vector khác nhau, Cosine giúp so sánh công bằng về ngữ nghĩa hơn so với khoảng cách Euclid.*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
**Phép tính:**

- Bước di chuyển (Stride) = `chunk_size - overlap = 500 - 50 = 450` ký tự.
- Công thức tính số chunk:

```text
ceil((10000 - 500) / 450) + 1
= ceil(9500 / 450) + 1
= ceil(21.11) + 1
= 22 + 1
= 23 chunks

### Nếu overlap tăng lên 100 thì sao?

Khi overlap tăng lên 100, Stride giảm xuống còn 500 - 100 = 400 ký tự. Số lượng chunk sẽ tăng lên thành ceil(9500 / 400) + 1 = 24 + 1 = 25 chunks. Tăng overlap giúp hạn chế việc bị gãy vỡ ngữ cảnh tại ranh giới cắt giữa hai chunk kề nhau, hỗ trợ truy xuất thông tin chính xác hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng biểu thức chính quy `re.split(r'(?<=[.!?])\s+', text)` để tách văn bản theo các dấu kết thúc câu (`.`, `!`, `?`). Sau đó, tôi gom nhóm các câu lại theo `max_sentences_per_chunk` và bỏ qua các khoảng trắng thừa hoặc chuỗi rỗng để giữ chunk hợp lý.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi dùng thuật toán chia đệ quy với danh sách dấu phân cách theo ưu tiên giảm dần: `['\n\n', '\n', '.', ' ']`. Trường hợp cơ sở là khi văn bản đã nhỏ hơn `chunk_size` hoặc không còn separator để dùng; nếu còn vượt quá giới hạn, hàm tiếp tục chia bằng separator kế tiếp cho đến khi có chunk phù hợp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` thực hiện embedding nội dung của các tài liệu qua `embedder`, tạo ID duy nhất và lưu vector cùng metadata vào kho vector. `search` nhúng query đầu vào, tính độ tương tự cosine với toàn bộ vector trong kho, sắp xếp giảm dần theo điểm số và trả về top-k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi thực hiện pre-filtering trước khi tính similarity: nếu có `metadata_filter`, danh sách candidate sẽ được lọc theo metadata trước, sau đó mới tính cosine similarity trên tập đã lọc. `delete_document` tìm kiếm `doc_id` tương ứng và loại khỏi bộ nhớ, trả về `True` nếu xóa thành công và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi dùng `EmbeddingStore` để truy xuất các chunk liên quan nhất với câu hỏi người dùng. Sau đó, các chunk này được đưa vào prompt mẫu làm ngữ cảnh (context) để LLM/Agent tạo câu trả lời và đính kèm danh sách trích dẫn nguồn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts ==============================
platform win32 -- Python 3.11.x, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

================================= 42 passed in 1.85s ================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách trả hàng và hoàn tiền Shopee | Quy định đổi trả sản phẩm lỗi dành cho người mua | cao | 0.88 | Có |
| 2 | Hướng dẫn đăng bán sản phẩm mới | Danh sách các sản phẩm bị cấm đăng bán trên sàn | cao | 0.79 | Có |
| 3 | Phương thức thanh toán qua ví điện tử | Quy trình giải quyết khiếu nại của người bán | thấp | 0.21 | Có |
| 4 | Yêu cầu xóa dữ liệu thông tin cá nhân | Thay đổi địa chỉ nhận hàng của người mua | thấp | 0.35 | Có |
| 5 | Thời gian giao hàng dự kiến của đơn hàng | Chính sách bảo mật thông tin tài khoản người dùng | thấp | 0.12 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp câu số 4 có điểm thực tế là 0.35, cao hơn mức kỳ vọng ban đầu. Điều này cho thấy embedding có thể giữ một phần liên quan ngữ cảnh chung trong cùng lĩnh vực thương mại điện tử, dù ý định nghiệp vụ của hai câu là khác nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Sau khi chạy benchmark mới trên bộ corpus K4, tôi ghi nhận các kết quả sau:

| # | Câu hỏi (Query) | Kết quả chạy benchmark | Có chunk liên quan trong top-3? | Nhận xét |
|---|-------|-----------------------|--------------------------------|----------|
| 1 | Shopee cho phép người bán đổi trả sản phẩm trong bao lâu? | Top-3 bị nhiễu bởi các tài liệu khác; `returns-policy` xuất hiện nhưng không có keyword evidence rõ ràng. | Không rõ | Câu hỏi này còn bị ảnh hưởng bởi embedding similarity và nội dung không đủ đặc trưng. |
| 2 | Ai là đối tượng được áp dụng chính sách bảo mật dữ liệu cá nhân? | Khi dùng metadata filter `category=privacy`, tài liệu `privacy-and-data` xuất hiện ở top-3. | Có | Metadata filter giúp làm đúng hướng cho câu hỏi về quyền riêng tư. |
| 3 | Nếu khách hàng thanh toán thất bại thì quy trình xử lý như thế nào? | Top-3 vẫn giữ `payment-terms` ở đầu; đây là kết quả tốt nhất trong benchmark. | Có | Câu hỏi này có độ rõ ràng cao và dễ trùng với tài liệu chuyên biệt. |
| 4 | Người bán có thể khiếu nại quyết định của nền tảng bằng cách nào? | Cả unfiltered lẫn filtered đều không đưa `seller-appeal` vào top-3. | Không | Đây là case thất bại rõ ràng; cần cải thiện query matching hoặc bổ sung chunk chất lượng hơn. |
| 5 | Những điều kiện nào khiến sản phẩm bị từ chối đăng bán? | Khi dùng metadata filter `customer_role=seller`, `seller-listing` xuất hiện ở top-3 và có keyword `đăng bán`. | Có | Metadata filter giúp rất tốt cho các query mang tính vai trò và điều kiện. |

**Bao nhiêu câu hỏi có chunk có liên quan trong top-3?** 3 / 5

**Điều hay nhất tôi học được từ benchmark mới:**
> Metadata filtering giúp cải thiện độ chính xác ở các câu hỏi phân biệt vai trò như seller/buyer, nhưng với các câu hỏi mang tính ngữ nghĩa rộng hoặc chưa khớp từ khóa, embedding store vẫn có thể bị nhiễu. Vì thế, việc chuẩn hóa metadata và cải thiện chunk quality là bước quan trọng tiếp theo.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

---


