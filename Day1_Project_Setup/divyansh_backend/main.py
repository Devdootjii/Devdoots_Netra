from fastapi import FastAPI

# App instance create karna
app = FastAPI(title="Project Netra Backend", description="Backend APIs for AI Threat Detection")

# Health check endpoint - ye verify karne ke liye ki server zinda hai
@app.get("/health")
def health_check():
    return {
        "status": "success", 
        "message": "Netra API is running perfectly."
    }