from backend.agents.research_agent import generate_research


topic = "The future of artificial intelligence"

research = generate_research(topic)

print("\n===== RESEARCH REPORT =====\n")
print(research)