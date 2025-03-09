import streamlit as st
import re

# Improved sentence extraction with focus on key details
def extract_important_sentences(text, num_sentences=5):
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(।)', text)
    processed_sentences = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sent = (sentences[i] + sentences[i+1]).strip()
            if sent:
                processed_sentences.append(sent)
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        processed_sentences.append(sentences[-1].strip() + "।")
    
    if not processed_sentences:
        return []
    
    if len(processed_sentences) <= num_sentences:
        return [s.rstrip("।") for s in processed_sentences]
    
    # Enhanced scoring: position, length, and detail richness
    scores = []
    all_words = text.split()
    total_words = len(all_words)
    for i, sentence in enumerate(processed_sentences):
        words = sentence.split()
        word_count = len(words)
        
        # Position: Start and end for context and conclusion
        position_score = 1.0 if i < 2 or i > len(processed_sentences) - 3 else 0.8 - 0.6 * (i / len(processed_sentences))
        
        # Length: Favor 8-18 words for clarity and info
        length_score = 0.5 if word_count < 8 else (0.6 if word_count > 18 else 1.0)
        
        # Detail richness: Prioritize sentences with numbers, rare words, or specific terms
        unique_words = set(words)
        has_numbers = any(any(char.isdigit() for char in w) for w in words)
        rarity_score = sum(1 for w in unique_words if all_words.count(w) < 3) / max(1, len(unique_words))
        detail_score = (1.5 if has_numbers else 1.0) * (len(unique_words) / max(1, word_count)) * rarity_score
        
        total_score = 0.35 * position_score + 0.25 * length_score + 0.4 * detail_score
        scores.append((sentence, total_score, i))
    
    # Select top-scoring sentences and maintain order
    scores.sort(key=lambda x: x[1], reverse=True)
    selected_sentences = scores[:num_sentences]
    selected_sentences.sort(key=lambda x: x[2])  # Keep narrative flow
    return [s[0].rstrip("।") for s in selected_sentences]

# Summarization function for clear, point-rich output
def generate_summary(text):
    st.info("Extracting key sentences...")
    important_sentences = extract_important_sentences(text, num_sentences=5)
    
    if not important_sentences:
        st.warning("No key sentences extracted. Using fallback.")
        return extractive_fallback(text)
    
    extraction = " ".join(s.strip() for s in important_sentences if s.strip())
    if not extraction:
        st.warning("Extraction empty. Using fallback.")
        return extractive_fallback(text)
    
    st.info("Generating final summary...")
    final_summary = adjust_to_target_length(extraction, text)
    
    final_summary = re.sub(r'\s+', ' ', final_summary.strip()).rstrip("।") + "।"
    return final_summary

# Enhanced fallback for capturing more points
def extractive_fallback(text, target_min=60, target_max=80):
    sentences = [s.strip() for s in re.split(r'(।)', text) if s.strip()]
    if not sentences:
        return text[:target_max] + "।"
    
    cleaned_sentences = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sent = (sentences[i] + sentences[i+1]).strip()
            if sent:
                cleaned_sentences.append(sent)
    if len(sentences) % 2 == 1:
        cleaned_sentences.append(sentences[-1] + "।")
    
    if not cleaned_sentences:
        return text[:target_max] + "।"
    
    # Score sentences with detail focus
    scores = []
    all_words = text.split()
    for i, sentence in enumerate(cleaned_sentences):
        words = sentence.split()
        word_count = len(words)
        position_score = 1.0 if i < 2 or i > len(cleaned_sentences) - 2 else 0.8 - 0.6 * (i / len(cleaned_sentences))
        length_score = 0.5 if word_count < 8 else (0.6 if word_count > 18 else 1.0)
        has_numbers = any(any(char.isdigit() for char in w) for w in words)
        unique_words = set(words)
        rarity_score = sum(1 for w in unique_words if all_words.count(w) < 3) / max(1, len(unique_words))
        detail_score = (1.5 if has_numbers else 1.0) * (len(unique_words) / max(1, word_count)) * rarity_score
        total_score = 0.35 * position_score + 0.25 * length_score + 0.4 * detail_score
        scores.append((sentence.rstrip("।"), total_score, i))
    
    # Select and spread points
    scores.sort(key=lambda x: x[1], reverse=True)
    top_sentences = scores[:5]
    top_sentences.sort(key=lambda x: x[2])
    result = [s[0] for s in top_sentences]
    words_count = len(" ".join(result).split())
    total_sentences = len(cleaned_sentences)
    
    # Ensure broader coverage if too short
    if words_count < target_min and len(result) < total_sentences:
        used_indices = {s[2] for s in top_sentences}
        spread_indices = [total_sentences // 5, 2 * total_sentences // 5, 3 * total_sentences // 5, 4 * total_sentences // 5]
        for idx in spread_indices:
            if idx < total_sentences and idx not in used_indices and words_count < target_max:
                result.append(cleaned_sentences[idx].rstrip("।"))
                words_count += len(cleaned_sentences[idx].split())
                used_indices.add(idx)
    
    # Trim if too long
    while words_count > target_max and len(result) > 1:
        result.pop()
        words_count = len(" ".join(result).split())
    
    return " ".join(result) + "।"

# Adjust summary to 60-80 words
def adjust_to_target_length(summary, original_text, target_min=60, target_max=80):
    word_count = len(summary.split())
    if target_min <= word_count <= target_max:
        return summary
    return extractive_fallback(original_text)

def main():
    st.title("🇳🇵 Nepali Summarizer")
    st.markdown("⚡ Meaningful news article summarization (60-80 words)")
    
    input_text = st.text_area("📝 Enter Nepali news article (200-350 words):", height=250)
    
    if st.button("🚀 Summarize"):
        if not input_text.strip():
            st.warning("⚠️ Please enter some text to summarize.")
            return
            
        with st.spinner("⏳ Generating summary..."):
            try:
                summary = generate_summary(input_text)
                
                st.subheader("📌 Summary")
                st.text_area("Summarized Text:", summary, height=150)
                
                word_count = len(summary.split())
                st.success(f"✨ Summary generated with {word_count} words")
                
                if word_count < 60 or word_count > 80:
                    st.info("Note: Summary length adjusted to 60-80 words.")
            
            except Exception as e:
                st.error(f"⚠️ Error: {e}")
                st.subheader("📌 Fallback Summary")
                fallback_summary = extractive_fallback(input_text)
                st.text_area("Summarized Text:", fallback_summary, height=150)
                st.warning("Used fallback method due to error.")

if __name__ == "__main__":
    main()
