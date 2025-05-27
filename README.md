# PCA Visualization Dashboard

An interactive Streamlit dashboard for visualizing PCA (Principal Component Analysis) data with advanced filtering and selection capabilities.

## Features

- 📊 Interactive PCA scatterplot with Plotly
- 🎯 Multiple selection modes (box select, lasso select, point select)
- 🔍 Data filtering and search functionality
- 📋 Data table with export capabilities
- 🔄 Real-time data refresh from MongoDB

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your MongoDB connection by creating a `.env` file:
```
MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=your_database_name
MONGODB_COLLECTION=your_collection_name
```

3. Run the app:
```bash
streamlit run pca_dashboard.py
```

## Data Requirements

Your MongoDB collection should contain documents with at least these fields:
- `Xpca`: X-coordinate for PCA visualization
- `Ypca`: Y-coordinate for PCA visualization

## Deployment

This app is configured for deployment on Streamlit Community Cloud. Make sure to set the environment variables in your Streamlit Cloud settings.
