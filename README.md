# subcontractor_research_system
 A subcontractor research system that automates finding and ranking mechanical contractors based on the specified criteria.

# Subcontractor Research API

This FastAPI application automates the discovery, analysis, and ranking of subcontractors based on specified criteria.

## Features

- **Web Discovery**: Find potential subcontractors based on trade, location, and keywords
- **Profile Extraction**: Extract key business information from contractor websites
- **License Verification**: Check license status with state regulatory bodies
- **Project History Analysis**: Identify relevant projects and experience
- **Scoring and Ranking**: Rank contractors based on relevance to project needs



### Prerequisites:

- Python 3.8+
- Docker (optional)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/subcontractor-research-api.git
   cd subcontractor-research-api
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create configuration:
   ```
   cp .env.example .env
   ```

5. Edit `.env` file to add your API keys

### Running the API

#### Using Python directly:

```
uvicorn main:app --reload
```

#### Using Docker:

```
docker build -t subcontractor-research .
docker run -p 8000:8000 --env-file .env subcontractor-research
```

## API Usage

### Submit a Research Job

**Endpoint**: `POST /research-jobs`

**Request Body**:
```json
{
  "trade": "mechanical",
  "city": "Austin",
  "state": "TX",
  "min_bond": 5000000,
  "keywords": ["hotel", "commercial"]
}
```

**Response**:
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "QUEUED"
}
```

### Check Job Status & Get Results

**Endpoint**: `GET /research-jobs/{job_id}`

**Response** (when complete):
```json
{
  "status": "SUCCEEDED",
  "results": [
    {
      "name": "XYZ Mechanical Contractors",
      "website": "https://xyzmech.com",
      "email": "info@xyzmech.com",
      "phone_number": "(512) 555-1234",
      "city": "Austin",
      "state": "TX",
      "lic_active": true,
      "lic_number": "TX12345678",
      "bond_amount": 6000000,
      "tx_projects_past_5yrs": 4,
      "score": 92,
      "evidence_url": "https://xyzmech.com/about",
      "evidence_text": "Bonded up to $6 million. Projects include Hilton Austin, 2022...",
      "last_checked": "2025-05-05T12:34:56"
    },
    ...
  ]
}
```

## Sample Client Usage

A sample client script is included to demonstrate API usage:

```
python sample_client.py --trade mechanical --city Austin --state TX --min-bond 5000000 --keywords hotel commercial
```

## Implementation Notes

This system follows requirements for the subcontractor research tool:

1. **Web Discovery (F-1)**: Uses search APIs and web scraping to identify ≥20 candidate companies
2. **Profile Extraction (F-2)**: Extracts key business information from candidate websites
3. **License Check (F-3)**: Verifies license status using regulatory databases
4. **Project History (F-4)**: Analyzes project details to identify relevant experience
5. **Scoring & Ranking (F-5)**: Scores candidates on relevant factors to produce the final list

### LLM Usage Policy

This implementation carefully follows the LLM policy:
- LLMs are NOT used to generate lists of subcontractors
- LLMs are ONLY used after raw HTML/JSON is fetched to:
  1. Extract structured fields from noisy HTML
  2. Normalize text representations (e.g., "five million" → 5,000,000)
  3. Perform lightweight semantic classification

Every returned contractor includes verifiable `evidence_url` and `evidence_text` fields.

## License

MIT
