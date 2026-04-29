from transformers import AutoTokenizer, AutoModel

model_name = "nlpaueb/legal-bert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

tokenizer.save_pretrained("models/legal_bert")
model.save_pretrained("models/legal_bert")

print("✅ LegalBERT downloaded successfully!")