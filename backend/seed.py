"""Insert 20 seed traces distributed across all categories."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from main import SessionLocal, Trace, Base, engine
from datetime import datetime, timezone, timedelta
import uuid

Base.metadata.create_all(bind=engine)
db = SessionLocal()

seeds = [
    ("I was charged twice for my subscription", "Let me look into the duplicate charge on your account.", "Billing", 210),
    ("Can you explain my latest invoice?", "Your latest invoice covers your monthly plan at $29/mo.", "Billing", 185),
    ("Why did my bill go up this month?", "It looks like your plan was upgraded. Let me check.", "Billing", 240),
    ("I see an extra fee on my statement", "That appears to be a processing fee. Let me verify.", "Billing", 195),
    ("I need a refund for the last payment", "I can help process your refund. Let me pull up the transaction.", "Refund", 320),
    ("Please refund my annual subscription", "I'll initiate the refund for your annual plan right away.", "Refund", 290),
    ("I want my money back for this month", "Let me start the refund process for this billing cycle.", "Refund", 305),
    ("Refund me the overcharge please", "I see the overcharge. I'll process the refund now.", "Refund", 275),
    ("I can't log into my account", "Let's reset your password. What email is on the account?", "Account Access", 180),
    ("My password reset email never arrived", "I'll resend the reset link. Please check spam as well.", "Account Access", 165),
    ("I'm locked out after too many attempts", "I've unlocked your account. Try logging in again.", "Account Access", 200),
    ("How do I enable two-factor auth?", "Go to Settings > Security > Enable 2FA.", "Account Access", 150),
    ("I want to cancel my subscription", "I can help you cancel. Your plan will end at the current cycle.", "Cancellation", 260),
    ("Cancel my account immediately", "Your account has been scheduled for cancellation.", "Cancellation", 230),
    ("How do I stop auto-renewal?", "You can turn off auto-renewal in your billing settings.", "Cancellation", 215),
    ("I don't want to continue my plan", "I understand. Let me walk you through the cancellation steps.", "Cancellation", 245),
    ("What features does your platform have?", "We offer invoicing, subscription management, and analytics.", "General Inquiry", 170),
    ("Do you have an API?", "Yes, we have a REST API. Check docs.example.com for details.", "General Inquiry", 155),
    ("What are your business hours?", "Our support team is available Mon–Fri, 9am–6pm EST.", "General Inquiry", 140),
    ("Can I talk to a human agent?", "Sure, I'll transfer you to a live agent shortly.", "General Inquiry", 190),
]

base_time = datetime.now(timezone.utc) - timedelta(hours=20)

for i, (user_msg, bot_resp, cat, ms) in enumerate(seeds):
    trace = Trace(
        id=str(uuid.uuid4()),
        user_message=user_msg,
        bot_response=bot_resp,
        category=cat,
        timestamp=base_time + timedelta(hours=i),
        response_time_ms=ms,
    )
    db.add(trace)

db.commit()
db.close()
print(f"Inserted {len(seeds)} seed traces.")
