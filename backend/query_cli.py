"""
Interactive CLI for querying the RAG pipeline without a browser.

Usage:
    python query_cli.py
    python query_cli.py --k 3
"""
import argparse
import json
import requests

RESET = "\033[0m"
BOLD  = "\033[1m"
CYAN  = "\033[36m"
GREEN = "\033[32m"
AMBER = "\033[33m"
GREY  = "\033[90m"

REFUSAL = "I cannot find this in the provided documents"

def query(api: str, question: str, k: int) -> dict:
    resp = requests.post(
        f"{api}/query",
        json={"query": question, "k": k},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()

def display(result: dict) -> None:
    answer = result["answer"]
    sources = result.get("sources", [])
    chunks  = result.get("chunks", [])

    is_refusal = REFUSAL in answer

    print()
    if is_refusal:
        print(f"{AMBER}[Not found in documents]{RESET}")
    else:
        print(f"{BOLD}Answer:{RESET}")
    print(answer)

    if sources and not is_refusal:
        print(f"\n{GREY}Sources: {', '.join(sources)}{RESET}")

    if chunks and not is_refusal:
        print(f"{GREY}Retrieved {len(chunks)} chunks:{RESET}")
        for i, c in enumerate(chunks, 1):
            meta = c.get("metadata", {})
            print(f"  {GREY}[{i}] {meta.get('filename','?')} "
                  f"chunk#{meta.get('chunk_index','?')} "
                  f"score={c.get('score',0):.2f}{RESET}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    print(f"{BOLD}RAG Query CLI{RESET} — connected to {args.api}")
    print("Type your question and press Enter. Ctrl+C to exit.\n")

    while True:
        try:
            question = input(f"{CYAN}You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not question:
            continue

        try:
            result = query(args.api, question, args.k)
            display(result)
        except requests.HTTPError as e:
            print(f"  Error: {e.response.text}")
        except Exception as exc:
            print(f"  Error: {exc}")
        print()

if __name__ == "__main__":
    main()
