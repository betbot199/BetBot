import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Importar funciones desde apuestas.py
from apuestas import scan, format_values, format_surebets, format_middles, get_bank, set_bank

# Configuración del logging
logging.basicConfig(level=logging.INFO)

# Variables de entorno
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

if not TOKEN:
    raise ValueError("❌ ERROR: La variable TELEGRAM_BOT_TOKEN no está definida.")
if not WEBHOOK_URL:
    raise ValueError("❌ ERROR: La variable WEBHOOK_URL no está definida.")

print("✅ Token y Webhook URL cargados correctamente.")

# Inicializar aplicación
app = ApplicationBuilder().token(TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al bot profesional de apuestas.\n"
        "Comandos disponibles:\n"
        "💰 /value → Muestra apuestas con valor esperado positivo.\n"
        "🔀 /surebets → Muestra oportunidades de arbitraje.\n"
        "🎯 /middles → Muestra oportunidades de middles.\n"
        "🏦 /bank → Consulta el bank actual.\n"
        "📈 /setbank <cantidad> → Configura el bank."
    )

# /value
async def value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Buscando value bets...")

    async def tarea():
        try:
            apuestas = scan("value")
            if not apuestas:
                await update.message.reply_text("❌ No se encontraron value bets.")
            else:
                texto = format_values(apuestas)
                await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error en /value: {e}")

    asyncio.create_task(tarea())

# /surebets
async def surebets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Buscando surebets...")

    async def tarea():
        try:
            apuestas = scan("surebets")
            if not apuestas:
                await update.message.reply_text("❌ No se encontraron surebets.")
            else:
                texto = format_surebets(apuestas)
                await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error en /surebets: {e}")

    asyncio.create_task(tarea())

# /middles
async def middles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Buscando middles...")

    async def tarea():
        try:
            apuestas = scan("middles")
            if not apuestas:
                await update.message.reply_text("❌ No se encontraron middles.")
            else:
                texto = format_middles(apuestas)
                await update.message.reply_text(texto, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error en /middles: {e}")

    asyncio.create_task(tarea())

# /bank
async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_actual = get_bank()
    await update.message.reply_text(f"🏦 Bank actual: {bank_actual} unidades.")

# /setbank
async def setbank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cantidad = float(context.args[0])
        set_bank(cantidad)
        await update.message.reply_text(f"✅ Bank configurado a {cantidad} unidades.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso correcto: /setbank <cantidad>")

# Registrar comandos
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("value", value))
app.add_handler(CommandHandler("surebets", surebets))
app.add_handler(CommandHandler("middles", middles))
app.add_handler(CommandHandler("bank", bank))
app.add_handler(CommandHandler("setbank", setbank_cmd))

# Ejecutar con webhook
if _name_ == "_main_":
    import nest_asyncio
    nest_asyncio.apply()

    print("🚀 Iniciando servidor con Webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )