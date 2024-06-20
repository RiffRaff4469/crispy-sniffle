from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Define states for the ConversationHandler
START, SELECT_COUNTRY, AGE_CONFIRMATION, PHYSICAL_ORDER, PHYSICAL_SIGNATURE, PHYSICAL_ID_PHOTO, DIGITAL_PHOTO, DIGITAL_TEXT = range(8)

# Tokens and chat ID
TOKEN = '6496977862:AAHCXU-6c4BXeuxIbEeCjV4i87iz-73yH_o'
YOUR_CHAT_ID = '7257763725'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message and show the main menu."""
    keyboard = [
        [InlineKeyboardButton("Order Physical ID", callback_data='order_physical')],
        [InlineKeyboardButton("Order Digital ID", callback_data='order_digital')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to Keys IDs! Please choose which type you want:', reply_markup=reply_markup)
    return START

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button presses and start the respective order process."""
    query = update.callback_query
    await query.answer()

    if query.data == 'order_physical':
        keyboard = [
            [InlineKeyboardButton("Canada Drivers", callback_data='canada')],
            [InlineKeyboardButton("United States Drivers", callback_data='usa')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Please select your country:', reply_markup=reply_markup)
        return SELECT_COUNTRY
    elif query.data == 'order_digital':
        await query.edit_message_text('Please upload a photo of your ID.')
        return DIGITAL_PHOTO

# Physical order handlers
async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle country selection and proceed accordingly."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'canada':
        context.user_data['country'] = 'Canada'
        await query.edit_message_text('Please enter your First Name:')
        return PHYSICAL_ORDER
    elif query.data == 'usa':
        context.user_data['country'] = 'United States'
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='confirm_age')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "For US ID's there are 2 different types, Under 21 and Over 21 because the drinking age is 21. \n"
            "Here is a list of which states have U21 and O21 ID since we cannot produce all. If you select one that doesnt exist we will pick for you. If you pick an out of stock one we will DM you. Press 'yes' once you understand the list. \n"
            "Over 21 is available for all 50 states except GA. Under 21 is available for AR, CA, DE, FL, GA, MS, NY, ND, PA, SC, TX. ", reply_markup=reply_markup
            )
        return AGE_CONFIRMATION

async def confirm_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle age confirmation and proceed to asking questions."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Please enter your First Name:')
    return PHYSICAL_ORDER

async def handle_physical_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect physical order details."""
    text = update.message.text
    context.user_data.setdefault('order_info', []).append(text)
    
    questions = [
        "First Name", "Middle Name (optional, say 'blank' if not needed)", "Last Name", "Date of Birth (dd/mm/yy)", "Country of Birth", "Eye Color (google VEHICLE, HAIR AND EYE COLOR CODES to see all options)", "Hair Color (google VEHICLE, HAIR AND EYE COLOR CODES to see all options)",
        "Height (in CM)", "Weight (in KG)", "State in Country", "Address (say 'blank' for random address)", "Photo of your signature (use flash)", "ID Photo (pro photo pls)"
    ]
    
    if len(context.user_data['order_info']) < len(questions) - 2:
        next_question = questions[len(context.user_data['order_info'])]
        await update.message.reply_text(f'Please enter your {next_question}:')
        return PHYSICAL_ORDER
    elif len(context.user_data['order_info']) == len(questions) - 2:
        await update.message.reply_text(f'Please upload a photo of your signature:')
        return PHYSICAL_SIGNATURE
    else:
        await update.message.reply_text(f'Please upload an ID photo of yourself:')
        return PHYSICAL_ID_PHOTO

async def handle_physical_signature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the uploaded signature photo."""
    context.user_data['signature'] = update.message.photo[-1].file_id
    await update.message.reply_text('Please upload an ID photo of yourself.')
    return PHYSICAL_ID_PHOTO

async def handle_physical_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the uploaded ID photo and finish the physical order."""
    context.user_data['id_photo'] = update.message.photo[-1].file_id
    await update.message.reply_text('Thank you, Mr. Key will DM you about payment and other details later.')
    
    info = context.user_data['order_info']
    country = context.user_data['country']
    username = update.message.from_user.username if update.message.from_user.username else "No username"
    
    await context.bot.send_photo(chat_id=YOUR_CHAT_ID, photo=context.user_data['signature'], caption="Signature")
    await context.bot.send_photo(chat_id=YOUR_CHAT_ID, photo=context.user_data['id_photo'], caption="ID Photo")
    await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=f"Physical order details ({country}) by @{username}: {info}")
    
    return START

# Digital order handlers
async def handle_digital_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the uploaded photo and ask for text details."""
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text('Please write what you want changed on your ID (birthday normally).')
    return DIGITAL_TEXT

async def handle_digital_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the text details and finish the digital order."""
    context.user_data['text'] = update.message.text
    await update.message.reply_text('Thank you, Mr. Key will DM you about payment later.')
    
    username = update.message.from_user.username if update.message.from_user.username else "No username"
    
    await context.bot.send_photo(chat_id=YOUR_CHAT_ID, photo=context.user_data['photo'], caption=f"Change request by @{username}: {context.user_data['text']}")
    return START

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [
                CallbackQueryHandler(button, pattern='^order_physical$|^order_digital$'),
            ],
            SELECT_COUNTRY: [
                CallbackQueryHandler(select_country, pattern='^canada$|^usa$'),
            ],
            AGE_CONFIRMATION: [
                CallbackQueryHandler(confirm_age, pattern='^confirm_age$'),
            ],
            PHYSICAL_ORDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_physical_info),
            ],
            PHYSICAL_SIGNATURE: [
                MessageHandler(filters.PHOTO, handle_physical_signature),
            ],
            PHYSICAL_ID_PHOTO: [
                MessageHandler(filters.PHOTO, handle_physical_id_photo),
            ],
            DIGITAL_PHOTO: [
                MessageHandler(filters.PHOTO, handle_digital_photo),
            ],
            DIGITAL_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_digital_text),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
        per_message=False  # Ensure the conversation persists across multiple messages
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
