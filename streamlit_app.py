import streamlit as st
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential
import pandas as pd
from io import BytesIO
import os

# Retrieve Azure credentials from environment variables
tenant_id = os.getenv('AZURE_TENANT_ID')
client_id = os.getenv('AZURE_CLIENT_ID')
client_secret = os.getenv('AZURE_CLIENT_SECRET')

credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

# Azure configuration
storage_account_name = "instagramarash"
table_name = "ImageMetadataTableNew"
container_name = "image-metadata"

# Initialize clients
table_service_client = TableServiceClient(
    endpoint=f"https://{storage_account_name}.table.core.windows.net",
    credential=credential
)

blob_service_client = BlobServiceClient(
    account_url=f"https://{storage_account_name}.blob.core.windows.net",
    credential=credential
)

# Load data from Azure Table Storage
@st.cache_data
def load_data():
    table_client = table_service_client.get_table_client(table_name)
    entities = table_client.list_entities()
    data = []
    for entity in entities:
        data.append(entity)
    df = pd.DataFrame(data)
    return df

df = load_data()

# Set page configuration
st.set_page_config(
    page_title="Image Data Explorer",
    layout="wide",
)

st.title("Image Data Explorer")

# Sidebar filters
st.sidebar.header("Filter Data")
categories = df['ImageCategory'].unique()
selected_category = st.sidebar.multiselect(
    "Select Category",
    categories,
    default=categories
)

# Filter dataframe based on selection
filtered_df = df[df['ImageCategory'].isin(selected_category)]

# Display data
st.dataframe(
    filtered_df.reset_index(drop=True),
    width=1000,
    height=500,
)

# Function to get image from Blob Storage
def get_image(blob_url):
    # Extract blob path from URL
    blob_path = blob_url.split(f"{container_name}/")[-1]
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_path
    )
    try:
        stream = blob_client.download_blob()
        image_bytes = stream.readall()
        return image_bytes
    except Exception as e:
        st.error(f"Failed to load image: {e}")
        return None

# Display images
st.subheader("Image Gallery")

cols = st.columns(4)
for index, row in filtered_df.iterrows():
    image_url = row['ImageURL']
    image_bytes = get_image(image_url)
    if image_bytes:
        with cols[index % 4]:
            # Display thumbnail
            st.image(
                image_bytes,
                caption=row['FileName'],
                width=150,
            )
            # Add expander for full-size image
            with st.expander("View Full Image"):
                st.image(
                    image_bytes,
                    caption=row['FileName'],
                    use_column_width=True,
                )

