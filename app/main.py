from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import customer_router, user_router, demo_router, email_router, ollama_router, chat_router, widget_router, acts_router, lead_router, monthly_updates_router


from app.auth.auth import auth_middleware_call
from app.configs.settings import settings
from app.utils.migration_utils import run_migrations
from app.services.import_scheduler import get_scheduler
from app.services.redis_service import RedisService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run migrations programmatically using Alembic
    run_migrations()
    
    # Initialize and start the import scheduler
    try:
        redis_service = RedisService()
        scheduler = get_scheduler(redis_service)
        scheduler.start_scheduler(interval_minutes=1440)  # Run once per day (24 hours = 1440 minutes)
        print("Import scheduler started successfully - runs once per day")
    except Exception as e:
        print(f"Warning: Could not start import scheduler: {e}")
    
    yield
    
    # Shutdown: Stop the scheduler
    try:
        scheduler.stop_scheduler()
        print("Import scheduler stopped")
    except:
        pass

app = FastAPI(
    title = settings.server.api_name,
    description = "This AI Agent combines the power of Large Language Models, Vector Databases, and API integrations to deliver contextual intelligence and dynamic automation.",
    version = settings.server.version,
    lifespan=lifespan
)

app.include_router(user_router.userRoutes)
app.include_router(customer_router.customerRoutes)
app.include_router(demo_router.demoRoutes)
app.include_router(email_router.emailRoutes)
app.include_router(ollama_router.aiAgentsRoutes)
app.include_router(chat_router.chat_router)
app.include_router(widget_router.widgetRoutes)
app.include_router(acts_router.actsRoutes)
app.include_router(lead_router.lead_router)
app.include_router(monthly_updates_router.monthlyUpdatesRoutes)

origins = settings.server.cors_urls

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Middleware to check API key for all requests
app.middleware("http")(auth_middleware_call)

@app.get("/")
def root():
    return {"message": f"Welcome to {app.title} {app.version}! {app.description}"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ricagent-api"}