# main.py
import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apuestas import scan, format_values, format_surebets, format_middles, get_bank, set_bank

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

if not TOKEN:
    raise ValueError("❌ Falta TELEGRAM_BOT_TOKEN")
if not WEBHOOK_URL:
    raise ValueError("❌ Falta WEBHOOK_URL")

app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot de ineficiencias activo.\n"
        "Comandos:\n"
        "• /scan – escanea mercados y calcula valor\n"
        "• /value [n] – muestra top n value bets\n"
        "• /surebets [n] – muestra arbitrajes\n"
        "• /middles [n] – (experimental)\n"
        "• /bank [monto] – fija bank (ej: /bank 1000)\n"
        f"Bank actual: {get_bank()}",
        disable_web_page_preview=True
    )

async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔍 Escaneando mercados… espera unos segundos ⏳")
    def job():
        v,s = scan()
        return v,s
    v,s = await asyncio.to_thread(job)
    await msg.edit_text(f"✅ Scan listo. Value: {v} | Surebets: {s}")

async def cmd_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 5
    if context.args:
        try: n = int(context.args[0])
        except: pass
    txt = await asyncio.to_thread(format_values, n)
    await update.message.reply_text(txt, parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_surebets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 5
    if context.args:
        try: n = int(context.args[0])
        except: pass
    txt = await asyncio.to_thread(format_surebets, n)
    await update.message.reply_text(txt, parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_middles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 5
    if context.args:
        try: n = int(context.args[0])
        except: pass
    txt = await asyncio.to_thread(format_middles, n)
    await update.message.reply_text(txt, parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(f"Bank actual: {get_bank()}")
    try:
        amt = float(context.args[0])
        set_bank(amt)
        await update.message.reply_text(f"💰 Bank actualizado: {amt}")
    except:
        await update.message.reply_text("Formato inválido. Ej: /bank 1000")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scan", cmd_scan))
app.add_handler(CommandHandler("value", cmd_value))
app.add_handler(CommandHandler("surebets", cmd_surebets))
app.add_handler(CommandHandler("middles", cmd_middles))
app.add_handler(CommandHandler("bank", cmd_bank))

if _name_ == "_main_":
    import nest_asyncio
    nest_asyncio.apply()
    app.run_webhook(listen="0.0.0.0", port=int(PORT), webhook_url=WEBHOOK_URL)