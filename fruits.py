import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image, ImageOps

st.set_page_config(page_title="🍏Fruit Classification🍐", layout="centered")

@st.cache_resource
def load_model():
    return tf.keras.models.load_model('fruit_classifier_model.h5')

model = load_model()
class_names = ['Apples', 'Grapes', 'Orange', 'Pineapple', 'Strawberry']

st.title("🍌Fruit Image Classifier")
st.write("Upload an image to classify the fruit.")

file = st.file_uploader("📸 Upload a fruit image", type=["jpg", "jpeg", "png", "bmp"])

def import_and_predict(image_data, model):
    size = model.input_shape[1:3]  # Resize to match model input
    image = ImageOps.fit(image_data, size, Image.LANCZOS)
    img_array = np.asarray(image).astype('float32') / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array)
    return prediction

if file is None:
    st.info("🖼️ Please upload a fruit image to proceed.")
else:
    image = Image.open(file).convert('RGB')
    st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("🔍 Classifying Fruit..."):
        prediction = import_and_predict(image, model)

    predicted_index = int(np.argmax(prediction))
    predicted_class = class_names[predicted_index]
    confidence = round(100 * np.max(prediction), 2)

    st.markdown(f"### 🌈 Predicted Fruit: **{predicted_class}**")
    st.markdown(f"### Confidence Level: **{round(confidence, 2)}**")

    if predicted_class == 'Apples':
        st.warning("🍎 An apple a day, keeps the doctor away.")
    elif predicted_class == 'Grapes':
        st.success("🍇 Grapes are rich in antioxidants, particularly resveratrol, which supports heart and brain health.")
    elif predicted_class == 'Pineapple':
        st.info("🍍 Pineapples are packed with vitamin C and bromelain, aiding immunity and digestion.")
    elif predicted_class == 'Orange':
        st.info("🍊 Oranges are loaded with vitamin C, supporting immune function and skin health.")
    elif predicted_class == 'Strawberry':
        st.info("🍓 Strawberries are low in calories but high in vitamin C, fiber, and powerful antioxidants.")
