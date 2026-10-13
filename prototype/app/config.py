"""Settings for the prototype. Values come from prototype/.env (see .env.example)."""
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROTOTYPE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE_DIR.parent
load_dotenv(PROTOTYPE_DIR / ".env")

# Which AI model to use: "anthropic" for Claude, or "fake" for offline development without a key.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

# 1 = pilot (tiers A and B only). 2 = Phase 2 (adds returns with agent approval).
PHASE = int(os.getenv("PHASE", "1"))

# Fixed "today" so the date rules give the same results as the test plan.
TODAY = date.fromisoformat(os.getenv("TODAY", "2026-10-12"))

# Links the assistant sends instead of taking card details in chat (FR-16, FR-20).
SECURE_PAYMENT_LINK = "https://harborandthread.example/pay"
SECURE_CHECKOUT_LINK = "https://harborandthread.example/checkout"

MOCK_CUSTOMERS_FILE = REPO_ROOT / "tests" / "mock_customers.json"
AUTOMATION_MATRIX_FILE = REPO_ROOT / "docs" / "automation_matrix.csv"
FAQ_FILE = PROTOTYPE_DIR / "data" / "faq.json"
LOG_FILE = PROTOTYPE_DIR / "logs" / "conversations.jsonl"
