import sys
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)
import evaluate

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROCESSED_DIR, SAVED_MODELS_DIR, RANDOM_SEED
from utils.logging_config import get_logger

log = get_logger("finetune_bert", "finetune_bert.log")

# 1. Map 5-star ratings to 3 classes (0: Negative, 1: Neutral, 2: Positive)
def map_rating_to_class(rating):
    if rating <= 2: return 0
    elif rating == 3: return 1
    else: return 2

def run():
    log.info("=" * 60)
    log.info("BookMyGig — Fine-Tuning DistilBERT")
    log.info("=" * 60)

    # Load Data
    data_path = PROCESSED_DIR / "reviews_clean.csv"
    df = pd.read_csv(data_path)
    df = df.dropna(subset=['Review_Text', 'Rating'])
    
    # Apply labels
    df['label'] = df['Rating'].apply(map_rating_to_class)
    df['text'] = df['Review_Text'].astype(str)

    # Split into Train and Validation sets
    train_df, val_df = train_test_split(df[['text', 'label']], test_size=0.2, random_state=RANDOM_SEED)
    
    # Convert to Hugging Face Dataset format
    train_dataset = Dataset.from_pandas(train_df, preserve_index=False)
    val_dataset = Dataset.from_pandas(val_df, preserve_index=False)

    # Load Tokenizer & Model
    model_name = "distilbert-base-uncased"
    log.info(f"Downloading base model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=3, # Positive, Neutral, Negative
        id2label={0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"},
        label2id={"NEGATIVE": 0, "NEUTRAL": 1, "POSITIVE": 2}
    )

    # Tokenize the data
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)

    log.info("Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)

    # Setup Evaluation Metric (Accuracy)
    metric = evaluate.load("accuracy")
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return metric.compute(predictions=predictions, references=labels)

    # Training Arguments
    output_dir = SAVED_MODELS_DIR / "distilbert_finetuned"
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3, # 3 epochs is usually the sweet spot for BERT
        weight_decay=0.01,
        load_best_model_at_end=True,
        logging_dir='./logs',
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        compute_metrics=compute_metrics,
    )

    # TRAIN THE MODEL
    log.info("Starting training loop... (This might take a while depending on your hardware)")
    trainer.train()

    # Save the final custom model
    log.info(f"Training complete! Saving custom model to {output_dir}")
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

if __name__ == "__main__":
    run()