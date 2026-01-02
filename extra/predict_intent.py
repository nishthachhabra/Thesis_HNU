"""
predict_intent.py

Load the trained multilingual intent classifier from ./intent_model
and predict intents for new queries (English or German).

Usage:
    python predict_intent.py
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

def main():
    model_path = "./intent_model"

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    # Create a text-classification pipeline
    nlp = pipeline("text-classification", model=model, tokenizer=tokenizer, top_k=3)

    print("✅ Model loaded. Type queries to predict intents. Type 'exit' to quit.\n")

    while True:
        query = input("🔎 Query: ").strip()
        if query.lower() in ["exit", "quit"]:
            break

        predictions = nlp(query)
        print("\nTop Predictions:")
        # Access the first (and only) list of predictions for a single query
        for pred in predictions[0]:
            label = pred["label"]
            score = pred["score"]
            print(f"  → {label}: {score:.4f}")
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()