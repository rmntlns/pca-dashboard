# PCA Visualization Dashboard

An interactive Streamlit dashboard for visualizing Q&A chunk usage and retrieval relevance with PCA coordinates.

## Features

### Layout Structure (Top to Bottom)

1. **PCA Scatterplot** - Always visible at top
2. **Date Range Filter** - Controls all data below
3. **Dynamic Content Section** - Changes based on selection state

### PCA Scatterplot

**Color Coding:**
- Dynamic gray-to-green scale based on usage_count
- Gray = 0 retrievals in selected time range
- Bright green = maximum retrievals in selected time range
- Usage count is calculated dynamically by aggregating retrieval_logs for each chunk within the date filter

**Hover Tooltip:**
- Chunk ID
- Usage Count (for selected time range)
- Question (full text)
- Answer (full text)

**Selection:**
- Use existing Plotly box select, lasso select, or point select
- Default Plotly selection styling (no custom highlighting)
- Selection drives the content displayed below

### Date Range Filter

**Position:** Directly below the PCA graph, above the dynamic content section

**Options:**
- Preset buttons: All time (default), Last 24h, Last 7 days, Last 30 days, Last 90 days
- Custom date picker: Select start and end dates

**Behavior:**
- Filters retrieval_logs collection by timestamp
- Recalculates usage_count for each chunk based on filtered logs
- Updates graph colors dynamically
- Updates all metrics and tables below

### Dynamic Content Section

The content below the date filter changes based on selection state:

#### State 1: No Selection
**Display:** Aggregate metrics in collapsible dropdown

**Metrics:**
- Total number of user queries (metric card)
- Average similarity score across all retrievals (metric card)
- Similarity score distribution histogram
  - 5 buckets: 0.9-1.0, 0.8-0.9, 0.7-0.8, 0.6-0.7, <0.6
  - X-axis: score ranges, Y-axis: count of retrievals

**Data source:** All retrieval_logs within selected date range

#### State 2: Multiple Chunks Selected
**Display:** Same aggregate metrics as State 1, calculated only for selected chunks

**Metrics:**
- Same three metrics (queries, avg score, distribution)
- Filtered to only show retrieval_logs where chunk_id matches any selected chunk

#### State 3: Single Chunk Selected
**Display:** Two collapsible sections

**Section 1: Aggregate Metrics (collapsed by default)**
- Same metrics as State 1/2, hidden in dropdown

**Section 2: Chunk Details (expanded by default)**

1. **Chunk Info Card:**
   - Chunk ID
   - Question (full text)
   - Answer (full text)
   - PCA Coordinates (Xpca, Ypca)
   - Lifetime Usage Count (all-time, not filtered by date)

2. **Retrieval Logs Table:**
   - **Columns:** Timestamp, User Query, Similarity Score
   - **Sorting:** Sortable by Timestamp and Similarity Score columns only
   - **Default sort:** Most recent timestamp first
   - **Pagination:** 10 records per page with Previous/Next buttons
   - **Data source:** All retrieval_logs for this chunk_id within selected date range

### Removed Features
- Old records table completely replaced by new dynamic content section
- No CSV download functionality

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure MongoDB connection in `.env` file:
```
MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=your_database_name
MONGODB_COLLECTION=your_collection_name
MONGODB_LOGS_COLLECTION=retrieval_logs
```

3. Run the app:
```bash
streamlit run pca_dashboard.py
```

## Data Requirements

### Chunks Collection
Documents with fields:
- `Xpca` (float): X-coordinate for PCA visualization
- `Ypca` (float): Y-coordinate for PCA visualization
- `id` (string): Chunk identifier (e.g., "qa-8987089672-3")
- `question` (string): Q&A pair question
- `answer` (string): Q&A pair answer
- `usage_count` (int): Lifetime usage count stored in Pinecone (optional, used for chunk info card)

### Retrieval Logs Collection (New)
This is a separate collection that needs to be populated by the n8n workflow.

Documents with fields:
- `chunk_id` (string): Links to chunk `id` in chunks collection
- `user_query` (string): The actual question the user asked that triggered retrieval
- `similarity_score` (float): Similarity score from Pinecone (e.g., 0.868713439)
- `timestamp` (datetime/ISO string): When the retrieval occurred
- `session_id` (string): User session identifier

**Example document:**
```json
{
  "chunk_id": "qa-8987089672-3",
  "user_query": "Can I get a refund on the setup fee?",
  "similarity_score": 0.868713439,
  "timestamp": "2025-12-22T10:14:08.452Z",
  "session_id": "session_abc123"
}
```

### Data Flow
1. n8n workflow retrieves chunks from Pinecone
2. For each retrieved chunk, log a document to `retrieval_logs` collection in MongoDB
3. Dashboard reads chunks collection for coordinates and metadata
4. Dashboard aggregates retrieval_logs by chunk_id to calculate time-based usage_count
5. Graph color scale reflects aggregated usage within selected date range

## User Workflow

### Typical Analysis Flow

1. **Initial View:**
   - User sees PCA graph with all chunks colored by lifetime usage
   - Date filter shows "All time"
   - Aggregate metrics display below showing overall statistics

2. **Time-based Analysis:**
   - User selects "Last 7 days" from date filter
   - Graph colors update to reflect usage in last 7 days only
   - Aggregate metrics recalculate for that period
   - User can identify which chunks are currently popular vs. historically popular

3. **Area Exploration:**
   - User draws box/lasso around cluster of chunks on graph
   - Aggregate metrics update to show statistics for only selected chunks
   - User can compare different regions of the semantic space

4. **Detailed Investigation:**
   - User clicks single chunk to investigate
   - Chunk details appear showing the Q&A content
   - Retrieval logs table shows actual user queries that retrieved this chunk
   - User can sort by similarity score to identify poorly matched retrievals
   - User can paginate through history to see usage patterns

5. **Relevance Assessment:**
   - By comparing user_query to chunk question/answer, user evaluates semantic relevance
   - Low similarity scores indicate potential retrieval quality issues
   - High usage with low similarity suggests chunk needs refinement

## Implementation Notes

### Usage Count Calculation
- **Graph colors:** Calculate usage_count by aggregating retrieval_logs filtered by date range
  - Group by `chunk_id`, count occurrences
  - Join with chunks collection on `id` field
  - Apply gray-to-green color scale where max = highest count in current dataset
  
- **Empty state:** If no retrieval_logs exist for selected time range:
  - All chunks appear gray on graph
  - Aggregate metrics show zeros
  - Display message: "No retrieval logs found for this time period"

### Selection Logic
- Use Plotly's existing selection events (box, lasso, points)
- Track number of selected chunks:
  - 0 selected → State 1 (all data aggregate)
  - 1 selected → State 3 (chunk details)
  - 2+ selected → State 2 (filtered aggregate)

### Performance Considerations
- Cache chunks collection data (coordinates change infrequently)
- Query retrieval_logs with date range filter and chunk_id filter as needed
- For single chunk details: limit initial query to 10 records, implement server-side pagination
- Consider indexing: `chunk_id` and `timestamp` in retrieval_logs collection

### Empty States
- No chunks in collection: Show error message
- No retrieval logs: Show graph with all gray points, metrics with zeros
- Single chunk with no logs: Show chunk info card, display "No retrievals found" in table
- Date range with no data: Update colors to all gray, show empty metrics

## Deployment

Configure environment variables in Streamlit Community Cloud settings.
