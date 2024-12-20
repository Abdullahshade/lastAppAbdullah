import streamlit as st
import pandas as pd
from PIL import Image
from github import Github
import os

# Authenticate with GitHub using Streamlit Secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
g = Github(GITHUB_TOKEN)

# Define repository and file paths
REPO_NAME = "Abdullahshade/lastAppAbdullah"  # Replace with your GitHub repository name
FILE_PATH = "GT_Pneumothorax.csv"  # Path to metadata CSV in your GitHub repo
repo = g.get_repo(REPO_NAME)

# Local paths
csv_file_path = FILE_PATH
images_folder = "combined"  # Path to your images folder (update as needed)

# Load metadata (GT_Pneumothorax.csv)
try:
    # Fetch the latest file from the GitHub repository
    contents = repo.get_contents(FILE_PATH)
    with open(csv_file_path, "wb") as f:
        f.write(contents.decoded_content)
    GT_Pneumothorax = pd.read_csv(csv_file_path)
except Exception as e:
    st.error(f"Failed to fetch metadata from GitHub: {e}")
    st.stop()

# App title
st.title("Pneumothorax Grading and Image Viewer with GitHub Integration")

# Initialize session state for the current index
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# Loop to skip labeled images automatically
while st.session_state.current_index < len(GT_Pneumothorax):
    row = GT_Pneumothorax.iloc[st.session_state.current_index]
    if row["Label_Flag"] == 1:
        st.session_state.current_index += 1  # Skip labeled images
    else:
        break

# Ensure there are still images left to process
if st.session_state.current_index >= len(GT_Pneumothorax):
    st.success("All images have been labeled! No more images to process.")
    st.stop()

# Get the current row (image and metadata)
row = GT_Pneumothorax.iloc[st.session_state.current_index]

# Get the current image path (based on Image_Name)
image_path = os.path.join(images_folder, row["Image_Name"])

# Check if the image file exists and display it
if os.path.exists(image_path):
    img = Image.open(image_path)
    st.image(
        img,
        caption=f"Image index: {row['Index']} | Image Name: {row['Image_Name']}",
        use_column_width=True
    )
else:
    st.error(f"Image {row['Image_Name']} not found in {images_folder}.")
    st.stop()

# Handling user input for Pneumothorax type and measurements
pneumothorax_type = st.selectbox("Pneumothorax Type", ["Simple", "Tension"], index=0)

# User input for A, B, and C values (Sum of Interpleural Distances)
A = st.number_input("Enter value for A:", min_value=0, max_value=100, value=0, step=1)
B = st.number_input("Enter value for B:", min_value=0, max_value=100, value=0, step=1)
C = st.number_input("Enter value for C:", min_value=0, max_value=100, value=0, step=1)

# Calculate Pneumothorax Volume Percentage using the formula
pneumothorax_percentage = 4.2 + (4.7 * (A + B + C))
st.write(f"### Calculated Pneumothorax Volume Percentage: {pneumothorax_percentage:.2f}%")

# Save changes button
if st.button("Save Changes"):
    # Update the metadata locally
    GT_Pneumothorax.at[st.session_state.current_index, "Pneumothorax_Type"] = pneumothorax_type
    GT_Pneumothorax.at[st.session_state.current_index, "A"] = A
    GT_Pneumothorax.at[st.session_state.current_index, "B"] = B
    GT_Pneumothorax.at[st.session_state.current_index, "C"] = C
    GT_Pneumothorax.at[st.session_state.current_index, "Pneumothorax_Percentage"] = pneumothorax_percentage
    GT_Pneumothorax.at[st.session_state.current_index, "Label_Flag"] = 1  # Mark as labeled

    # Save the updated CSV locally
    try:
        GT_Pneumothorax.to_csv(csv_file_path, index=False)

        # Push updated metadata to GitHub
        updated_content = GT_Pneumothorax.to_csv(index=False)
        repo.update_file(
            path=contents.path,
            message="Update metadata with pneumothorax grading",
            content=updated_content,
            sha=contents.sha
        )
        st.success(f"Changes saved for Image {row['Image_Name']} and pushed to GitHub!")
    except Exception as e:
        st.error(f"Failed to save changes or push to GitHub: {e}")

# Navigation buttons (Previous / Next)
col1, col2 = st.columns(2)
if col1.button("Previous") and st.session_state.current_index > 0:
    st.session_state.current_index -= 1
if col2.button("Next") and st.session_state.current_index < len(GT_Pneumothorax) - 1:
    st.session_state.current_index += 1
