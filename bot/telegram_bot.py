import logging
import aiohttp
import os
import asyncio
import threading
import time
import re


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

SHOW_MENU, EMAIL, CONFIRM_EMAIL, PIX_TYPE, PIX, CONFIRM_PIX, OPTION, VALUE, CONFIRM_VALUE, START_QUIZ, CHECK_ANSWER = range(11)
TIME_TO_START_QUIZ = 5
TIME_TO_ANSWER_QUIZ = 5

reply_keyboard_menu = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Verificar saldo", callback_data="Verificar saldo"), InlineKeyboardButton("Recarregar saldo", callback_data="Recarregar saldo")],
        [InlineKeyboardButton("Iniciar quiz", callback_data="Iniciar quiz"), InlineKeyboardButton("Cancelar", callback_data="Cancelar")],
    ]
)

reply_keyboard_pix_type = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("CPF", callback_data="CPF"), InlineKeyboardButton("CNPJ", callback_data="CNPJ")],
        [InlineKeyboardButton("Chave aleatória", callback_data="Chave aleatória"), InlineKeyboardButton("Email", callback_data="Email")],
        [InlineKeyboardButton("Telefone", callback_data="Telefone"), InlineKeyboardButton("Cancelar", callback_data="Cancelar")],
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

async def fetch(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def post(url: str, data: dict) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            return await response.json()

async def put(url: str, data: dict) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=data) as response:
            return await response.json()

async def delete(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as response:
            return await response.json()
        
async def get_user_data(chat_id: int) -> dict:
  url = f"https://quizmy.site/api/v1/client/?chat_id={chat_id}"
  response = await fetch(url)
  return response

async def register_client(data: dict) -> dict:
  url = "https://quizmy.site/api/v1/client/"
  response = await post(url, data)
  return response

def validate_cpf(cpf: str) -> bool:
  # Remove any non-numeric characters
  cpf = re.sub(r'\D', '', cpf)
  
  # CPF must be 11 digits
  if len(cpf) != 11:
      return False
  
  # Validate CPF format
  if not re.match(r'\d{11}', cpf):
      return False
  
  # Basic CPF validation algorithm (simplified)
  def calc_digit(digits):
      total = sum(int(digit) * (index + 1) for index, digit in enumerate(digits))
      return total % 11 % 10
  
  if calc_digit(cpf[:9]) == int(cpf[9]) and calc_digit(cpf[:10]) == int(cpf[10]):
      return True
  return False

def validate_cnpj(cnpj: str) -> bool:
  # Remove any non-numeric characters
  cnpj = re.sub(r'\D', '', cnpj)
  
  # CNPJ must be 14 digits
  if len(cnpj) != 14:
      return False
  
  # Validate CNPJ format
  if not re.match(r'\d{14}', cnpj):
      return False
  
  # Basic CNPJ validation algorithm (simplified)
  def calc_digit(digits):
      weights = [6, 7, 8, 9, 2, 3, 4, 5]
      total = sum(int(digit) * weight for digit, weight in zip(digits[::-1], weights))
      return total % 11 % 10
  
  if calc_digit(cnpj[:12]) == int(cnpj[12]) and calc_digit(cnpj[:13]) == int(cnpj[13]):
      return True
  return False

def validate_phone(phone: str) -> bool:
  # Remove any non-numeric characters
  phone = re.sub(r'\D', '', phone)
  
  # Phone should have 10 or 11 digits
  if len(phone) not in [10, 11]:
      return False
  
  return bool(re.match(r'\d{10,11}', phone))

def validate_email(email: str) -> bool:
    # Define a regex pattern for validating an email address
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Match the email against the pattern
    if re.match(pattern, email):
        return True
    else:
        return False
    
def validate_pix(pix: str, pix_type: str) -> bool:
  validators = {
      "CPF": validate_cpf,
      "CNPJ": validate_cnpj,
      "Email": validate_email,
      "Telefone": validate_phone,
      "Chave aleatória": lambda x: True,
  }

  if pix_type in validators:
      return validators[pix_type](pix)
  else:
      return False
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa e solicita ao cliente o email"""
    first_name = update.message.from_user.first_name
    chat_id = update.message.chat_id
    user_data = get_user_data(chat_id)

    context.user_data["chat_id"] = chat_id
    context.user_data["first_name"] = first_name
    
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
    
    if not validate_email(email):
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
            "Ótimo! Agora preciso que você me informe sua chave PIX para pagamentos, ok? Escolha o tipo abaixo:",
            reply_markup=reply_keyboard_pix_type,
        )
        return PIX_TYPE
    else:
        await query.edit_message_text(
            "Por favor, me informe seu email novamente."
        )
        return EMAIL

async def pix_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    pix_type = query.data

    if pix_type == "Cancelar":
        await query.edit_message_text(
            "Tudo bem! Quando estiver pronto, basta digitar /start novamente.",
        )
        return ConversationHandler.END

    context.user_data["pix_type"] = pix_type

    await query.edit_message_text(
        f"Ótimo! Você escolheu o tipo {pix_type}. Agora insira a chave abaixo, incluindo pontos.",
    )
    return PIX


async def pix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pix = update.message.text.strip()
    valid = validate_pix(pix, context.user_data["pix_type"])
    if not valid:
      await update.message.reply_text(
          "Por favor, me informe uma chave PIX válida."
      )
      return PIX
    
    context.user_data["pix"] = pix

    await update.message.reply_text(
        f"Você informou a chave PIX {pix}. Verifique se está correto para evitar problemas com pagamentos. Confirma?",
        reply_markup=reply_keyboard_confirm,
    )
    return CONFIRM_PIX

async def confirm_pix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    answer = query.data

    if answer == "Sim":
        await query.edit_message_text(
            "Ótimo! Aguarde enquanto seu cadastro é feito...",
            reply_markup=reply_keyboard_menu,
        )
        data = {
            "chat_id": context.user_data["chat_id"],
            "first_name": context.user_data["first_name"],
            "email": context.user_data["email"],
            "pix_type": context.user_data["pix_type"],
            "pix": context.user_data["pix"],
        }
        response = await register_client(data)
        if response.get("error"):
          await query.edit_message_text(
              "Ocorreu um erro ao registrar seu cadastro. Por favor, tente novamente."
          )
          return ConversationHandler.END
        
        await query.edit_message_text(
            "Cadastro realizado com sucesso! Selecione uma opção no menu abaixo.",
            reply_markup=reply_keyboard_menu,
        )
        return OPTION
    else:
        await query.edit_message_text(
            "Por favor, me informe sua chave PIX novamente."
        )
        return PIX

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
  initial_time = time.time()
  time_passed_before = 0
  time_passed = 0

  await query.edit_message_text(
      f"{question} Você tem 5 segundos para responder.",
      reply_markup=reply_markup,
  )

  while time_passed < TIME_TO_ANSWER_QUIZ:
    if user_context.user_data.get("answered"):
      break
    
    time_passed = int(time.time() - initial_time)    
    
    if time_passed != time_passed_before:
      await query.edit_message_text(
          f"{question} Você tem {TIME_TO_ANSWER_QUIZ - time_passed} segundos para responder.",
          reply_markup=reply_markup,
      )
    
    await asyncio.sleep(0.1)
    time_passed_before = time_passed
    
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  
  query = update.callback_query
  await query.answer()

  selected_answer = query.data

  if selected_answer not in ["A", "B", "C", "D"]:
    return await show_menu(update, context)

  context.user_data["answered"] = True
  await asyncio.sleep(0.2) # aguarda 0.2 segundos para garantir que o método edit_quiz_message não está sendo executado

  if selected_answer == context.user_data["correct_answer"]:
    await query.edit_message_text(
      "Parabéns! Você acertou a resposta!",
      reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU
  else:
    await query.edit_message_text(
      "Que pena! Você errou a resposta.",
      reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU


async def timeout_callback(context: CallbackContext):
  user_context: ContextTypes.DEFAULT_TYPE = context.job.data["context"]
  user_update: Update = context.job.data["update"]

  await asyncio.sleep(0.2)

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