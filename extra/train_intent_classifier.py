"""
train_intent_classifier.py

Train a multilingual intent classifier using Hugging Face Transformers.
Uses TSV files generated from synthetic data:
   ./hnu-chatbot-project/synthetic_data/en/employee_data.tsv
   ./hnu-chatbot-project/synthetic_data/de/employee_data.tsv

Model: distilbert-base-multilingual-cased (lightweight, multilingual)

Output:
   ./intent_model/  (saved model + tokenizer)
"""

import os
import argparse
import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
import torch

def load_tsv_data(tsv_path):
    """Load TSV with columns: text, label"""
    df = pd.read_csv(tsv_path, sep="\t")
    df = df.dropna()
    return df

def prepare_dataset(df, tokenizer, label2id):
    """Tokenize dataset and encode labels"""
    def tokenize(batch):
        return tokenizer(
            batch["text"], padding="max_length", truncation=True, max_length=128
        )
    dataset = Dataset.from_pandas(df)
    dataset = dataset.map(tokenize, batched=True)
    dataset = dataset.map(lambda x: {"labels": [label2id[l] for l in x["label"]]}, batched=True)
    dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
    return dataset

def main(args):
    # Load data
    en_tsv = os.path.join(args.synthetic_dir, "en", "employee_data.tsv")
    de_tsv = os.path.join(args.synthetic_dir, "de", "employee_data.tsv")

    dfs = []
    if os.path.exists(en_tsv):
        dfs.append(load_tsv_data(en_tsv))
    if os.path.exists(de_tsv):
        dfs.append(load_tsv_data(de_tsv))

    if not dfs:
        raise FileNotFoundError("No TSV files found. Run generate_employee_intent.py first.")

    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(df)} examples across {df['label'].nunique()} intents.")

    # Create label mapping
    labels = sorted(df["label"].unique())
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for label, i in label2id.items()}
    print(f"Labels: {label2id}")

    # Train/test split
    train_df, test_df = train_test_split(df, test_size=0.1, stratify=df["label"], random_state=42)

    # Load tokenizer + model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id
    )

    # Prepare datasets
    train_dataset = prepare_dataset(train_df, tokenizer, label2id)
    test_dataset = prepare_dataset(test_df, tokenizer, label2id)

    # Training args
    training_args = TrainingArguments(
        output_dir=args.out_dir,
        do_train=True,
        do_eval=True,  # ensures evaluation is run
        save_total_limit=2,
        learning_rate=5e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir=os.path.join(args.out_dir, "logs"),
        logging_steps=50
    
    )


    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        tokenizer=tokenizer
    )

    # Train
    trainer.train()

    # Save model
    model.save_pretrained(args.out_dir)
    tokenizer.save_pretrained(args.out_dir)
    print(f"\n✅ Model saved to {args.out_dir}")

    # Evaluate
    metrics = trainer.evaluate()
    print("\n📊 Evaluation metrics:", metrics)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic_dir", type=str, default="./hnu-chatbot-project/synthetic_data", help="Path to synthetic data folder")
    parser.add_argument("--model_name", type=str, default="distilbert-base-multilingual-cased", help="Hugging Face model name")
    parser.add_argument("--out_dir", type=str, default="./intent_model", help="Where to save trained model")
    args = parser.parse_args()
    main(args)
