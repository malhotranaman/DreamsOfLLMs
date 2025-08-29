import os
from random import choice, randint
from anthropic import Anthropic
import json
import datetime

import Keys


def load_recent_context():
    """Load the list of recent queries from recent_queries.json."""
    try:
        with open("recent_queries.json") as f:
            data = json.load(f)
            # Expecting { "recent_queries": [ ... ] }
            return data.get("recent_queries", [])
    except FileNotFoundError:
        return []


def decay_memory_chain(fragments, keep=2):
    """Simulate memory decay by randomly truncating or altering previous fragments."""
    recent = fragments[-keep:]
    mutated = []
    for text in recent:
        # simple decay: drop a random word
        words = text.split()
        if len(words) > 3:
            idx = randint(0, len(words) - 1)
            words.pop(idx)
        mutated.append(" ".join(words))
    return mutated


def call_model(prompt, temperature=0.95, model="claude-3-5-sonnet-20241022"):
    client = Anthropic(
        api_key=Keys.api_key
    )

    response = client.messages.create(
        model=model,
        max_tokens=128,
        temperature=temperature,
        system="You are an AI dreaming. Be thoughtful about the queries you had today and try and come up with new ideas based on mixing, elaborating and extending those you has today asked to you.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text.strip()


def generate_dream_fragment(hour, memory_snippets, prev_fragments):
    """Generate a surreal dream fragment for the given hour."""
    last_snippet = prev_fragments[-1]["text"] if prev_fragments else ""
    prompt = f"Hour {hour}: Dream using memories: {memory_snippets}. Continue from: '{last_snippet[:80]}'"
    return call_model(prompt)


def main():
    today = datetime.date.today().isoformat()
    log_dir = "dreamlogs"
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"dream_{today}.json")

    if os.path.exists(path):
        with open(path) as f:
            state = json.load(f)
    else:
        state = {"fragments": []}

    hour = datetime.datetime.now().hour
    fragments = state["fragments"]
    mem = load_recent_context() + decay_memory_chain([f["text"] for f in fragments])

    text = generate_dream_fragment(hour, mem, fragments)
    fragments.append({"hour": hour, "text": text})

    with open(path, "w") as f:
        json.dump(state, f, indent=2)


LOG_DIR = "dreamlogs"

def summarize_today():
    today = datetime.date.today().isoformat()
    path = os.path.join(LOG_DIR, f"dream_{today}.json")
    if not os.path.exists(path):
        print("No dreams logged today.")
        return
    with open(path) as f:
        data = json.load(f)
    texts = [frag["text"] for frag in data["fragments"]]
    prompt = ("Summarize these dream fragments into a single poetic myth, "
              "maybe coming up with some new ideas inline with what the u"
              "ser has already thought:\n") + "\n---\n".join(texts)
    summary = call_model(prompt, temperature=0.8)
    print("\n--- Dream Summary ---\n", summary)


if __name__ == "__main__":
    main()
    summarize_today()
