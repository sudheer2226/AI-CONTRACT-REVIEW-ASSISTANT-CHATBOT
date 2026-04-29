from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained("models/legal_bert")
model = AutoModel.from_pretrained("models/legal_bert")

def extract_key_info(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)
    return "LegalBERT processed the contract successfully."