import streamlit as st
import requests
import os
import time
API_KEY = st.secrets["API_KEY"]
API_URL=st.secrets['API_URL']



# Function to call Hugging Face API with retries
def query_huggingface_api(text: str, max_retries=3, retry_delay=2):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Set fixed target word count in the 30-50 range
    target_word_count = 40  # Target middle of 30-50 range
    
    # Prepare the payload with parameters for a shorter summary
    payload = {
        "inputs": text,
        "parameters": {
            "max_length": 60,  # Allow a bit more to get complete sentences
            "min_length": 25,   # A bit lower than our minimum to give flexibility
            "num_beams": 4,     # Good quality
            "early_stopping": True,
            "no_repeat_ngram_size": 3,
            "do_sample": True,
            "top_k": 50,
            "top_p": 0.85,
            "length_penalty": 1.0
        }
    }
    
    for attempt in range(max_retries):
        try:
            # Send request to Hugging Face API
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                generated_text = response.json()[0]["generated_text"]
                
                # Post-process to ensure proper length and ending
                if generated_text:
                    # Split by sentences
                    sentences = generated_text.replace("।", "।|").split("|")
                    
                    # Build summary within 30-50 word range
                    words_so_far = 0
                    final_sentences = []
                    
                    for sentence in sentences:
                        if not sentence.strip():
                            continue
                        
                        sentence_word_count = len(sentence.split())
                        
                        # Add sentence if we're still under the maximum
                        if words_so_far + sentence_word_count <= 50:
                            final_sentences.append(sentence)
                            words_so_far += sentence_word_count
                        else:
                            # Only add if we're below minimum
                            if words_so_far < 30:
                                final_sentences.append(sentence)
                            break
                    
                    summary = "".join(final_sentences)
                    
                    # Ensure summary ends with Nepali sentence ending symbol
                    if not summary.endswith("।"):
                        summary = summary + "।"
                    
                    return summary
                
                return generated_text
            
            elif response.status_code == 503:
                st.warning(f"⚠️ Service temporarily unavailable. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay * (attempt + 1))
            else:
                return f"Error: {response.status_code}, {response.text}"
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ Request failed: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay * (attempt + 1))
    
    return "Error: Service unavailable after multiple retries. Please try again later."

def main():
    st.title("🇳🇵 Nepali Summarizer")
    st.markdown("⚡ Concise news article summarization (30-50 words)")
    
    input_text = st.text_area("📝 Enter Nepali news article:", height=250)
    
    if st.button("🚀 Summarize"):
        if input_text.strip():
            with st.spinner("⏳ Generating summary..."):
                try:
                    summary = query_huggingface_api(input_text)
                    if not summary.startswith("Error"):
                        st.subheader("📌 Summary")
                        st.text_area("Summarized Text:", summary, height=150)
                        word_count = len(summary.split())
                        st.success(f"✨ Summary generated with {word_count} words")
                        
                        # Check if summary is in desired range
                        if word_count < 30 or word_count > 50:
                            st.info("Note: Summary length is outside the 30-50 word target range. This may be due to sentence structure constraints.")
                    else:
                        st.error(summary)
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")
        else:
            st.warning("⚠️ Please enter some text to summarize.")

if __name__ == "__main__":
    main()
