web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
api: uvicorn backend.main:app --host 0.0.0.0 --port ${API_PORT:-8000}
