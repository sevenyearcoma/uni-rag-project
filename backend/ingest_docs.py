"""
Convenience script to ingest documents via the API.

Usage:
    python ingest_docs.py --dir data/sample_docs --strategy fixed
    python ingest_docs.py --dir data/sample_docs --strategy recursive --clear
"""
import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the RAG pipeline.")
    parser.add_argument("--dir", default="./data/sample_docs", help="Directory of documents")
    parser.add_argument("--strategy", choices=["fixed", "recursive"], default="fixed")
    parser.add_argument("--chunk-size", type=int, default=256)
    parser.add_argument("--overlap", type=float, default=0.15)
    parser.add_argument("--clear", action="store_true", help="Clear index before ingesting")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    payload = {
        "directory": args.dir,
        "strategy": args.strategy,
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
        "clear_first": args.clear,
    }

    print(f"Ingesting '{args.dir}' with strategy='{args.strategy}'…")
    resp = requests.post(f"{args.api}/ingest", json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    print(f"  Documents loaded : {data['documents_loaded']}")
    print(f"  Chunks created   : {data['chunks_created']}")
    print(f"  Total vectors    : {data['total_vectors']}")
    print(f"  Strategy used    : {data['strategy']}")

if __name__ == "__main__":
    main()
