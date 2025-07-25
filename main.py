import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apuestas import generar_recomendacion, generar_varias_recomendaciones

# 🔐 Cargar token desde variable de entorno
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ERROR: La variable de entorno TELEGRAM_BOT_TOKEN no está definida.")
else:
    print("✅ TOKEN cargado correctamente.")

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

    async def tarea_lenta():
        try:
            texto = generar_recomendacion()
            await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Error en /recomendar: {e}")
            await update.message.reply_text("❌ Hubo un problema generando la recomendación.")

    asyncio.create_task(tarea_lenta())

# /ver_3
async def ver_tres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 Comando /ver_3 recibido")
    await update.message.reply_text("🔍 Buscando 3 combinadas con valor... ⏳")

    async def tarea_lenta():
        try:
            texto = generar_varias_recomendaciones(cantidad=3)
            await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Error en /ver_3: {e}")
            await update.message.reply_text("❌ Hubo un problema generando las combinadas.")

    asyncio.create_task(tarea_lenta())

# Inicializar aplicación del bot
if __name__ == "__main__":
    print("🤖 Bot iniciado y conectado a The Odds API.")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recomendar", recomendar))
    app.add_handler(CommandHandler("ver_3", ver_tres))

    app.run_polling()
