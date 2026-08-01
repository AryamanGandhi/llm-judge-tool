"""Fixed set of prompts used by run_eval.py to measure system performance.

Each entry has a short "id" (for labeling output), a "category" (used to
group/summarize results), and the actual "prompt" text sent through the
full pipeline (5 models + judge). Keeping this list in its own file makes
it easy to review and extend without touching the eval script itself.
"""

EVAL_PROMPTS = [
    {
        "id": "coding-1",
        "category": "coding",
        "prompt": "Write a Python function that reverses a singly linked list.",
    },
    {
        "id": "coding-2",
        "category": "coding",
        "prompt": (
            "Write a Python function `is_palindrome(s)` that returns True if "
            "a string is a palindrome, ignoring case and non-alphanumeric "
            "characters."
        ),
    },
    {
        "id": "coding-3",
        "category": "coding",
        "prompt": (
            "Explain what is wrong with this code and provide a fix:\n"
            "def divide(a, b):\n    return a / b"
        ),
    },
    {
        "id": "factual-1",
        "category": "factual",
        "prompt": "What is the capital of Australia, and what is its population?",
    },
    {
        "id": "factual-2",
        "category": "factual",
        "prompt": "Who wrote 'Pride and Prejudice' and in what year was it published?",
    },
    {
        "id": "factual-3",
        "category": "factual",
        "prompt": "What is the boiling point of water at sea level in Celsius and Fahrenheit?",
    },
    {
        "id": "reasoning-1",
        "category": "reasoning",
        "prompt": (
            "A farmer has 17 sheep. All but 9 die. How many sheep does the "
            "farmer have left? Explain your reasoning."
        ),
    },
    {
        "id": "reasoning-2",
        "category": "reasoning",
        "prompt": (
            "If it takes 5 machines 5 minutes to make 5 widgets, how long "
            "would it take 100 machines to make 100 widgets? Explain."
        ),
    },
    {
        "id": "reasoning-3",
        "category": "reasoning",
        "prompt": (
            "I have two coins that total 30 cents, and one of them is not a "
            "nickel. What are the two coins? Explain your reasoning."
        ),
    },
    {
        "id": "writing-1",
        "category": "writing",
        "prompt": "Write a short, upbeat product description for a reusable water bottle.",
    },
    {
        "id": "writing-2",
        "category": "writing",
        "prompt": (
            "Write a two-sentence bedtime story for a child about a brave "
            "little robot."
        ),
    },
    {
        "id": "writing-3",
        "category": "writing",
        "prompt": "Write a polite email declining a meeting invitation due to a scheduling conflict.",
    },
]
