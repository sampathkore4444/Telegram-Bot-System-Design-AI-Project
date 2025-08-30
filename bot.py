import os
import logging
import sqlite3
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import ollama
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-r1:8b")  # Lighter model for Railway
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


# Initialize Ollama client
ollama_client = ollama.Client(host=OLLAMA_HOST)

# In-memory cache for free tier (no persistence)
response_cache = {}
user_states = {}


async def debug_ollama_connection():
    """Debug Ollama connection issues"""
    try:
        # Try to connect to Ollama
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags", timeout=5) as response:
                logger.info(f"Ollama connection status: {response.status}")
                return True
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")

        # Additional debugging
        try:
            # Check if port is open
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("localhost", 11434))
            logger.info(f"Socket connection test: {result} (0 means success)")
            sock.close()
        except Exception as sock_error:
            logger.error(f"Socket test failed: {sock_error}")

        return False


async def check_ollama_health():
    """Check if Ollama server is healthy"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags", timeout=10) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return False


async def ensure_model_ready():
    """Ensure the model is loaded and ready"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            models = ollama_client.list()
            model_exists = any(
                m["model"] == MODEL_NAME for m in models.get("models", [])
            )

            if not model_exists:
                logger.info(f"Model {MODEL_NAME} not found. Pulling...")
                ollama_client.pull(MODEL_NAME)
                await asyncio.sleep(10)  # Wait for pull to complete

            # Test the model
            response = ollama_client.chat(
                model=MODEL_NAME, messages=[{"role": "user", "content": "Hello"}]
            )
            logger.info("✅ Model is ready")
            return True

        except Exception as e:
            logger.warning(
                f"Model not ready yet (attempt {attempt + 1}/{max_retries}): {e}"
            )
            await asyncio.sleep(5)

    logger.error("❌ Model failed to load after multiple attempts")
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_text = f"""
👋 Hello {user.first_name}! I'm **SystemSensei**, your AI system design mentor.

🚀 *Now running on Railway Cloud!*

I can help you with:
• Explaining system design concepts
• Architecture patterns
• Technology comparisons
• Design principles

Just send me a topic like:
• `Load Balancer`
• `CAP Theorem`
• `Microservices vs Monolith`
• `Database indexing`

*Note:* Using a lighter model for faster responses on free tier.
    """
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    user_states[user.id] = "idle"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages"""
    user = update.effective_user
    user_input = update.message.text.strip().lower()

    if not user_input:
        await update.message.reply_text("Please send a topic or question!")
        return

    # Check cache first
    if user_input in response_cache:
        await update.message.reply_text(
            response_cache[user_input], parse_mode="Markdown"
        )
        return

    # Check if model is ready
    if not await check_ollama_health():
        await update.message.reply_text(
            "⚠️ AI engine is starting up. Please wait a moment and try again."
        )
        return

    await update.message.chat.send_action(action="typing")

    try:
        # Master prompt optimized for lighter models
        master_prompt = f"""
You are SystemSensei, a system design expert. Explain this concept clearly and concisely.

Topic: {user_input}

Please provide:
1. A simple analogy or real-world example
2. Key characteristics and components
3. When to use it and when to avoid it
4. Related technologies or patterns

Keep it under 500 words. Use Markdown for formatting.
        """

        # Generate response
        response = ollama_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": master_prompt}],
            options={"temperature": 0.1, "num_predict": 300},  # Conservative settings
        )

        explanation = response["message"]["content"]

        # Cache the response
        response_cache[user_input] = explanation

        await update.message.reply_text(explanation, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "❌ Sorry, I'm having trouble processing your request. The model might still be loading. Try again in a moment."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    health = await check_ollama_health()
    status_text = f"""
🔄 **System Status**
• Ollama Health: {'✅ Healthy' if health else '❌ Unhealthy'}
• Model: `{MODEL_NAME}`
• Cache Size: {len(response_cache)} topics
• Active Users: {len(user_states)}

*Running on Railway Free Tier*
    """
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def post_init(application: Application):
    """Run after application initialization"""
    logger.info("Starting model initialization...")

    # Start model loading in background
    asyncio.create_task(load_model_async())


async def load_model_async():
    """Load model asynchronously"""
    await asyncio.sleep(2)  # Wait for Ollama to start
    await ensure_model_ready()


def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is required!")
        logger.error("Set it in Railway dashboard: Settings -> Variables")
        return

    # Create Application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Start the bot
    logger.info("Starting SystemDesignBot on Railway...")
    application.run_polling()


if __name__ == "__main__":
    main()
