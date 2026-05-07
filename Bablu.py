#!/usr/bin/env python3
"""
Termux Telegram Bot - Fixed Version
"""

import os
import sys
import time
import sqlite3
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

# Fix for Termux
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# ============================================
# IMPORT FIX - Direct import without error
# ============================================

try:
    from telegram import Update
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler
    from telegram.ext import CallbackQueryHandler, ContextTypes, filters
    from telegram.constants import ParseMode
    print("✅ Telegram module loaded successfully!")
except Exception as e:
    print(f"❌ Import Error: {e}")
    print("\nSOLUTION: Rename or delete old 'telegram.py' file!")
    print("Command: rm /storage/emulated/0/Download/telegram.py\n")
    sys.exit(1)

# ============================================
# CONFIGURATION
# ============================================

class Config:
    """Bot Settings"""
    
    # ⚠️ YAHAN APNI SETTINGS DALO
    BOT_TOKEN = "8745022562:AAEIHFPxH-UCj_YF39d8bF6AbqIvHwOyWSg" # @BotFather se token lo
    BOT_USERNAME = "TermuxBot"
    
    # ⚠️ Apna Telegram User ID yahan dalo
    ADMIN_IDS = {6539387265}
    
    # Database path
    DB_PATH = os.path.join(os.path.expanduser("~"), "balu_bot.db")
    
    # Rate limit
    RATE_LIMIT = 1.0

# ============================================
# SIMPLE DATABASE
# ============================================

class Database:
    """Simple database"""
    
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            msg_count INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )""")
        self.conn.commit()
        print("✅ Database ready")
    
    def save_user(self, user_id, username=None, first_name=None):
        """Save user"""
        self.conn.execute("""INSERT OR REPLACE INTO users 
            VALUES (?, ?, ?, COALESCE((SELECT msg_count+1 FROM users WHERE user_id=?), 1), 0)""",
            (user_id, username, first_name, user_id))
        self.conn.commit()
    
    def get_count(self):
        """Get user count"""
        return self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    
    def is_banned(self, user_id):
        """Check ban"""
        r = self.conn.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
        return r and r[0] == 1
    
    def close(self):
        """Close db"""
        self.conn.close()

# ============================================
# BOT HANDLER
# ============================================

class Bot:
    """Main bot class"""
    
    def __init__(self):
        self.db = Database()
        self.rate = {}  # Rate limiter
        self.start_time = datetime.now()
    
    def is_admin(self, uid):
        """Check admin"""
        return uid in Config.ADMIN_IDS
    
    def check_rate(self, uid):
        """Rate limit check"""
        now = time.time()
        if uid in self.rate and now - self.rate[uid] < Config.RATE_LIMIT:
            return False
        self.rate[uid] = now
        return True
    
    def menu_keyboard(self, uid):
        """Main keyboard"""
        btns = [
            ["📋 Help", "ℹ️ About"],
            ["📊 Stats", "💬 Feedback"],
            ["⚙️ Settings", "❓ FAQ"]
        ]
        if self.is_admin(uid):
            btns.append(["👑 Admin"])
        return ReplyKeyboardMarkup(btns, resize_keyboard=True)
    
    # ========== COMMANDS ==========
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        u = update.effective_user
        
        if not self.check_rate(u.id):
            await update.message.reply_text("⏳ Wait...")
            return
        
        self.db.save_user(u.id, u.username, u.first_name)
        
        txt = f"""✨ *Welcome {u.first_name}!*

🤖 Bot: *{Config.BOT_USERNAME}*
📱 Running on Termux

*Commands:*
/start - Start
/help - Help
/about - Info
/stats - Stats
/ping - Check status

Use buttons below!"""
        
        await update.message.reply_text(
            txt,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.menu_keyboard(u.id)
        )
    
    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help"""
        txt = """📚 *Help Menu*

/start - Start bot
/help - This menu
/about - Bot info
/stats - Your stats
/ping - Check bot
/feedback msg - Send feedback
/time - Current time
/date - Today's date"""
        
        if self.is_admin(update.effective_user.id):
            txt += "\n\n👑 *Admin:*\n/admin - Panel\n/users - Count"
        
        await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About"""
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        users = self.db.get_count()
        
        txt = f"""ℹ️ *About*

🤖 Bot: {Config.BOT_USERNAME}
📱 Platform: Termux
🐍 Python: {sys.version.split()[0]}
⏱️ Uptime: {uptime}
👥 Users: {users}
✅ Status: Online"""
        
        await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)
    
    async def ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ping"""
        start = time.time()
        msg = await update.message.reply_text("🏓 Ping...")
        ms = round((time.time() - start) * 1000, 2)
        await msg.edit_text(f"🏓 *Pong!* `{ms}ms`", parse_mode=ParseMode.MARKDOWN)
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stats"""
        u = update.effective_user
        txt = f"""📊 *Your Stats*

🆔 ID: `{u.id}`
👤 Name: {u.first_name}
📝 Username: @{u.username or 'N/A'}
✅ Active User"""
        
        await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)
    
    async def feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Feedback"""
        if not context.args:
            await update.message.reply_text("💬 Use: /feedback your message")
            return
        
        msg = ' '.join(context.args)
        for aid in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(aid, f"📬 Feedback from {update.effective_user.first_name}:\n{msg}")
            except:
                pass
        
        await update.message.reply_text("✅ Feedback sent!")
    
    async def time_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Time"""
        t = datetime.now().strftime("%H:%M:%S")
        await update.message.reply_text(f"🕐 {t}")
    
    async def date_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Date"""
        d = datetime.now().strftime("%d %B, %Y")
        await update.message.reply_text(f"📅 {d}")
    
    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Echo"""
        t = ' '.join(context.args) if context.args else "Kuch to bolo!"
        await update.message.reply_text(f"🔊 {t}")
    
    # ========== ADMIN ==========
    
    async def admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin panel"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only!")
            return
        
        btns = [[InlineKeyboardButton("👥 Users", callback_data="a_users"),
                 InlineKeyboardButton("📊 Status", callback_data="a_status")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]]
        
        await update.message.reply_text(
            "👑 *Admin Panel*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(btns)
        )
    
    async def users_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User count"""
        if not self.is_admin(update.effective_user.id):
            return
        await update.message.reply_text(f"👥 Users: {self.db.get_count()}")
    
    # ========== MESSAGE HANDLER ==========
    
    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages"""
        u = update.effective_user
        t = update.message.text
        
        if self.db.is_banned(u.id):
            return
        
        if not self.check_rate(u.id):
            await update.message.reply_text("⏳ Wait...")
            return
        
        self.db.save_user(u.id, u.username, u.first_name)
        
        # Keyboard buttons
        if t == "📋 Help":
            await self.help_cmd(update, context)
        elif t == "ℹ️ About":
            await self.about(update, context)
        elif t == "📊 Stats":
            await self.stats(update, context)
        elif t == "💬 Feedback":
            context.args = ["hi"]
            await self.feedback(update, context)
        elif t == "⚙️ Settings":
            await update.message.reply_text("⚙️ Coming soon!")
        elif t == "❓ FAQ":
            await update.message.reply_text("❓ *FAQ*\n\nQ: Free?\nA: Yes!\n\nQ: Support?\nA: /feedback", parse_mode=ParseMode.MARKDOWN)
        elif t == "👑 Admin" and self.is_admin(u.id):
            await self.admin(update, context)
        else:
            await update.message.reply_text(
                f"👋 Hello *{u.first_name}*!\n📝 You said: _{t}_\n\n💡 Use /help for commands",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========== CALLBACKS ==========
    
    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callbacks"""
        q = update.callback_query
        await q.answer()
        
        if q.data == "close":
            await q.message.delete()
        elif q.data == "a_users":
            await q.edit_message_text(f"👥 Total users: *{self.db.get_count()}*", parse_mode=ParseMode.MARKDOWN)
        elif q.data == "a_status":
            up = str(datetime.now() - self.start_time).split('.')[0]
            await q.edit_message_text(f"✅ Online\n⏱️ Uptime: {up}\n📱 Termux")

# ============================================
# ERROR HANDLER
# ============================================

async def on_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Error handler"""
    print(f"❌ Error: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ Error! Try again.")
        except:
            pass

# ============================================
# MAIN
# ============================================

def main():
    """Start bot"""
    os.system('clear')
    
    print("=" * 40)
    print("   TERMUX TELEGRAM BOT")
    print("=" * 40)
    
    # Check token
    if "YOUR_BOT_TOKEN" in Config.BOT_TOKEN:
        print("\n❌ ERROR: Bot token set nahi hai!")
        print("   BOT_TOKEN variable mein apna token dalo\n")
        return
    
    # Create bot handler
    bot = Bot()
    
    # Build app
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_cmd))
    app.add_handler(CommandHandler("about", bot.about))
    app.add_handler(CommandHandler("ping", bot.ping))
    app.add_handler(CommandHandler("stats", bot.stats))
    app.add_handler(CommandHandler("feedback", bot.feedback))
    app.add_handler(CommandHandler("time", bot.time_cmd))
    app.add_handler(CommandHandler("date", bot.date_cmd))
    app.add_handler(CommandHandler("echo", bot.echo))
    app.add_handler(CommandHandler("admin", bot.admin))
    app.add_handler(CommandHandler("users", bot.users_cmd))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.on_message))
    
    # Callback handler
    app.add_handler(CallbackQueryHandler(bot.on_callback))
    
    # Error handler
    app.add_error_handler(on_error)
    
    print("✅ Bot starting...")
    print("📋 Commands ready")
    print("⚠️  Ctrl+C to stop\n")
    
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    finally:
        bot.db.close()

if __name__ == "__main__":
    main()
