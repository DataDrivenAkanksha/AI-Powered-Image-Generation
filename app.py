import streamlit as st
import requests
import base64
import os

from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
from langchain_groq import ChatGroq

# -------------------------
# Load Environment Variables
# -------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in .env")
    st.stop()

if not OPENROUTER_API_KEY:
    st.error("OPENROUTER_API_KEY not found in .env")
    st.stop()

# -------------------------
# Groq LLM
# -------------------------
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY
)

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(
    page_title="AI Image Generator",
    layout="centered"
)

st.title("🎨 AI-Powered Image Generator")

st.write(
    """
    Enter a simple idea.
    
    Groq will enhance your prompt and Gemini will generate the image.
    """
)

# -------------------------
# Prompt Enhancement
# -------------------------
def enhance_prompt(user_prompt):

    response = llm.invoke(
        f"""
        You are an expert prompt engineer for AI image generation.

        Convert the following idea into a highly detailed image prompt.

        Include:
        - Subject details
        - Environment
        - Composition
        - Camera angle
        - Lighting
        - Colors
        - Artistic style
        - Quality descriptors

        Idea:
        {user_prompt}

        Return only the enhanced prompt.
        """
    )

    return response.content


# -------------------------
# Image Generation
# -------------------------
def generate_image(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "google/gemini-2.5-flash-image",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["text", "image"],
        "max_tokens": 1024
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=300
    )

    return response.json()


# -------------------------
# User Input
# -------------------------
user_prompt = st.text_area(
    "Enter your idea:",
    height=120,
    placeholder="A futuristic city floating above the clouds"
)

enhance = st.checkbox(
    "Enhance Prompt using Groq",
    value=True
)

# -------------------------
# Generate Button
# -------------------------
if st.button("Generate Image 🚀"):

    if not user_prompt:
        st.warning("Please enter a prompt.")
        st.stop()

    final_prompt = user_prompt

    # Prompt Enhancement
    if enhance:

        with st.spinner("Enhancing prompt with Groq..."):

            final_prompt = enhance_prompt(user_prompt)

        st.subheader("✨ Enhanced Prompt")

        st.text_area(
            "Generated Prompt",
            final_prompt,
            height=220
        )

    # Image Generation
    with st.spinner("Generating image..."):

        result = generate_image(final_prompt)

    # Handle Errors
    if "error" in result:

        st.error(result["error"])

    elif result.get("choices"):

        message = result["choices"][0]["message"]

        if message.get("images"):

            image_data = message["images"][0]

            data_url = image_data["image_url"]["url"]

            base64_str = data_url.split(",", 1)[1]

            image_bytes = base64.b64decode(base64_str)

            image = Image.open(BytesIO(image_bytes))

            st.subheader("🖼️ Generated Image")

            st.image(
                image,
                use_container_width=True
            )

            st.download_button(
                label="⬇ Download Image",
                data=image_bytes,
                file_name="generated_image.png",
                mime="image/png"
            )

        else:

            st.warning("No image returned.")

            if message.get("content"):
                st.write(message["content"])

    else:

        st.error("Unexpected response format.")
        st.json(result)