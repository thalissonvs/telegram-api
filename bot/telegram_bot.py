import logging
import requests
import os
import asyncio
import threading

from telegram.ext import JobQueue, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

SHOW_MENU, EMAIL, CONFIRM_EMAIL, OPTION, VALUE, CONFIRM_VALUE, START_QUIZ, CHECK_ANSWER = range(8)
TIME_TO_START_QUIZ = 2
TIME_TO_ANSWER_QUIZ = 10

reply_keyboard_menu = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Verificar saldo", callback_data="Verificar saldo"), InlineKeyboardButton("Recarregar saldo", callback_data="Recarregar saldo")],
        [InlineKeyboardButton("Iniciar quiz", callback_data="Iniciar quiz"), InlineKeyboardButton("Cancelar", callback_data="Cancelar")],
    ]
)
reply_keyboard_values = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("1R$", callback_data="1R$"), InlineKeyboardButton("5R$", callback_data="5R$")],
        [InlineKeyboardButton("10R$", callback_data="10R$"), InlineKeyboardButton("100R$", callback_data="100R$")],
        [InlineKeyboardButton("1000R$", callback_data="1000R$"), InlineKeyboardButton("Cancelar", callback_data="Cancelar")],
    ]
)
reply_keyboard_confirm = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Sim", callback_data="Sim"), InlineKeyboardButton("Não", callback_data="Não")],
    ]
)

reply_keyboard_return = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Retornar ao menu", callback_data="Retornar ao menu")],
    ]

)

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
          reply_markup=reply_keyboard_menu,
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
        reply_markup=reply_keyboard_confirm,
    )
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    answer = query.data

    if answer == "Sim":
        await query.edit_message_text(
            "Ótimo! Selecione uma opção no menu abaixo.",
            reply_markup=reply_keyboard_menu,
        )
        return OPTION
    else:
        await query.edit_message_text(
            "Por favor, me informe seu email novamente."
        )
        return EMAIL
    
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Selecione uma opção no menu abaixo.",
        reply_markup=reply_keyboard_menu,
    )
    return OPTION

async def option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_option = query.data

    if selected_option == "Verificar saldo":
        await query.edit_message_text(
            "Seu saldo é de 100R$.",
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU
    
    elif selected_option == "Cancelar":
        await update.message.reply_text(
            "Até mais!"
        )
        return ConversationHandler.END
    
    elif selected_option == "Iniciar quiz":
        await query.edit_message_text(
            "Ótimo! Selecione um valor para apostar.",
            reply_markup=reply_keyboard_values,
        )
        return VALUE
        
async def value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_value = query.data

    if selected_value == "Cancelar":
        await query.edit_message_text(
          "Tudo bem! Você pode escolher uma nova opção no menu abaixo.",
          reply_markup=reply_keyboard_menu,
        )
        return OPTION


    context.user_data["selected_value"] = selected_value

    await query.edit_message_text(
        f"Você escolheu apostar {selected_value}. Está correto?",
        reply_markup=reply_keyboard_confirm,
    )
    return CONFIRM_VALUE

async def confirm_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    answer = query.data

    if answer == "Sim":
        for second in range(TIME_TO_START_QUIZ):
            await query.edit_message_text(
                f"Você está pronto? O quiz iniciará em {TIME_TO_START_QUIZ - second} segundos."
            )
            await asyncio.sleep(1)
        return await start_quiz(update, context)
    else:
        await query.edit_message_text(
            "Tudo certo! Basta escolher um novo valor para apostar.",
            reply_markup=reply_keyboard_values,
        )
        return VALUE
    
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  query = update.callback_query
  await query.answer()

  reply_keyboard_quiz = InlineKeyboardMarkup(
    [
      [InlineKeyboardButton("França", callback_data="A"), InlineKeyboardButton("Brasília", callback_data="B")],
      [InlineKeyboardButton("Berlim", callback_data="C"), InlineKeyboardButton("Tokyo", callback_data="D")],
    ]
  )
  context.user_data["correct_answer"] = "D"
  context.user_data["answered"] = False

  # executa um timer para chamar o método timeout_callback após x segundos, sem thread
  context.job_queue.run_once(timeout_callback, TIME_TO_ANSWER_QUIZ, {"context": context, "update": update})
  context.job_queue.run_once(edit_quiz_message, 0, {"query": query, "question": "Qual é a capital do Japão?", "reply_markup": reply_keyboard_quiz, "context": context})

  return CHECK_ANSWER

async def edit_quiz_message(context: CallbackContext) -> int:
  query = context.job.data["query"]
  question = context.job.data["question"]
  reply_markup = context.job.data["reply_markup"]
  user_context = context.job.data["context"]
  
  for second in range(TIME_TO_ANSWER_QUIZ):
    
    if user_context.user_data.get("answered"):
      break

    await query.edit_message_text(
        f"{question} Você tem {TIME_TO_ANSWER_QUIZ - second} segundos para responder.",
        reply_markup=reply_markup,
    )
    await asyncio.sleep(1)
    
    
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  
  query = update.callback_query
  await query.answer()

  selected_answer = query.data

  if selected_answer not in ["A", "B", "C", "D"]:
    return await show_menu(update, context)

  context.user_data["answered"] = True

  if selected_answer == context.user_data["correct_answer"]:
    await query.edit_message_text(
      "Parabéns! Você acertou a resposta!"
    )
  else:
    await query.edit_message_text(
      "Que pena! Você errou a resposta."
    )

  return ConversationHandler.END

async def timeout_callback(context: CallbackContext):
  user_context: ContextTypes.DEFAULT_TYPE = context.job.data["context"]
  user_update: Update = context.job.data["update"]

  if not user_context.user_data.get("answered"):
    await user_update.callback_query.edit_message_text(
      "Tempo esgotado! Você não respondeu a tempo.",
      reply_markup=reply_keyboard_return,
    )
  
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
            CONFIRM_EMAIL: [CallbackQueryHandler(confirm_email, pattern="^(Sim|Não)$")],
            OPTION: [CallbackQueryHandler(option, pattern="^(Verificar saldo|Recarregar saldo|Iniciar quiz|Cancelar|Retornar ao menu)$")],
            SHOW_MENU: [CallbackQueryHandler(show_menu, pattern="^(Retornar ao menu)$")],
            VALUE: [CallbackQueryHandler(value, pattern="^(1R\$|5R\$|10R\$|100R\$|1000R\$|Cancelar)$")],
            CONFIRM_VALUE: [CallbackQueryHandler(confirm_value, pattern="^(Sim|Não)$")],
            START_QUIZ: [CallbackQueryHandler(start_quiz, pattern="^(A|B|C|D)")],
            CHECK_ANSWER: [CallbackQueryHandler(check_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
  

if __name__ == "__main__":
    main()