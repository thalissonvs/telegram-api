import logging
import requests
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

EMAIL, CONFIRM_EMAIL, OPTION, VALUE, CONFIRM_VALUE, START_QUIZ = range(6)
reply_keyboard_menu = [["Verificar saldo", "Recarregar saldo"], ["Iniciar quiz", "Cancelar"]]
reply_keyboard_values = [["1R$", "5R$"], ["10R$", "100R$"], ["1000R$", "Cancelar"]]
reply_keyboard_confirm = [["Sim", "Não"]]

def get_user_data(chat_id: int) -> dict:
    pass

def verify_email(email: str) -> bool:
  if len(email.split(" ")) > 1 or "@" not in email or "." not in email:
      return False
  return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa e solicita ao cliente o email"""
    first_name = update.message.from_user.first_name
    chat_id = update.message.chat_id
    user_data = get_user_data(chat_id)
    
    if not user_data:
      
      await update.message.reply_text(
          f"Olá {first_name}! Bem vindo ao QuizzinBot! Vejo que é sua primeira vez aqui, poderia me informar seu email?"
      )
      return EMAIL
    
    else:
      
      await update.message.reply_text(
          f"Olá {first_name}! Bem vindo de volta ao QuizzinBot! Selecione uma opção no menu abaixo.",
          reply_markup=ReplyKeyboardMarkup(reply_keyboard_menu, one_time_keyboard=True, resize_keyboard=True),
      )
      return OPTION

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o email do cliente"""
    email = update.message.text.strip()
    
    if not verify_email(email):
      await update.message.reply_text(
          "Por favor, me informe um email válido."
      )
      return EMAIL
    
    await update.message.reply_text(
        f"Obrigado! Seu email é {email}, está correto?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard_confirm, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text.strip()
    if answer == "Sim":
        await update.message.reply_text(
            "Ótimo! Seu cadastro está completo! Selecione uma opção no menu abaixo.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_menu, one_time_keyboard=True, resize_keyboard=True),
        )
        return OPTION
    else:
        await update.message.reply_text(
            "Por favor, me informe seu email novamente."
        )
        return EMAIL
  
async def option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_option = update.message.text

    if selected_option == "Verificar saldo":
        await update.message.reply_text(
            "Seu saldo é de R$ 0,00."
        )
        await update.message.reply_text(
            "Selecione uma opção no menu abaixo.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_menu, one_time_keyboard=True, resize_keyboard=True),
        )
        return OPTION
    
    elif selected_option == "Cancelar":
        await update.message.reply_text(
            "Até mais!"
        )
        return ConversationHandler.END
    
    elif selected_option == "Iniciar quiz":
        await update.message.reply_text(
            "Vamos começar o quiz! Primeiro, escolha o valor que deseja apostar.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_values, one_time_keyboard=True, resize_keyboard=True),
        )
        return VALUE
        
async def value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_value = update.message.text
    
    if selected_value == "Cancelar":
        await update.message.reply_text(
            "Tudo bem! Você pode escolher novamente uma opção no menu abaixo.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_menu, one_time_keyboard=True, resize_keyboard=True),
        )
        return OPTION

    await update.message.reply_text(
        f"Você deseja apostar {selected_value}?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard_confirm, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM_VALUE

async def confirm_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text.strip()
    if answer == "Sim":
        context.user_data["value"] = update.message.text
        await update.message.reply_text(
            "Ótimo! Vamos começar o quiz!"
        )
        return START_QUIZ
    else:
        await update.message.reply_text(
            "Tudo certo! Basta escolher um valor novamente.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_values, one_time_keyboard=True, resize_keyboard=True),
        )
        return VALUE

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a conversa e finaliza o bot"""
    await update.message.reply_text(
        "Até mais!"
    )
    return ConversationHandler.END

def main() -> None:
    token = os.getenv("TELEGRAM_KEY") or "7164176762:AAHgcZ__UPWDC7xK5LrpbymUSvPFVe_edAg"
    application = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT, email)],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT, confirm_email)],
            OPTION: [MessageHandler(filters.TEXT, option)],
            VALUE: [MessageHandler(filters.TEXT, value)],
            CONFIRM_VALUE: [MessageHandler(filters.TEXT, confirm_value)],
            START_QUIZ: [MessageHandler(filters.TEXT, start_quiz)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()
  

if __name__ == "__main__":
    main()