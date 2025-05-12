# mount-doom-challenge
founding-engineer-hiring-challenege

### 🔄 Local Data Storage: JSON Fallback

Due to SSL handshake issues with MongoDB Atlas on Windows/Python 3.8, this project uses JSON files to store raw and processed transcripts locally.

- `raw_transcripts.json` — stores incoming transcript data
- `processed_results.json` — stores AI-analyzed summaries and insights

To enable MongoDB in production, ensure:
- Python >= 3.9
- Proper OpenSSL installation
- Atlas TLS/SSL verified URI
