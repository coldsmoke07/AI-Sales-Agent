"""
WaveNxD AI Sales Representative - CLI Interactive Runner
========================================================
Interactive terminal interface for demonstrating the WaveNxD Sales Representative.
Runs directly in your terminal using standard Python with zero external dependencies.

Usage:
    python run.py
"""

import sys
from salesgpt.agent import SalesAgent
from salesgpt.catalog import WaveNxDCatalog
from salesgpt.stages import get_stage_info


def main():
    catalog = WaveNxDCatalog()
    agent = SalesAgent(catalog_obj=catalog)
    messages = []

    print("=" * 65)
    print("WaveNxD Technologies Pvt. Ltd., Kolhapur")
    print("AI Technical Sales Representative (SalesGPT Engine)")
    print("=" * 65)
    print("Commands: 'reset' to start over, 'catalog' to inspect products, 'exit' to quit.\n")

    # Initial Turn: Greeting & Pitch
    first_res = agent.run([])
    messages.append({"role": "assistant", "content": first_res["reply"]})
    print(f"\n[Arjun Kulkarni - WaveNxD Sales Representative | Stage 1: Introduction]:\n{first_res['reply']}\n")
    if first_res.get("options"):
        print("Suggested responses:")
        for opt in first_res["options"][:5]:
            print(f"  • {opt}")
        print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting consultation. Thank you for connecting with WaveNxD!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Session ended. Thank you for connecting with WaveNxD Technologies!")
            break

        if user_input.lower() == "catalog":
            print("\n--- WaveNxD Official Nozzle Catalog ---")
            for n in catalog.get_all_nozzles():
                print(f"• {n['family']} | {n['frequency_khz']} kHz | Droplet: {n['droplet_size_um']} µm | Feed: {n['feed_rate_text']} | Viscosity: {n['viscosity_text']}")
                print(f"  Applications: {', '.join(n['typical_applications'])}\n")
            continue

        if user_input.lower() == "reset":
            messages = []
            res = agent.run([{"role": "user", "content": "reset"}])
            messages.append({"role": "assistant", "content": res["reply"]})
            print(f"\n[Arjun Kulkarni | Stage 1: Introduction]:\n{res['reply']}\n")
            continue

        messages.append({"role": "user", "content": user_input})
        res = agent.run(messages)
        messages.append({"role": "assistant", "content": res["reply"]})

        stage_meta = get_stage_info(res["stage"])
        print(f"\n[Arjun Kulkarni | Stage {res['stage']}: {stage_meta['name']}]:")
        print(res["reply"])

        if res.get("options"):
            print("\nSuggested next inputs:")
            for opt in res["options"]:
                print(f"  • {opt}")
        print("-" * 65)


if __name__ == "__main__":
    main()
