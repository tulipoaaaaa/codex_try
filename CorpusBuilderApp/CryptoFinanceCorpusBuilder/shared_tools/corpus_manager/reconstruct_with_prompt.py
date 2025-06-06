import json

in_path  = "data/concept_bank_665.jsonl"
out_path = "outputs/v4b_concept_20250506.jsonl"
fixed_out = "outputs/v4b_concept_20250506_with_prompt.jsonl"

with open(in_path, encoding="utf-8") as fin1, \
     open(out_path, encoding="utf-8") as fin2, \
     open(fixed_out, "w", encoding="utf-8") as fout:

    for p_line, c_line in zip(fin1, fin2):
        prompt_obj = json.loads(p_line)
        output_obj = json.loads(c_line)
        output_obj["prompt"] = prompt_obj["prompt"]
        fout.write(json.dumps(output_obj, ensure_ascii=False) + "\n")

print(f"✅ reconstructed {fixed_out}") 