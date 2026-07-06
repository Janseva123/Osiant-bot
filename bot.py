import os
import logging
import re
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import requests
import whois
import socket
import dns.resolver
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# 🔴 YAHAN APNA TOKEN LAGAO
8727022727:AAEzTxPc-WZ6h0WmRluSXy6l4Ys148NCw3k

HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/"
IPAPI = "http://ip-api.com/json/"

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📱 Phone Lookup", callback_data='phone')],
        [InlineKeyboardButton("👤 Username Search", callback_data='username')],
        [InlineKeyboardButton("📧 Email Check", callback_data='email')],
        [InlineKeyboardButton("🌐 IP Address Lookup", callback_data='ip')],
        [InlineKeyboardButton("🔍 Domain Lookup", callback_data='domain')],
        [InlineKeyboardButton("🔎 Google Dorking", callback_data='dork')],
        [InlineKeyboardButton("📸 Social Media Search", callback_data='social')],
        [InlineKeyboardButton("💾 Leaked Data Search", callback_data='leak')],
        [InlineKeyboardButton("❓ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔥 *MAFIA OSINT BOT* 🔥\n\n"
        "Aapka apna OSINT Assistant. Neeche diye gaye options mein se koi ek chune:\n\n"
        "_Made with ❤️_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    menus = {
        'phone': ("📱 *Phone Number Lookup*\n\n10-digit phone number likhein (eg: 9876543210):", 'awaiting_phone'),
        'username': ("👤 *Username Search*\n\nUsername likhein (Instagram, Twitter, GitHub, Reddit, TikTok):", 'awaiting_username'),
        'email': ("📧 *Email Check*\n\nEmail address likhein (data breaches check honge):", 'awaiting_email'),
        'ip': ("🌐 *IP Address Lookup*\n\nIP address likhein (eg: 8.8.8.8):", 'awaiting_ip'),
        'domain': ("🔍 *Domain Lookup*\n\nDomain name likhein (eg: google.com):", 'awaiting_domain'),
        'dork': ("🔎 *Google Dorking*\n\nSearch query likhein:", 'awaiting_dork'),
        'social': ("📸 *Social Media Search*\n\nUsername ya URL likhein:", 'awaiting_social'),
        'leak': ("💾 *Leaked Data Search*\n\nEmail ya username dalen:", 'awaiting_leak'),
        'help': (None, None),
    }

    if data == 'help':
        help_text = ("❓ *Help*\n\n"
                     "📱 Phone Lookup - Country, carrier, location\n"
                     "👤 Username Search - 20+ social platforms\n"
                     "📧 Email Check - Data breach detection\n"
                     "🌐 IP Lookup - Location, ISP\n"
                     "🔍 Domain Lookup - WHOIS, DNS\n"
                     "🔎 Google Dorking - Advanced search\n"
                     "📸 Social Search - Profile scraper\n"
                     "💾 Leak Check - Breach database")
        await query.edit_message_text(help_text, parse_mode='Markdown')
        return

    msg, state = menus[data]
    await query.edit_message_text(msg, parse_mode='Markdown')
    context.user_data['state'] = state

async def handle_message(update, context):
    state = context.user_data.get('state')
    text = update.message.text

    functions = {
        'awaiting_phone': phone_lookup,
        'awaiting_username': username_search,
        'awaiting_email': email_check,
        'awaiting_ip': ip_lookup,
        'awaiting_domain': domain_lookup,
        'awaiting_dork': google_dork,
        'awaiting_social': social_search,
        'awaiting_leak': leak_check,
    }

    if state in functions:
        result = await functions[state](text)
        await update.message.reply_text(result, parse_mode='Markdown')

async def phone_lookup(number):
    try:
        if len(number) == 10:
            number = "+91" + number
        elif not number.startswith("+"):
            number = "+" + number
        phone = phonenumbers.parse(number, None)
        if not phonenumbers.is_valid_number(phone):
            return "❌ *Invalid phone number!*"
        country = geocoder.description_for_number(phone, "en")
        carrier_name = carrier.name_for_number(phone, "en")
        timezones = timezone.time_zones_for_number(phone)
        region = geocoder.region_code_for_number(phone)
        type_names = {0: "Fixed Line", 1: "Mobile", 2: "Fixed/Mobile", 3: "Toll Free", 4: "Premium", 6: "VoIP"}
        nt = phonenumbers.number_type(phone)
        return (f"📱 *Phone Details*\n\n🌍 Country: {country} ({region})\n"
                f"🏢 Carrier: {carrier_name or 'Unknown'}\n🕐 Timezone: {', '.join(timezones)}\n"
                f"📞 Type: {type_names.get(nt, 'Unknown')}\n✅ Valid: Yes")
    except Exception as e:
        return f"❌ Error: {e}"

async def username_search(username):
    platforms = {
        "Instagram": f"https://www.instagram.com/{username}",
        "Twitter/X": f"https://twitter.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "Reddit": f"https://reddit.com/u/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Facebook": f"https://www.facebook.com/{username}",
        "Telegram": f"https://t.me/{username}",
    }
    found = []
    for platform, url in platforms.items():
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code == 200:
                found.append(f"✅ {platform}")
        except:
            pass
    return (f"👤 *@{username}*\n\n✅ Found on {len(found)} platforms:\n" +
            "\n".join(found) if found else "❌ Not found on any platform")

async def email_check(email):
    try:
        resp = requests.get(f"{HIBP_API}{email}", headers={"User-Agent": "OSINT-Bot"}, timeout=10)
        if resp.status_code == 200:
            breaches = resp.json()
            result = f"📧 *{email}*\n\n⚠️ {len(breaches)} breaches:\n"
            for b in breaches[:5]:
                result += f"\n🔴 {b['Name']} - {b.get('BreachDate', 'Unknown')}"
            return result
        return f"✅ No breaches found for {email}"
    except Exception as e:
        return f"❌ Error: {e}"

async def ip_lookup(ip):
    try:
        resp = requests.get(f"{IPAPI}{ip}").json()
        if resp.get('status') == 'fail':
            return f"❌ Invalid IP"
        return (f"🌐 *{ip}*\n\n📍 {resp.get('city', '?')}, {resp.get('regionName', '?')}, {resp.get('country', '?')}\n"
                f"🏢 ISP: {resp.get('isp', '?')}\n📶 AS: {resp.get('as', '?')}")
    except Exception as e:
        return f"❌ Error: {e}"

async def domain_lookup(domain):
    try:
        w = whois.whois(domain)
        return (f"🔍 *{domain}*\n\n📅 Created: {w.creation_date}\n"
                f"⏰ Expires: {w.expiration_date}\n"
                f"🏢 Registrar: {w.registrar}")
    except Exception as e:
        return f"❌ Error: {e}"

async def google_dork(query):
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    return f"🔎 *Dork*\n\nQuery: `{query}`\n\n🔗 [Open in Google]({url})"

async def social_search(query):
    sites = {
        "Instagram": f"https://www.instagram.com/{query}",
        "Twitter": f"https://twitter.com/{query}",
        "YouTube": f"https://www.youtube.com/results?search_query={query}",
    }
    res = "📸 *Social Search*\n\n"
    for k, v in sites.items():
        res += f"• [{k}]({v})\n"
    return res

async def leak_check(query):
    if '@' in query:
        return await email_check(query)
    return "🔍 Check: haveibeenpwned.com"

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot started!")
    app.run_polling()
