"""Seed ChromaDB with 30 verified facts and create demo users + sample data."""
import json
from datetime import datetime, timedelta
from database import init_db, db
from auth import hash_password
from rag_engine import add_facts

FACTS = [
    {"claim": "COVID-19 vaccines contain microchips for tracking", "verdict": "FALSE", "explanation": "Vaccines contain mRNA/proteins and adjuvants, not electronic chips. Verified by WHO, ICMR.", "date": "2021-06-12", "category": "Health"},
    {"claim": "Drinking cow urine cures COVID-19", "verdict": "FALSE", "explanation": "No clinical evidence; ICMR & WHO state no proof of cure. Can cause infections.", "date": "2020-04-02", "category": "Health"},
    {"claim": "Eating garlic prevents coronavirus infection", "verdict": "FALSE", "explanation": "WHO: garlic has antimicrobial properties but no evidence it prevents COVID-19.", "date": "2020-03-15", "category": "Health"},
    {"claim": "5G towers spread coronavirus", "verdict": "FALSE", "explanation": "Viruses cannot travel on radio waves. WHO and DoT India confirmed myth.", "date": "2020-04-20", "category": "Technology"},
    {"claim": "Demonetisation eliminated black money in India", "verdict": "MISLEADING", "explanation": "RBI report: 99% of demonetised notes returned. Limited impact on black money.", "date": "2018-08-30", "category": "Finance"},
    {"claim": "EVMs in India can be hacked remotely", "verdict": "FALSE", "explanation": "ECI EVMs are standalone, no networking. Multiple court & expert reviews confirm.", "date": "2019-04-10", "category": "Politics"},
    {"claim": "UNESCO declared 'Jana Gana Mana' best national anthem", "verdict": "FALSE", "explanation": "UNESCO has issued no such ranking. Recurring viral hoax.", "date": "2016-01-26", "category": "Politics"},
    {"claim": "Indian Rs 2000 note has GPS tracking chip", "verdict": "FALSE", "explanation": "RBI confirmed no chip. Withdrawn from circulation in 2023.", "date": "2016-11-12", "category": "Finance"},
    {"claim": "Drinking hot water kills coronavirus", "verdict": "FALSE", "explanation": "WHO: temperature of drinking water has no effect on COVID-19 risk.", "date": "2020-03-25", "category": "Health"},
    {"claim": "Government gives free recharge during lockdown via link", "verdict": "FALSE", "explanation": "Phishing scam; no telecom or government scheme exists.", "date": "2020-04-05", "category": "Finance"},
    {"claim": "Lemon and baking soda cures cancer", "verdict": "FALSE", "explanation": "No peer-reviewed evidence. Tata Memorial & AIIMS warn against it.", "date": "2019-07-01", "category": "Health"},
    {"claim": "PM Kisan scheme gives Rs 6000 per year to eligible farmers", "verdict": "TRUE", "explanation": "Govt of India scheme launched 2019, three installments of Rs 2000.", "date": "2019-02-24", "category": "Politics"},
    {"claim": "GST has only one slab in India", "verdict": "FALSE", "explanation": "India has multiple slabs (0, 5, 12, 18, 28%). GST Council reviews periodically.", "date": "2017-07-01", "category": "Finance"},
    {"claim": "Aadhaar is mandatory to operate a bank account", "verdict": "MISLEADING", "explanation": "SC 2018 ruling: Aadhaar not mandatory for banks; only PAN is required.", "date": "2018-09-26", "category": "Politics"},
    {"claim": "Famous Bollywood actor died (recurring death hoax)", "verdict": "FALSE", "explanation": "Celebrity death hoaxes spread frequently on WhatsApp; verify with verified press.", "date": "2022-08-10", "category": "Entertainment"},
    {"claim": "NASA called Mahabharata war the biggest nuclear war", "verdict": "FALSE", "explanation": "NASA has made no such statement. Recurring hoax.", "date": "2017-05-11", "category": "Religion"},
    {"claim": "Drinking alcohol kills coronavirus inside body", "verdict": "FALSE", "explanation": "WHO: alcohol consumption does NOT kill the virus and increases health risks.", "date": "2020-04-14", "category": "Health"},
    {"claim": "Indian Army uses cow dung bullets", "verdict": "FALSE", "explanation": "Indian Army has issued no such statement; viral satire.", "date": "2021-01-08", "category": "Politics"},
    {"claim": "Mobile radiation causes brain cancer (definitive)", "verdict": "MISLEADING", "explanation": "WHO/IARC: 'possibly carcinogenic'; no definitive proof. Use precaution.", "date": "2019-11-20", "category": "Health"},
    {"claim": "Modi government waived all student loans", "verdict": "FALSE", "explanation": "No such blanket waiver announced. Specific schemes exist for select categories.", "date": "2022-06-15", "category": "Finance"},
    {"claim": "Hindu temples destroyed by Mughals — number 'X' (inflated WhatsApp count)", "verdict": "PARTIALLY TRUE", "explanation": "Temple destruction occurred historically; specific numbers in viral posts often unverified.", "date": "2020-12-05", "category": "Religion"},
    {"claim": "WhatsApp will start charging users monthly", "verdict": "FALSE", "explanation": "WhatsApp remains free for personal use; recurring hoax for years.", "date": "2017-03-19", "category": "Technology"},
    {"claim": "ISRO is the world's most efficient space agency cost-wise", "verdict": "PARTIALLY TRUE", "explanation": "ISRO missions are notably cost-efficient but 'most efficient' depends on metric.", "date": "2014-09-25", "category": "Technology"},
    {"claim": "Voting NOTA above 50% triggers re-election", "verdict": "FALSE", "explanation": "ECI: NOTA has no such legal effect; winner is the candidate with most votes.", "date": "2019-04-22", "category": "Politics"},
    {"claim": "Yoga cures diabetes completely", "verdict": "MISLEADING", "explanation": "Yoga helps manage diabetes; not a cure. Medical treatment essential.", "date": "2018-06-21", "category": "Health"},
    {"claim": "Indian rupee will be replaced by digital currency next month", "verdict": "FALSE", "explanation": "Digital Rupee (CBDC) is a pilot; physical notes remain legal tender.", "date": "2022-12-01", "category": "Finance"},
    {"claim": "Solar eclipse fasting prevents diseases", "verdict": "FALSE", "explanation": "No scientific evidence eclipse changes food safety. AIIMS confirms.", "date": "2019-07-02", "category": "Religion"},
    {"claim": "Ayushman Bharat provides up to Rs 5 lakh health cover per family/year", "verdict": "TRUE", "explanation": "PMJAY scheme provides Rs 5 lakh cover for eligible beneficiaries.", "date": "2018-09-23", "category": "Politics"},
    {"claim": "Drinking 8 glasses of water daily detoxes the body", "verdict": "MISLEADING", "explanation": "Hydration is essential, but kidneys/liver handle 'detox'. No magic threshold.", "date": "2020-02-11", "category": "Health"},
    {"claim": "Tap water in Delhi is unsafe to drink without filtering", "verdict": "PARTIALLY TRUE", "explanation": "Quality varies by area; BIS standards met in many zones; locality testing recommended.", "date": "2019-11-19", "category": "Health"},
]

COMMUNITY_SAMPLES = [
    "Forwarded: 'Govt giving Rs 5000 to all unemployed youth, click link to claim.'",
    "Is it true that mobile flash on eye treats vision problems?",
    "Saw a video saying onions absorb the flu virus from the air.",
    "WhatsApp message: 'Tonight Mars will appear as big as the Moon.'",
    "Claim: drinking turmeric milk every night cures kidney stones.",
    "Forwarded: 'New traffic rule — Rs 25,000 fine for not wearing helmet.'",
    "Is petrol crossing Rs 200 next week per leaked govt circular?",
    "Video shows cyclone hitting Mumbai tomorrow — IMD warning?",
    "Claim: Aadhaar is being deactivated for everyone above 60.",
    "Forwarded: free smartphones for students from PM scheme.",
    "Is it true that boiling water with cloves prevents COVID?",
    "Claim: ATM withdrawals will be limited to Rs 5000 per day.",
    "Forwarded: 'Don't take this medicine, it has been banned globally.'",
    "Astrology predicts a specific date as 'no work' day — accurate?",
    "Claim: Ration cards being cancelled in 7 days unless re-linked.",
]

DEMO_USERS = [
    ("Adil Khan", "adil@demo.com", "demo123", "Both"),
    ("Arif Sheikh", "arif@demo.com", "demo123", "Hindi"),
]

def seed():
    init_db()
    add_facts(FACTS)
    print(f"Seeded {len(FACTS)} facts.")

    with db() as conn:
        user_ids = []
        for name, email, pw, lang in DEMO_USERS:
            row = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if row:
                user_ids.append(row["id"])
                continue
            cur = conn.execute(
                "INSERT INTO users(name,email,password_hash,language) VALUES(?,?,?,?)",
                (name, email, hash_password(pw), lang),
            )
            user_ids.append(cur.lastrowid)
        print(f"Demo users: {user_ids}")

        # 10 sample fact-checks per user
        sample_inputs = [
            ("text", FACTS[0]["claim"]),
            ("whatsapp", "Forwarded as received: " + FACTS[2]["claim"]),
            ("url", "https://example.com/news/" + FACTS[3]["claim"][:30]),
            ("text", FACTS[5]["claim"]),
            ("text", FACTS[7]["claim"]),
            ("whatsapp", FACTS[9]["claim"]),
            ("text", FACTS[11]["claim"]),
            ("text", FACTS[13]["claim"]),
            ("text", FACTS[16]["claim"]),
            ("whatsapp", FACTS[21]["claim"]),
        ]
        for uid in user_ids:
            existing = conn.execute("SELECT COUNT(*) c FROM fact_checks WHERE user_id=?", (uid,)).fetchone()["c"]
            if existing:
                continue
            for i, (typ, txt) in enumerate(sample_inputs):
                fact = FACTS[(i * 2) % len(FACTS)]
                analysis = {
                    "verdict": fact["verdict"],
                    "confidence": 70 + (i * 3) % 25,
                    "summary": fact["explanation"],
                    "evidence_for": [fact["claim"]],
                    "evidence_against": [fact["explanation"]],
                    "context": fact["explanation"],
                    "sources_consulted": ["PIB Fact Check", "WHO India"],
                    "language_detected": "Hinglish" if i % 3 == 0 else "English",
                    "spread_risk": "High" if fact["verdict"] == "FALSE" else "Medium",
                    "recommended_action": "Do not share" if fact["verdict"] == "FALSE" else "Share with caution",
                    "reasoning_steps": ["extract claim", "RAG lookup", "compare", "verdict"],
                }
                created = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT INTO fact_checks(user_id,input_text,input_type,verdict,confidence,analysis_json,created_at) VALUES(?,?,?,?,?,?,?)",
                    (uid, txt, typ, fact["verdict"], analysis["confidence"], json.dumps(analysis), created),
                )
            conn.execute("UPDATE users SET checks_count=? WHERE id=?", (len(sample_inputs), uid))

        # 15 community reports
        existing = conn.execute("SELECT COUNT(*) c FROM community_reports").fetchone()["c"]
        if not existing:
            for i, claim in enumerate(COMMUNITY_SAMPLES):
                uid = user_ids[i % len(user_ids)]
                ai_v = ["FALSE", "MISLEADING", "UNVERIFIABLE", "PARTIALLY TRUE"][i % 4]
                conn.execute(
                    "INSERT INTO community_reports(user_id,claim_text,upvotes,downvotes,ai_verdict) VALUES(?,?,?,?,?)",
                    (uid, claim, 5 + i * 2, i % 4, ai_v),
                )
        print("Sample data ready.")


if __name__ == "__main__":
    seed()
