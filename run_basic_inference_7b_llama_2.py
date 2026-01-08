from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

model_id = "meta-llama/Llama-2-7b-hf"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=True)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype="auto")

# Create text generation pipeline
llama_pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Run inference
prompt = "Explain the theory of relativity in simple terms."
outputs = llama_pipe(prompt, max_new_tokens=100, do_sample=True, temperature=0.7)
print(outputs[0]["generated_text"])
