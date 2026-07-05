import json
import os
import sys

def filter_dataset():
    # Define paths relative to the script's directory for robust execution
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # We allow running the script from either the workspace root or the cinelocalai directory.
    # We check multiple possible relative input paths.
    possible_inputs = [
        os.path.join(script_dir, "data", "adaption_dataset", "indian_movie_dubbing_loc.jsonl"),
        os.path.join(script_dir, "..", "data", "adaption_dataset", "indian_movie_dubbing_loc.jsonl"),
        os.path.abspath("data/adaption_dataset/indian_movie_dubbing_loc.jsonl"),
        os.path.abspath("cinelocalai/data/adaption_dataset/indian_movie_dubbing_loc.jsonl")
    ]
    
    input_path = None
    for p in possible_inputs:
        if os.path.exists(p):
            input_path = p
            break
            
    if not input_path:
        print("Error: Could not find input file indian_movie_dubbing_loc.jsonl in any standard location.", file=sys.stderr)
        print("Expected locations searched:", file=sys.stderr)
        for p in possible_inputs:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)
        
    # Determine correct output path relative to input file's grandparent directory (data/)
    data_dir = os.path.dirname(os.path.dirname(input_path))
    output_dir = os.path.join(data_dir, "gold_dataset")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cinelocalai_gold.jsonl")
    summary_path = os.path.join(os.path.dirname(input_path), "..", "..", "audit_summary.json")
    # Clean up summary path representation
    summary_path = os.path.abspath(summary_path)

    print(f"Reading dataset from: {input_path}")
    print(f"Writing gold dataset to: {output_path}")

    total_rows = 0
    passed_rows = 0
    
    # Track statistics for filtering rules
    stats = {
        "rule_1_domain_movie_dialogue_failed": 0,
        "rule_2_language_pair_invalid_failed": 0,
        "rule_3_source_text_null_failed": 0,
        "rule_4_target_text_null_failed": 0,
        "rule_5_emotion_null_failed": 0,
        "rule_6_intensity_null_failed": 0,
        "rule_7_register_null_failed": 0,
        "rule_8_quality_score_low_failed": 0
    }
    
    # Detail breakdowns of the final gold dataset
    gold_lang_pairs = {}
    gold_emotions = {}
    gold_registers = {}
    gold_quality_scores = {}

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            if not line.strip():
                continue
            total_rows += 1
            
            try:
                row = json.loads(line)
            except Exception as e:
                print(f"Warning: Line {line_num} is not valid JSON and was skipped. Error: {e}", file=sys.stderr)
                continue
            
            # Rule 1: domain == "movie_dialogue"
            domain = row.get("domain")
            if domain != "movie_dialogue":
                stats["rule_1_domain_movie_dialogue_failed"] += 1
                continue
                
            # Rule 2: language_pair in ["en_hi", "en_te"]
            lang_pair = row.get("language_pair")
            if lang_pair not in ["en_hi", "en_te"]:
                stats["rule_2_language_pair_invalid_failed"] += 1
                continue
                
            # Rule 3: source_text not null
            source_text = row.get("source_text")
            if source_text is None:
                stats["rule_3_source_text_null_failed"] += 1
                continue
                
            # Rule 4: target_text not null
            target_text = row.get("target_text")
            if target_text is None:
                stats["rule_4_target_text_null_failed"] += 1
                continue
                
            # Rule 5: emotion not null
            emotion = row.get("emotion")
            if emotion is None:
                stats["rule_5_emotion_null_failed"] += 1
                continue
                
            # Rule 6: intensity not null
            intensity = row.get("intensity")
            if intensity is None:
                stats["rule_6_intensity_null_failed"] += 1
                continue
                
            # Rule 7: register not null
            register = row.get("register")
            if register is None:
                stats["rule_7_register_null_failed"] += 1
                continue
                
            # Rule 8: quality_score >= 4
            quality_score = row.get("quality_score")
            # If missing, it counts as null (failed)
            if quality_score is None:
                stats["rule_8_quality_score_low_failed"] += 1
                continue
            try:
                qs_val = int(quality_score)
                if qs_val < 4:
                    stats["rule_8_quality_score_low_failed"] += 1
                    continue
            except (ValueError, TypeError):
                stats["rule_8_quality_score_low_failed"] += 1
                continue
                
            # If all rules passed, write to output file
            outfile.write(json.dumps(row, ensure_ascii=False) + "\n")
            passed_rows += 1
            
            # Record distribution stats for gold dataset
            gold_lang_pairs[lang_pair] = gold_lang_pairs.get(lang_pair, 0) + 1
            gold_emotions[emotion] = gold_emotions.get(emotion, 0) + 1
            gold_registers[register] = gold_registers.get(register, 0) + 1
            gold_quality_scores[quality_score] = gold_quality_scores.get(quality_score, 0) + 1

    # Create final summary structure
    summary = {
        "dataset_metadata": {
            "input_file": os.path.basename(input_path),
            "output_file": os.path.basename(output_path),
            "total_input_rows": total_rows,
            "total_gold_rows": passed_rows,
            "exclusion_rate_percent": round(((total_rows - passed_rows) / total_rows) * 100, 2) if total_rows > 0 else 0
        },
        "filtering_exclusions": {
            "domain_not_movie_dialogue": stats["rule_1_domain_movie_dialogue_failed"],
            "language_pair_invalid": stats["rule_2_language_pair_invalid_failed"],
            "source_text_missing_or_null": stats["rule_3_source_text_null_failed"],
            "target_text_missing_or_null": stats["rule_4_target_text_null_failed"],
            "emotion_missing_or_null": stats["rule_5_emotion_null_failed"],
            "intensity_missing_or_null": stats["rule_6_intensity_null_failed"],
            "register_missing_or_null": stats["rule_7_register_null_failed"],
            "quality_score_below_4_or_null": stats["rule_8_quality_score_low_failed"]
        },
        "gold_dataset_breakdown": {
            "language_pairs": gold_lang_pairs,
            "emotions": gold_emotions,
            "registers": gold_registers,
            "quality_scores": gold_quality_scores
        }
    }

    # Write summary to audit_summary.json
    with open(summary_path, 'w', encoding='utf-8') as sum_file:
        json.dump(summary, sum_file, indent=2, ensure_ascii=False)
        
    print(f"Summary report written to: {summary_path}")
    print(f"Filtering complete. {passed_rows} of {total_rows} rows passed the filter rules ({passed_rows/total_rows*100:.2f}%).")

if __name__ == "__main__":
    filter_dataset()
