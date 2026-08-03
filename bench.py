from __future__ import annotations

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed


QUERIES = [
    {
        "question": "Shopee cho phép người bán đổi trả sản phẩm trong bao lâu?",
        "expected_doc": "returns-policy",
        "expected_keywords": ["đổi trả", "hoàn tiền", "15 ngày", "nhận hàng"],
        "metadata_filter": None,
        "notes": "Câu hỏi liên quan đến chính sách đổi trả và thời gian xử lý.",
    },
    {
        "question": "Ai là đối tượng được áp dụng chính sách bảo mật dữ liệu cá nhân?",
        "expected_doc": "privacy-and-data",
        "expected_keywords": ["dữ liệu cá nhân", "người dùng", "người bán", "người mua"],
        "metadata_filter": {"category": "privacy"},
        "notes": "Câu hỏi cần phân biệt đúng đối tượng người dùng và seller.",
    },
    {
        "question": "Nếu khách hàng thanh toán thất bại thì quy trình xử lý như thế nào?",
        "expected_doc": "payment-terms",
        "expected_keywords": ["thanh toán", "thất bại", "hủy", "khôi phục"],
        "metadata_filter": {"category": "payment"},
        "notes": "Câu hỏi về ngoại lệ và quy trình xử lý thanh toán.",
    },
    {
        "question": "Người bán có thể khiếu nại quyết định của nền tảng bằng cách nào?",
        "expected_doc": "seller-appeal",
        "expected_keywords": ["khiếu nại", "chứng cứ", "tài khoản", "đánh giá"],
        "metadata_filter": {"customer_role": "seller"},
        "notes": "Câu hỏi về quy trình khiếu nại và tranh chấp.",
    },
    {
        "question": "Những điều kiện nào khiến sản phẩm bị từ chối đăng bán?",
        "expected_doc": "seller-listing",
        "expected_keywords": ["đăng bán", "cấm", "phản động", "bạo lực", "quy định"],
        "metadata_filter": {"customer_role": "seller"},
        "notes": "Câu hỏi về danh sách điều kiện và quy định đăng bán.",
    },
]


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def _summarize_results(results: list[dict], keywords: list[str]) -> str:
    matched = []
    for result in results:
        hits = _match_keywords(result["content"], keywords)
        if hits:
            matched.append(f"{result['id']}:{','.join(hits[:2])}")
    return "; ".join(matched) if matched else "no keyword evidence"


def main() -> None:
    chunker = RecursiveChunker(chunk_size=400)
    store = build_knowledge_base("data/k4_ecommerce", _mock_embed, chunker=chunker, collection_name="lab7_bench")
    agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: "Agent answer generated from retrieved context.")

    print("Strategy: RecursiveChunker(chunk_size=400)")
    print(f"Chunks loaded: {store.get_collection_size()}")
    print()

    for index, item in enumerate(QUERIES, 1):
        base_results = store.search(item["question"], top_k=3)
        filtered_results = []
        if item["metadata_filter"]:
            filtered_results = store.search_with_filter(item["question"], top_k=3, metadata_filter=item["metadata_filter"])

        print(f"Query {index}: {item['question']}")
        print(f"Expected doc: {item['expected_doc']}")
        print(f"Notes: {item['notes']}")
        print("Unfiltered top-3:")
        for result in base_results:
            preview = result["content"][:140].replace("\n", " ")
            print(f" - score={result['score']:.4f} doc_id={result['id']} preview={preview}")

        if filtered_results:
            print("Filtered top-3:")
            for result in filtered_results:
                preview = result["content"][:140].replace("\n", " ")
                print(f" - score={result['score']:.4f} doc_id={result['id']} preview={preview}")

        evidence_unfiltered = _summarize_results(base_results, item["expected_keywords"])
        evidence_filtered = _summarize_results(filtered_results, item["expected_keywords"]) if filtered_results else "n/a"
        print(f"Evidence (unfiltered): {evidence_unfiltered}")
        print(f"Evidence (filtered): {evidence_filtered}")
        agent_answer = agent.answer(item["question"], top_k=3)
        print(f"Agent answer: {agent_answer}")
        if filtered_results and filtered_results != base_results:
            print("Filter effect: changed ranking and reduced noise.")
        elif filtered_results:
            print("Filter effect: no meaningful difference compared with unfiltered search.")
        else:
            print("Filter effect: no metadata filter applied.")
        print()


if __name__ == "__main__":
    main()
