from fastapi import FastAPI
from .models.recommender import Recommender
import uvicorn
import threading
from .events.consumer import start_consumer
import os

app = FastAPI(title="Recommendation Service")
recommender = Recommender()

# Iniciar consumidor de RabbitMQ en segundo plano
threading.Thread(target=start_consumer, daemon=True).start()

@app.on_event("startup")
async def startup_event():
    recommender.update_model()

@app.post("/recommend")
def get_recommendations(user_data: dict):
    # Lógica de ejemplo (usa tu modelo real)
    recommender = Recommender()
    recommendations = recommender.generate_recommendations(
        user_data["user_id"],
        user_data["product_ids"]
    )
    
    return {
        "user_id": user_data["user_id"],
        "recommendations": recommendations
    }

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8003)),
        reload=True
    )