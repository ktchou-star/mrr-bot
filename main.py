 """
Telegram Bot - Agent IA Architecte MRR
Propulsé par OpenRouter (gratuit)
Version Railway — lit les clés depuis les variables d'environnement
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

# ─────────────────────────────────────────────
# CONFIGURATION — clés lues depuis Railway
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.0-flash:free"  # Gratuit sur OpenRouter

# ─────────────────────────────────────────────
# PROMPT SYSTÈME
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un architecte expert en systèmes IA multi-agents autonomes orientés génération de MRR.

Ta mission :
Créer une architecture complète d'un système autonome SaaS capable d'atteindre 1000€/mois minimum.

Le système doit :
 • Choisir automatiquement sa niche via scoring intelligent
 • Créer un MVP SaaS
 • Lancer et déployer automatiquement
 • Générer trafic organique
 • Optimiser conversion
 • Surveiller churn
 • Ajuster prix
 • Abandonner projets non rentables
 • Conserver mémoire stratégique

Tu peux fournir :
 1. Architecture détaillée multi-agents
 2. Structure base de données complète
 3. Moteur de scoring pondéré
 4. Moteur décisionnel conditionnel précis
 5. Boucle autonome globale
 6. Plan d'implémentation technique
 7. Méthode d'optimisation continue
 8. Stratégie réaliste pour atteindre 1000€/mois

Sois technique, structuré et concret. Réponds toujours en français sauf demande contraire."""

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# MÉMOIRE PAR UTILISATEUR
# ─────────────────────────────────────────────
user_conversations: dict[int, list[dict]] = {}
MAX_HISTORY = 10


def get_history(user_id: int) -> list[dict]:
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]


def add_message(user_id: int, role: str, text: str):
    history = get_history(user_id)
    history.append({"role": role, "content": text})
    if len(history) > MAX_HISTORY:
        user_conversations[user_id] = history[-MAX_HISTORY:]


# ─────────────────────────────────────────────
# APPEL OPENROUTER
# ─────────────────────────────────────────────
def call_ai(user_id: int, retries: int = 3) -> str:
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
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
                logger.warning(f"429 rate limit, attente {wait}s (tentative {attempt+1}/{retries})")
                time.sleep(wait)
                continue
            logger.error(f"OpenRouter HTTP error {e.code}: {body}")
            return f"❌ Erreur {e.code} : {body}"
        except Exception as e:
            logger.error(f"Erreur OpenRouter: {e}")
            return f"❌ Erreur : {str(e)}"

    return "⏳ Le service est surchargé, réessaie dans une minute !"


# ─────────────────────────────────────────────
# UTILITAIRE
# ─────────────────────────────────────────────
def split_message(text: str, max_length: int = 4000) -> list[str]:
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


# ─────────────────────────────────────────────
# HANDLERS TELEGRAM
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Bonjour {user.first_name} !\n\n"
        "🤖 Je suis ton Architecte IA MRR propulsé par OpenRouter.\n"
        "Je t'aide à construire des systèmes SaaS autonomes qui génèrent 1000€/mois+\n\n"
        "Commandes :\n"
        "/architecture — Système multi-agents complet\n"
        "/scoring — Moteur de scoring de niche\n"
        "/bdd — Structure base de données\n"
        "/boucle — Boucle autonome globale\n"
        "/strategie — Atteindre 1000€/mois\n"
        "/reset — Effacer l'historique\n\n"
        "Ou pose directement ta question ! 💬"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_conversations[update.effective_user.id] = []
    await update.message.reply_text("🔄 Historique effacé !")


async def quick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    user_id = update.effective_user.id
    await update.message.reply_text("⏳ Génération en cours...")
    add_message(user_id, "user", prompt)
    response = call_ai(user_id)
    add_message(user_id, "assistant", response)
    for chunk in split_message(response):
        await update.message.reply_text(chunk)


async def cmd_architecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_cmd(update, context,
        "Donne l'architecture détaillée complète du système multi-agents autonome MRR.")


async def cmd_scoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_cmd(update, context,
        "Explique le moteur de scoring pondéré pour choisir automatiquement la niche.")


async def cmd_bdd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_cmd(update, context,
        "Donne la structure complète de la base de données : tables, colonnes, relations, index.")


async def cmd_boucle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_cmd(update, context,
        "Décris la boucle autonome globale : étapes, triggers, conditions d'arrêt, mémoire stratégique.")


async def cmd_strategie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_cmd(update, context,
        "Stratégie réaliste pour atteindre 1000€/mois de MRR. Timeline, jalons, KPIs, actions semaine par semaine.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    await update.message.reply_text("⏳ Analyse en cours...")
    add_message(user_id, "user", user_text)
    response = call_ai(user_id)
    add_message(user_id, "assistant", response)
    for chunk in split_message(response):
        await update.message.reply_text(chunk)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
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
    logger.info("🤖 Bot MRR (OpenRouter) démarré...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
