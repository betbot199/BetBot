import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apuestas import generar_recomendacion, generar_varias_recomendaciones

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Cargar variables de entorno
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

if not TOKEN:
    raise ValueError("❌ ERROR: La variable TELEGRAM_BOT_TOKEN no está definida.")
if not WEBHOOK_URL:
    raise ValueError("❌ ERROR: La variable WEBHOOK_URL no está definida.")

print("✅ Token y Webhook URL cargados correctamente.")

# Inicializar aplicación del bot
app = ApplicationBuilder().token(TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Usa:\n"
        "👉 /recomendar para ver una combinada sugerida\n"
        "👉 /ver_3 para ver tres distintas"
    )

# /recomendar
async def recomendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 Comando /recomendar recibido")
    await update.message.reply_text("🔍 Buscando combinada óptima... Dame unos segundos ⏳")

    async def tarea():
        try:
            texto = generar_recomendacion()
            await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Error en /recomendar: {e}")
            await update.message.reply_text("❌ Hubo un problema generando la recomendación.")

    asyncio.create_task(tarea())

# /ver_3
async def ver_tres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 Comando /ver_3 recibido")
    await update.message.reply_text("🔍 Buscando 3 combinadas con valor... ⏳")

    async def tarea():
        try:
            texto = generar_varias_recomendaciones(cantidad=3)
            await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Error en /ver_3: {e}")
            await update.message.reply_text("❌ Hubo un problema generando las combinadas.")

    asyncio.create_task(tarea())

# Añadir handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("recomendar", recomendar))
app.add_handler(CommandHandler("ver_3", ver_tres))

# Ejecutar servidor con webhook
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    print("🚀 Iniciando servidor con Webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

