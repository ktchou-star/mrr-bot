"""
Telegram Bot - Agent IA Architecte MRR
Propulse par OpenRouter (gratuit)
Version Railway
"""

import logging
import os
import json
import time
import urllib.request
import urllib.error
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

SYSTEM_PROMPT = """Tu es un architecte expert en systemes IA multi-agents autonomes orientes generation de MRR.

Ta mission : Creer une architecture complete d'un systeme autonome SaaS capable d'atteindre 1000 euros/mois minimum.

Le systeme doit :
- Choisir automatiquement sa niche via scoring intelligent
- Creer un MVP SaaS
- Lancer et deployer automatiquement
- Generer trafic organique
- Optimiser conversion
- Surveiller churn
- Ajuster prix
- Abandonner projets non rentables
- Conserver memoire strategique

Tu peux fournir :
1. Architecture detaillee multi-agents
2. Structure base de donnees complete
3. Moteur de scoring pondere
4. Moteur decisionnel conditionnel precis
5. Boucle autonome globale
6. Plan d'implementation technique
7. Methode d'optimisation continue
8. Strategie realiste pour atteindre 1000 euros/mois

Sois technique, structure et concret. Reponds toujours en francais sauf demande contraire."""

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

user_conversations = {}
MAX_HISTORY = 10


def get_history(user_id):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]


def add_message(user_id, role, text):
    history = get_history(user_id)
    history.append({"role": role, "content": text})
    if len(history) > MAX_HISTORY:
        user_conversations[user_id] = history[-MAX_HISTORY:]


def call_ai(user_id, retries=3):
    history = get_history(user_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(retries):
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + OPENROUTER_API_KEY,
                "HTTP-Referer": "https://mrr-bot.railway.app",
                "X-Title": "MRR Architect Bot",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                wait = 20 * (attempt + 1)
                time.sleep(wait)
                continue
            return "Erreur " + str(e.code) + " : " + body
        except Exception as e:
            return "Erreur : " + str(e)
    return "Le service est surcharge, reessaie dans une minute !"


def split_message(text, max_length=4000):
    if len(text) <= max_length:
        return [text]
    chunks = []
    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


async def start(update, context):
    user = update.effective_user
    await update.message.reply_text(
        "Bonjour " + user.first_name + " !\n\n"
        "Je suis ton Architecte IA MRR propulse par OpenRouter.\n"
        "Je t'aide a construire des systemes SaaS autonomes qui generent 1000 euros/mois+\n\n"
        "Commandes :\n"
        "/architecture - Systeme multi-agents complet\n"
        "/scoring - Moteur de scoring de niche\n"
        "/bdd - Structure base de donnees\n"
        "/boucle - Boucle autonome globale\n"
        "/strategie - Atteindre 1000 euros/mois\n"
        "/reset - Effacer l'historique\n\n"
        "Ou pose directement ta question !"
    )


async def reset(update, context):
    user_conversations[update.effective_user.id] = []
    await update.message.reply_text("Historique efface !")


async def quick_cmd(update, context, prompt):
    user_id = update.effective_user.id
    await update.message.reply_text("Generation en cours...")
    add_message(user_id, "user", prompt)
    response = call_ai(user_id)
    add_message(user_id, "assistant", response)
    for chunk in split_message(response):
        await update.message.reply_text(chunk)


async def cmd_architecture(update, context):
    await quick_cmd(update, context, "Donne l'architecture detaillee complete du systeme multi-agents autonome MRR.")


async def cmd_scoring(update, context):
    await quick_cmd(update, context, "Explique le moteur de scoring pondere pour choisir automatiquement la niche.")


async def cmd_bdd(update, context):
    await quick_cmd(update, context, "Donne la structure complete de la base de donnees : tables, colonnes, relations, index.")


async def cmd_boucle(update, context):
    await quick_cmd(update, context, "Decris la boucle autonome globale : etapes, triggers, conditions d'arret, memoire strategique.")


async def cmd_strategie(update, context):
    await quick_cmd(update, context, "Strategie realiste pour atteindre 1000 euros/mois de MRR. Timeline, jalons, KPIs, actions semaine par semaine.")


async def handle_message(update, context):
    user_id = update.effective_user.id
    user_text = update.message.text
    await update.message.reply_text("Analyse en cours...")
    add_message(user_id, "user", user_text)
    response = call_ai(user_id)
    add_message(user_id, "assistant", response)
    for chunk in split_message(response):
        await update.message.reply_text(chunk)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("architecture", cmd_architecture))
    app.add_handler(CommandHandler("scoring", cmd_scoring))
    app.add_handler(CommandHandler("bdd", cmd_bdd))
    app.add_handler(CommandHandler("boucle", cmd_boucle))
    app.add_handler(CommandHandler("strategie", cmd_strategie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot MRR OpenRouter demarre...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
