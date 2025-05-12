# 🔥 Mount Doom Voice Agent Challenge - AI Transcript Processor

## 🚀 Overview

A scalable LLM-powered system that:

* Streams voice transcripts from Mount Doom API
* Extracts structured data with Gemini
* Performs sentiment and preparedness analysis
* Summarizes the conversation
* Saves results to MongoDB or local JSON
* Submits processed output via API

Designed for resilience, quota fallback, and high throughput.

---

## 🔄 System Architecture

```text
                    +---------------------+
                    |  Mount Doom API     |
                    | (Auth, Stream, Post)|
                    +---------+-----------+
                              |
                        [Auth Token]
                              |
                     +--------v---------+
     +-------------+ |  Stream Listener  | +-------------+
     | Transcripts |--> Async Queue --> |  N Workers    |-->
     +-------------+                   +-------+---------+
                                                |
        +--------------------+------------------+---------------------+
        |                    |                  |                     |
[Gemini Summarizer] [Gemini Extractor] [Gemini Analyzer]    -->    submit_result()
        |                    |                  |
        +-----------> save to MongoDB (or fallback to JSON) <--------+
```

---

## 🔧 How to Run Locally

### 1. Clone the Repo

```bash
git clone https://github.com/YOUR_USERNAME/mount-doom-challenge
cd mount-doom-challenge
```

### 2. Setup Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create `.env` File

```env
GEMINI_API_KEY=your_google_gemini_key
CALLLIVE_API_KEY=candidate-api-key-fff031f8
MONGODB_URI=mongodb+srv://<username>:<userpassword>@cluster0.bzgev.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
USE_MOCK_LLM=true
```

> Set `USE_MOCK_LLM=false` to use real Gemini (limited to 15 req/min). for gemini 1.5 flash and for gemini 2.0 flash we have 30req/min

### 4. Run Mock API Server (Optional)

```bash
python scripts/mock_api.py
```

### 5. Run Main App

```bash
python -m src.app
```

---

## 🔄 Local Data Storage: JSON Fallback

Due to SSL handshake issues with MongoDB Atlas on Windows/Python 3.8, this project uses JSON files to store raw and processed transcripts locally.

```text
📁 raw_transcripts.json     → stores incoming transcript data
📁 processed_results.json   → stores AI-analyzed summaries and insights
```

To enable MongoDB in production, ensure:

* Python >= 3.9
* Proper OpenSSL installation
* Atlas TLS/SSL verified URI

---

## 📁 Folder Structure

```text
src/
├── api/         # API client (auth, stream, submit)
├── processing/  # summarizer.py, extractor.py, analyzer.py
├── queue/       # queue.py with asyncio.Queue
├── storage/     # db.py for MongoDB & JSON fallback
├── app.py       # main orchestrator
scripts/
├── mock_api.py  # local API simulation
```

---

## 🌐 API Endpoints Used

* `POST /api/auth`                         ✅
* `GET /api/v1/transcripts/stream`       ✅
* `POST /api/v1/transcripts/process`     ✅
* `GET /api/v1/stats`                    ✅

---

## 📊 Performance Notes

* Processes up to **10 concurrent transcripts** using asyncio
* Automatically respects Gemini's rate limits with mock fallback
* Can throttle POST rate using `asyncio.Semaphore`

---

## 📄 Dockerfile (Optional)

```dockerfile
FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "-m", "src.app"]
```

---

## 🌟 Key Features

* Robust async pipeline
* LLM prompt engineering
* Gemini API integration
* MongoDB + JSON fallback
* Works offline using mock API

---

## 🚫 Known Limitations

* Gemini quota: 15 req/min
* MongoDB: TLS issues on Windows or Python <3.9
* Uses simplified sentiment scale (0.0 to 1.0)

---

## 📦 Final Notes

This project demonstrates:

* System design for scale and fault tolerance
* LLM integration under constraints
* Clean architecture and modularity


