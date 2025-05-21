import streamlit as st
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image

# Load the trained model
model = load_model('fruit_classifier_model.keras')

# Define class names and corresponding emojis
class_names = ['apple', 'banana', 'mango', 'orange', 'strawberry']
class_emojis = {
    'apple': '🍎',
    'banana': '🍌',
    'mango': '🥭',
    'orange': '🍊',
    'strawberry': '🍓'
}

# Set up Streamlit app
st.title("🍎🍌🍊 Fruit Image Classifier")
st.write("Upload an image of a fruit.")

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the uploaded image
    img = Image.open(uploaded_file)
    st.image(img, caption='Uploaded Image.', use_column_width=True)

    # Preprocess the image
    img = img.resize((128, 128))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # Make prediction
    prediction = model.predict(img_array)
    predicted_class = class_names[np.argmax(prediction)]
    confidence = np.max(prediction) * 100
    emoji = class_emojis.get(predicted_class, '')

    # Display prediction
    st.markdown(f"### 🧠 Prediction: **{predicted_class.capitalize()} {emoji}**")
    st.markdown(f"**Confidence:** {confidence:.2f}%")
