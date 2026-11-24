"""Phase 2: Generate Banking Intent Dataset for MuRIL Fine-tuning.

Defines 15 banking intents, generates Devanagari Hindi, romanized Hinglish,
and English examples using Groq/Sarvam LLM (or high-quality seed bank),
and applies common.py's augment() to produce banking_train.csv and banking_labels.json.
"""
import os
import sys
import json
import argparse
import random
from pathlib import Path
import pandas as pd

# Add current directory to path to import common.py
sys.path.insert(0, str(Path(__file__).parent))
from common import augment, is_dev, romanize, light, chatify

BANKING_INTENTS = [
    "apply_card",
    "check_eligibility",
    "give_income",
    "give_pan",
    "give_dob",
    "ask_documents",
    "ask_fees",
    "compare_cards",
    "consent_yes",
    "consent_no",
    "ask_status",
    "talk_to_human",
    "greeting",
    "ask_card_benefits",
    "out_of_scope",
]

# High-quality seed examples for each of the 15 banking intents
SEED_EXAMPLES = {
    "apply_card": [
        "mujhe credit card apply karna hai", "credit card chahiye online", "naya card lene ka process kya hai",
        "i want to apply for a credit card", "how can i get a new credit card", "card application start karo",
        "क्रेडिट कार्ड के लिए आवेदन करना है", "नया क्रेडिट कार्ड कैसे मिलेगा", "मुझे कार्ड चाहिए",
        "please apply credit card for me", "can i get an unsecured card", "credit card form open karo",
    ],
    "check_eligibility": [
        "meri eligibility check kar lo", "kya mujhe card mil sakta hai", "cibil score check karke batao",
        "check my credit card eligibility", "am i eligible for millenia card", "mera cibil 750 hai eligible hoon kya",
        "मेरी पात्रता चेक करें", "क्या मैं इस कार्ड के लिए योग्य हूँ", "एलिजिबिलिटी कैसे चेक होगी",
        "bureau check run karo", "score safe soft check kijiye", "check if i qualify for infinia",
    ],
    "give_income": [
        "meri monthly salary 65000 hai", "in-hand 85000 aati hai account mein", "income 1.4 lakh per month",
        "my monthly income is 50000", "i earn 70k every month", "monthly inhand 25000 salary hai",
        "मेरी मासिक आय 60000 रुपये है", "महीने की सैलरी 80 हजार है", "कमाई 45000 प्रति माह है",
        "salary account icici mein hai 75k credit hota hai", "net income 110000", "earning 90000 per month",
    ],
    "give_pan": [
        "mera pan card number ABCDE1234F hai", "pan number note kar lo", "here is my pan number",
        "my pan is BKZPS8792K", "pan card details share kar raha hoon", "ye lo mera pan card",
        "मेरा पैन कार्ड नंबर नोट करें", "पैन नंबर दे रहा हूँ", "पैन कार्ड संख्या",
        "pan details verified", "pan card upload kar diya", "enter pan number",
    ],
    "give_dob": [
        "meri date of birth 15 august 1995 hai", "dob 12/04/1998", "born on 22nd march 2000",
        "janm tithi 10 january 1992", "my birth date is 5 november", "dob is 18-09-1996",
        "मेरी जन्म तिथि 15 अगस्त 1995 है", "जन्म दिनांक", "जन्मतिथि",
        "28 years old born in 1996", "birthdate note kijiye", "dob share kar diya",
    ],
    "ask_documents": [
        "kya documents upload karne padenge", "documents kya lagenge card ke liye", "salary slip upload karni hai kya",
        "what documents are required for application", "do i need to submit payslips", "aadhaar aur pan lagega kya",
        "क्या दस्तावेज आवश्यक हैं", "सैलरी स्लिप चाहिए क्या", "कौन से कागज लगेंगे",
        "is itr mandatory", "bank statement upload karna padega kya", "document checklist batao",
    ],
    "ask_fees": [
        "annual fee kitni hai is card ki", "joining charges kya hain", "card free hai ya chargeable",
        "what is the annual fee of regalia card", "is there any joining fee", "charges kitne lagenge",
        "सालाना फीस कितनी है", "कार्ड का शुल्क क्या है", "कोई जॉइनिंग चार्ज है क्या",
        "renewal fee waiver condition kya hai", "hidden charges toh nahi hain", "annual maintenance charges",
    ],
    "compare_cards": [
        "infinia aur regalia mein kya farak hai", "compare millennia vs moneyback", "kaun sa card best hai",
        "which card is better for travel and lounge", "compare rewards points between cards", "difference batao",
        "दोनों कार्ड्स में क्या अंतर है", "कौन सा क्रेडिट कार्ड बेहतर है", "कार्ड तुलना करें",
        "fuel spends ke liye kaun sa sahi rahega", "cashback vs rewards comparison", "suggest best card for me",
    ],
    "consent_yes": [
        "haan mujhe manzoor hai", "yes I agree", "proceed kijiye", "haan consent deta hoon",
        "i authorize bureau pull", "yes agree with terms and conditions", "theek hai aage badho",
        "हाँ मैं सहमत हूँ", "हाँ आगे बढ़ें", "स्वीकार है",
        "yes confirm my application", "ok proceed with verification", "ha accept karta hoon",
    ],
    "consent_no": [
        "nahi mujhe nahi chahiye", "no i do not agree", "cancel kar do application", "mana karta hoon",
        "stop the process", "consent deny karta hoon", "nahi lena card abhi",
        "नहीं मुझे नहीं चाहिए", "रद्द करें", "अस्वीकार है",
        "don't pull my bureau score", "reject this offer", "nahi karna proceed",
    ],
    "ask_status": [
        "meri application ka status kya hai", "track my credit card status", "card kab tak deliver hoga",
        "check application status reference number", "dispatch hua kya card mera", "kahan tak pahunchi application",
        "मेरे आवेदन की स्थिति क्या है", "कार्ड कब तक आएगा", "स्टेटस चेक करें",
        "tracking id share karo", "is my card approved yet", "approval status check karke batao",
    ],
    "talk_to_human": [
        "customer care agent se baat karao", "i want to speak to a human representative", "executive ko connect karo",
        "bank representative se call schedule karo", "human agent se baat karni hai", "connect to customer support",
        "कस्टमर केयर से बात करवाएं", "अधिकारी से बात करनी है", "सपोर्ट टीम से बात कराओ",
        "transfer to live agent", "call me back from bank", "representative chahiye",
    ],
    "greeting": [
        "namaste", "hello", "hi there", "good morning", "kese ho bhai", "namaskar",
        "नमस्ते", "प्रणाम", "शुभ प्रभात", "हेलो",
        "hey assistant", "hi kaise ho", "sat sri akal",
    ],
    "ask_card_benefits": [
        "is card ke fayde kya hain", "airport lounge access free hai kya", "cashback kitna milega online spends par",
        "what are the key benefits and reward points", "fuel surcharge waiver milega", "movie ticket discounts hain kya",
        "इस कार्ड के क्या लाभ हैं", "लाउंज एक्सेस मिलेगा क्या", "कैशबैक कितना है",
        "welcome voucher kya milega", "features aur rewards details batao", "what perks are included",
    ],
    "out_of_scope": [
        "aaj delhi ka mausam kaisa hai", "kal subah 7 baje alarm lagao", "arijit singh ke gaane chalao",
        "dominos se pizza order karo", "what is the weather forecast tomorrow", "play rock music",
        "आज मौसम कैसा रहेगा", "अलार्म लगाओ", "गाना चलाओ", "खाना आर्डर करो",
        "who is the prime minister of india", "bhai volume kam karo", "joke sunao koi achha sa",
    ],
}


def expand_with_llm(intent: str, seeds: list, n_target: int = 50, provider: str = "groq") -> list:
    """Use configured LLM to generate diverse Hinglish / Hindi / English phrases."""
    api_key = os.environ.get("GROQ_API_KEY") if provider == "groq" else os.environ.get("SARVAM_API_KEY")
    if not api_key:
        return []

    import urllib.request
    prompt = (
        f"Generate {n_target} realistic, diverse user utterances for a banking voice assistant intent: '{intent}'.\n"
        f"Format: exactly one utterance per line, no numbering, no quotes.\n"
        f"Include a balanced mix of:\n"
        f"1. Natural romanized Hinglish (e.g. casual texting, 'bhai limit kitni milegi', 'salary verify kar lo')\n"
        f"2. Devanagari Hindi (e.g. 'क्रेडिट कार्ड के नियम बताएं')\n"
        f"3. Plain English\n"
        f"Reference seeds:\n" + "\n".join(seeds[:5])
    )

    try:
        if provider == "groq":
            req_body = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 1200,
            }
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(req_body).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                lines = data["choices"][0]["message"]["content"].splitlines()
                return [line.strip().strip("- ") for line in lines if len(line.strip()) > 3]
    except Exception as e:
        print(f"LLM generation warning for {intent}: {e}")
        return []
    return []


def build_banking_dataset(output_dir: Path, target_per_intent: int = 150):
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows = []

    print(f"Generating Phase-2 Banking Intent Dataset for {len(BANKING_INTENTS)} intents...")

    provider = os.environ.get("LLM_PROVIDER", "groq").lower()

    for intent in BANKING_INTENTS:
        seeds = SEED_EXAMPLES.get(intent, ["apply for credit card"])
        generated = []
        
        # Try LLM expansion if API key exists
        if os.environ.get("GROQ_API_KEY") or os.environ.get("SARVAM_API_KEY"):
            generated = expand_with_llm(intent, seeds, n_target=60, provider=provider)
        
        # Combine seeds and generated
        combined = list(set(seeds + generated))
        
        # Synthetic variation generation if needed to hit target
        rng = random.Random(42)
        variations = []
        for text in combined:
            variations.append(text)
            if not is_dev(text):
                variations.append(chatify(text, rng))
                variations.append(light(text))

        selected = list(set(variations))
        for text in selected:
            all_rows.append({"query_text": text, "target": intent})
        print(f"  - Intent '{intent:20s}': {len(selected)} base utterances")

    base_df = pd.DataFrame(all_rows)
    base_df["roman"] = ~base_df.query_text.map(is_dev)

    # Apply common.py augment()
    print("Applying common.py augment() (Devanagari romanization + chatify + permutations)...")
    augmented_df = augment(base_df, seed=42, chat=True)

    csv_path = output_dir / "banking_train.csv"
    augmented_df.to_csv(csv_path, index=False)
    print(f"Saved augmented dataset: {csv_path} ({len(augmented_df)} rows)")

    # Save labels.json
    labels_path = output_dir / "banking_labels.json"
    labels_data = {
        "note": "15 banking intents for Credit Card Onboarding MuRIL model.",
        "names": BANKING_INTENTS,
    }
    labels_path.write_text(json.dumps(labels_data, indent=2), encoding="utf-8")
    print(f"Saved labels mapping: {labels_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate banking intent training dataset")
    parser.add_argument("--out", type=str, default=str(Path(__file__).parent), help="Output directory")
    args = parser.parse_args()
    build_banking_dataset(Path(args.out))
