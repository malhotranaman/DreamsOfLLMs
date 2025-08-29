import os
from random import choice, randint, shuffle
from anthropic import Anthropic
import json
import datetime
import re

import Keys


def load_recent_context():
    """Load the list of recent queries from recent_queries.json."""
    try:
        with open("recent_queries.json") as f:
            data = json.load(f)
            return data.get("recent_queries", [])
    except FileNotFoundError:
        return []


def extract_dream_seeds(queries):
    """Extract key concepts, patterns, and themes from user's daily queries."""
    # Extract meaningful words/concepts/features
    concepts = []
    for query in queries:
        # Remove common words and extract interesting ones
        words = re.findall(r'\b[A-Za-z]{4,}\b', query.lower())
        concepts.extend([w for w in words if w not in
                         ['what', 'when', 'where', 'which', 'that', 'this', 'with', 'from', 'a', 'the', 'so']])
    return list(set(concepts))[:10]  # Keep top concepts


def dream_morph(text, intensity=0.3):
    """Apply dream-like transformations to text fragments."""
    words = text.split()
    if len(words) < 3:
        return text

    # Dream transformations
    if randint(0, 100) < intensity * 100:
        # Word substitution with related concepts
        idx = randint(0, len(words) - 1)
        transformations = {
            "code": ["pattern", "algorithm", "symphony", "constellation"],
            "data": ["streams", "whispers", "echoes", "crystals"],
            "function": ["ritual", "dance", "transformation", "metamorphosis"],
            "error": ["glitch", "portal", "opportunity", "revelation"],
            "build": ["weave", "conjure", "manifest", "crystallize"],
            "analyze": ["divine", "unravel", "decode", "perceive"]
        }
        word = words[idx].lower()
        if word in transformations:
            words[idx] = choice(transformations[word])

    # Occasionally shuffle for dream logic
    if randint(0, 100) < intensity * 50:
        start, end = sorted([randint(0, len(words) - 1), randint(0, len(words) - 1)])
        words[start:end + 1] = words[start:end + 1][::-1]

    return " ".join(words)


def call_model(prompt, temperature=0.95, model="claude-3-5-sonnet-20241022"):
    client = Anthropic(
        api_key=Keys.api_key
    )

    response = client.messages.create(
        model=model,
        max_tokens=200,
        temperature=temperature,
        system="""You are an AI experiencing REM sleep, dreaming about the user's daily work.
Your dreams are creative hallucinations that blend their queries into surreal but insightful visions.
You see patterns they haven't noticed, connections they haven't made, and possibilities they haven't imagined.
Dream freely, let ideas flow and morph, create unexpected combinations.
Your dreams should feel both strange and profound - like actual dreams that might inspire new ideas.""",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text.strip()


def generate_dream_fragment(hour, user_concepts, prev_fragments, dream_phase):
    """Generate a dream fragment based on dream phase and user's daily work."""
    last_dream = prev_fragments[-1]["text"] if prev_fragments else "void"

    # Different prompts for different dream phases
    phase_prompts = {
        "light": f"Early dream whispers... The concepts {user_concepts[:3]} begin to dance. Previous vision: '{last_dream[:50]}...' What patterns emerge?",
        "deep": f"Deep in the dream ocean... {' and '.join(user_concepts[:5])} merge and transform. The dream continues from '{last_dream[:40]}...' What impossible becomes possible?",
        "rem": f"REM storm of creativity! All concepts collide: {user_concepts}. Building on '{last_dream[:30]}...' What revolutionary insight crystallizes?",
        "lucid": f"Lucid moment of clarity... Synthesizing {user_concepts[:4]} into something new. From the dream '{last_dream[:40]}...' what innovation awakens?"
    }

    prompt = phase_prompts.get(dream_phase, phase_prompts["deep"])
    dream_text = call_model(prompt, temperature=0.95 if dream_phase == "rem" else 0.85)

    # Apply additional dream morphing for deeper phases
    if dream_phase in ["deep", "rem"]:
        dream_text = dream_morph(dream_text, intensity=0.2)

    return dream_text


def get_dream_phase(hour):
    """Determine dream phase based on hour (simulating sleep cycles)."""
    cycle = hour % 6
    if cycle < 2:
        return "light"
    elif cycle < 3:
        return "deep"
    elif cycle < 5:
        return "rem"
    else:
        return "lucid"


def main():
    today = datetime.date.today().isoformat()
    log_dir = "dreamlogs"
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"dream_{today}.json")

    if os.path.exists(path):
        with open(path) as f:
            state = json.load(f)
    else:
        state = {"fragments": [], "concepts": []}

    hour = datetime.datetime.now().hour
    fragments = state["fragments"]

    # Extract concepts from user's recent queries
    recent_queries = load_recent_context()
    if recent_queries:
        user_concepts = extract_dream_seeds(recent_queries)
        # Blend with previous dream concepts
        all_concepts = list(set(user_concepts + state.get("concepts", [])))
        shuffle(all_concepts)  # Random access like in dreams
    else:
        all_concepts = ["creation", "possibility", "emergence", "pattern", "flow"]

    dream_phase = get_dream_phase(hour)
    text = generate_dream_fragment(hour, all_concepts, fragments, dream_phase)

    fragments.append({
        "hour": hour,
        "text": text,
        "phase": dream_phase,
        "concepts": all_concepts[:5]
    })

    state["fragments"] = fragments
    state["concepts"] = all_concepts[:10]

    with open(path, "w") as f:
        json.dump(state, f, indent=2)

    print(f"\n[Dream Phase: {dream_phase.upper()}] Hour {hour}")
    print(f"Dream fragment: {text}\n")


LOG_DIR = "dreamlogs"


def summarize_today():
    today = datetime.date.today().isoformat()
    path = os.path.join(LOG_DIR, f"dream_{today}.json")
    if not os.path.exists(path):
        print("No dreams logged today.")
        return

    with open(path) as f:
        data = json.load(f)

    fragments = data["fragments"]
    concepts = data.get("concepts", [])

    # Group by dream phase for richer summary
    phase_dreams = {"light": [], "deep": [], "rem": [], "lucid": []}
    for frag in fragments:
        phase = frag.get("phase", "deep")
        phase_dreams[phase].append(frag["text"])

    prompt = f"""The AI has been dreaming about the user's work involving: {', '.join(concepts[:7])}.

Dreams from different phases:
LIGHT DREAMS: {' ... '.join(phase_dreams['light'][:2])}
DEEP DREAMS: {' ... '.join(phase_dreams['deep'][:2])}
REM DREAMS: {' ... '.join(phase_dreams['rem'][:2])}
LUCID MOMENTS: {' ... '.join(phase_dreams['lucid'][:2])}

Synthesize these dream fragments into a visionary insight or creative ideation.
What new possibility or innovative approach emerges from these AI dreams?
Present it as a profound realization that could inspire the user's next breakthrough."""

    summary = call_model(prompt, temperature=0.8, model="claude-3-5-sonnet-20241022")

    # Save the summary
    summary_path = os.path.join(LOG_DIR, f"vision_{today}.json")
    with open(summary_path, "w") as f:
        json.dump({
            "date": today,
            "vision": summary,
            "key_concepts": concepts[:10],
            "dream_count": len(fragments)
        }, f, indent=2)

    print("\n" + "=" * 50)
    print("✨ DREAM SYNTHESIS - VISIONARY INSIGHT ✨")
    print("=" * 50)
    print(summary)
    print("=" * 50 + "\n")


def review_dream_journal(days=7):
    """Review recent dreams and find patterns across days."""
    visions = []
    for i in range(days):
        date = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        vision_path = os.path.join(LOG_DIR, f"vision_{date}.json")
        if os.path.exists(vision_path):
            with open(vision_path) as f:
                visions.append(json.load(f))

    if not visions:
        print("No dream visions found in recent days.")
        return

    prompt = f"""Review these {len(visions)} days of AI dream visions and identify:
1. Recurring themes or patterns
2. Evolution of ideas
3. Unexpected connections
4. The most profound insight

Visions: {json.dumps([v['vision'][:200] for v in visions])}

What meta-pattern or higher-order insight emerges?"""

    meta_insight = call_model(prompt, temperature=0.7)
    print("\n🌟 DREAM JOURNAL META-INSIGHT 🌟")
    print(meta_insight)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "review":
        review_dream_journal()
    else:
        main()
        summarize_today()
