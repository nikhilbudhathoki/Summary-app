import streamlit as st
import requests
import os
import time
API_KEY = st.secrets["API_KEY"]
API_URL=st.secrets['API_URL']


# Function to call Hugging Face API with retries
def query_huggingface_api(text: str, target_word_count: int, max_retries=3, retry_delay=2):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    # Prepare the payload with input text
    payload = {
        "inputs": text,
        "parameters": {
            "max_length": int(target_word_count * 1.3),  # Ensure this is an integer
            "min_length": max(10, int(target_word_count)),  # Ensure this is an integer
            "num_beams": 2,  # Reduced for speed
            "early_stopping": True,
            "no_repeat_ngram_size": 2,
            "do_sample": False  # More deterministic
        }
    }

    for attempt in range(max_retries):
        try:
            # Send request to Hugging Face API with timeout
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json()[0]["generated_text"]
            elif response.status_code == 503:
                st.warning(f"⚠️ Service temporarily unavailable. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                return f"Error: {response.status_code}, {response.text}"
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ Request failed: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)

    return "Error: Service unavailable after multiple retries. Please try again later."

def main():
    st.title("🇳🇵 Optimized Nepali Summarizer")
    st.markdown("⚡ Efficient news article summarization using Hugging Face API")

    input_text = st.text_area("📝 Enter Nepali news article:", height=250)

    target_word_count = st.slider(
        "📏 Summary Length",
        min_value=20,
        max_value=100,
        value=50,
        step=5
    )

    if st.button("🚀 Summarize"):
        if input_text.strip():
            with st.spinner("⏳ Generating summary..."):
                try:
                    summary = query_huggingface_api(input_text, target_word_count)
                    if not summary.startswith("Error"):
                        st.subheader("📌 Summary")
                        st.text_area("Summarized Text:", summary, height=150)
                        st.info(f"✨ Summary Word Count: {len(summary.split())}")
                    else:
                        st.error(summary)
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")
        else:
            st.warning("⚠️ Please enter some text to summarize.")

if __name__ == "__main__":
    main()
