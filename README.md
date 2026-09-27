# PDF Study Assistant - Muhammad Danyal's learning project

A complete local Python app for asking questions about one PDF. Read the comments in `app.py` and `rag.py`: each meaningful executable line has a plain-English explanation. Read `WORKFLOW_GUIDE.md` for the overall design and `LINE_BY_LINE_GUIDE.md` for an indexed explanation of the source files.

## Start here on Windows

1. Install **64-bit Python 3.11 or 3.12** from https://www.python.org/downloads/. Enable Add Python to PATH if the installer offers it.
2. **Extract the ZIP completely**. Do not run scripts inside the ZIP viewer.
3. Open the extracted `pdf-chatbot` folder in Antigravity. Antigravity is an editor; the app also works without it.
4. Double-click `setup_windows.bat`. It creates `.venv`, installs the core packages, and creates `.env` without overwriting an existing file. Internet is needed for package installation.
5. Double-click `run_windows.bat`. Keep the terminal open while using the app.
6. Open http://127.0.0.1:8501 if a browser tab does not open automatically.
7. Leave **Use the included sample PDF** checked, keep **Keyword (easy start)** and **Search passages only**, and click **Process PDF**.
8. Ask **What is overfitting?** Open the matching source passage; it should reference physical PDF page 2.
9. Untick the sample option to upload your own PDF. Click Process PDF again.
10. Stop the app with Ctrl+C in its terminal.

No API key is needed for this first run. Search mode shows passages, not a generated AI answer. Once dependencies are installed, keyword search works offline.

### Manual Windows commands

Open a terminal inside the extracted project folder and run each line separately:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Copy `.env.example` only if `.env` does not already exist. If `python` is not found, use `py -3 -m venv .venv` for the first command. Directly invoking the environment's Python avoids PowerShell activation-policy problems.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp -n .env.example .env
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

## Turn on generated answers

1. Sign in to https://platform.openai.com/ and configure API billing/access if needed. ChatGPT Plus does not supply this app with API credits.
2. Create an API key in your project. Do not paste it into the chat or source code.
3. Edit your local `.env` file in Antigravity. Set `OPENAI_API_KEY` to your real key and `OPENAI_MODEL` to a Responses-compatible text model available to your API project. No model is preselected because availability and price vary by account.
4. Save the file, stop the app, and run it again. Environment variables already set in your terminal take priority over `.env`.
5. Process a PDF. Select **Generate answer with OpenAI** and check the model ID in the sidebar.
6. Ask a question. The app retrieves up to four passages, sends them with your question to the API, and displays the answer plus the original source passages.

Example `.env` structure (replace the placeholder text locally):

```dotenv
OPENAI_API_KEY=your_real_key
OPENAI_MODEL=your_available_text_model_id
```

Only your question and retrieved text excerpts are sent to OpenAI, not the entire PDF file. The API call uses `store=False`; that setting does not mean every type of provider retention is disabled. Your API key is never shown by the interface. `.env` is excluded from Git by `.gitignore`.

## Turn on semantic search: Hugging Face + FAISS

The first-run keyword backend keeps setup smaller and makes it easy to inspect retrieval. Semantic search adds the embedding workflow discussed in your learning plan; it can match related meanings with different wording.

Stop the app, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-semantic.txt
```

For macOS/Linux use `.venv/bin/python` instead. Restart the app, choose **Semantic (optional)**, and click **Process PDF**. The first run downloads `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face. Allow time, internet access, and disk space for PyTorch and model dependencies. It runs on CPU; no GPU is required. Models are cached outside this project by Hugging Face. Subsequent processing can use the cached model offline.

The same embedding model encodes both the chunks and questions. FAISS stores vectors in memory and finds nearby vectors. This is local embedding/search, with no embedding API charge. Generated OpenAI answers still use the API. Switching backends clears the previous index and answers, so process the PDF again.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit interface, buttons, messages, session state, friendly errors |
| `rag.py` | PDF reading, chunking, keyword/semantic indexing, retrieval, OpenAI generation |
| `requirements.txt` | Core dependencies for the first run |
| `requirements-semantic.txt` | Optional local embeddings and FAISS dependencies |
| `.env.example` | Empty API-settings template |
| `.gitignore` | Excludes secrets, virtual environment, and Python cache files |
| `.streamlit/config.toml` | Upload limit, theme, and Streamlit telemetry setting |
| `setup_windows.bat` | Creates the environment and installs core packages |
| `run_windows.bat` | Starts the app on your local computer |
| `sample_documents/machine_learning_notes.pdf` | Three-page selectable-text practice PDF |
| `WORKFLOW_GUIDE.md` | Concept explanations and a worked example |
| `LINE_BY_LINE_GUIDE.md` | Line-numbered source explanations |
| `tests/test_workflow.py` | Local tests for PDF parsing, retrieval, grounding payload, and errors |
| `tests/test_app.py` | Streamlit checks for processing, questions, and stale-index clearing |
| `VALIDATION.md` | What was actually tested and the remaining limitations |

## Test your installation

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests do not use a paid API or download a model. The FAISS test runs only if its optional dependencies are installed and uses deterministic test vectors. Real-model semantic checks are described separately in VALIDATION.md.

Manual practice with the included PDF:

| Question | Expected source/result |
| --- | --- |
| What is supervised learning? | Page 1 |
| What is classification? | Page 1 |
| What is overfitting? | Page 2 |
| What is the purpose of a test set? | Page 2 |
| What is precision? | Page 3 |
| What is the admission deadline for AWKUM? | No supported answer; generated mode should admit missing evidence |
| Who is the president of Pakistan? | No supported answer in the PDF |

Keywords may still retrieve unrelated chunks for an unanswerable question. Retrieval ranks similarity; it does not certify answerability. Inspect passages and check whether generated mode refuses unsupported answers.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Python not found | Install 64-bit Python 3.11/3.12 and reopen the terminal; try `py -3` |
| Package installation fails | Read the first error; check internet, Python version, and free disk space; rerun setup |
| `No module named ...` | Use the project's `.venv` Python, not a different Python installation |
| Browser did not open | Visit http://127.0.0.1:8501 while the run script is active |
| Port already in use | Stop the other app or add `--server.port 8502` to the run command |
| No readable text | Use a selectable-text PDF; scans require OCR, which this project does not implement |
| Some pages skipped | Those pages have no extractable text; use a text version if the missing material matters |
| Model download fails | Use Keyword search or fix access to Hugging Face and retry |
| SOCKS proxy / socksio error | If your network uses a SOCKS proxy, run the environment Python with `-m pip install "httpx[socks]"` |
| API authentication error | Check `.env`, remove accidental spaces, and restart the app |
| API quota/rate error | Check API billing, balance, and usage limits; ChatGPT payment is separate |
| Model error | Choose a model your API project can access and that supports Responses text generation |
| Unhelpful search results | Inspect extracted text and chunks; try semantic search or a more specific question |
| Wrong citations | Compare them with source passages; citations are prompted, not independently verified |

## Scope and limitations

This is a local learning project, not a hardened public service. It supports one PDF per browser session, up to 20 MiB, 200 pages, and one million extracted characters. Indexes and displayed conversations live in session memory and are rebuilt after a restart. It does not save uploads or indexes to disk. It does not implement OCR, image understanding, complex table reconstruction, authentication, multi-PDF retrieval, or conversational follow-up resolution. Ask complete questions: previous questions are displayed but are not passed to the model.

Chunk boundaries stay inside a page to preserve citations. Page numbers mean physical PDF positions starting at 1, which may differ from printed page labels. This model and initial settings are intended for English text. Keyword matching is not semantic understanding. Search-only mode is not generative AI; selecting OpenAI generation adds the generative component. Prompt instructions reduce unsupported claims but cannot guarantee truth or prevent every prompt-injection attempt.

## Official references

- Streamlit installation: https://docs.streamlit.io/get-started/installation/command-line
- LangChain text splitting: https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
- LangChain local embeddings: https://docs.langchain.com/oss/python/integrations/embeddings/sentence_transformers
- PyPDF text extraction: https://pypdf.readthedocs.io/en/stable/user/extract-text.html
- OpenAI API quickstart: https://developers.openai.com/api/docs/quickstart
- OpenAI text generation: https://developers.openai.com/api/docs/guides/text
