import logging
import aiohttp
import os
import asyncio
import threading
import time
import re
import requests


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

SHOW_MENU, EMAIL, CONFIRM_EMAIL, PIX_TYPE, PIX, CONFIRM_PIX, OPTION, ADD_BALANCE, VALUE, CONFIRM_VALUE, START_QUIZ, CHECK_ANSWER = range(12)
TIME_TO_START_QUIZ = 5
TIME_TO_ANSWER_QUIZ = 5

reply_keyboard_menu = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Iniciar quiz", callback_data="Iniciar quiz"), InlineKeyboardButton("Recarregar saldo", callback_data="Recarregar saldo")],
        [InlineKeyboardButton("Verificar saldo", callback_data="Verificar saldo"), InlineKeyboardButton("Mudar chave PIX", callback_data="Mudar chave PIX")],
        [InlineKeyboardButton("Cancelar", callback_data="Cancelar")],
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

reply_keyboard_change_pix_type = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Mudar tipo de chave", callback_data="Mudar tipo de chave")],
    ]

)


def login():
  url = "https://quizmy.site/api/v1/login/"
  data = {"email": "casa11tv@hotmail.com", "password": "99325120Aa@"}
  session = requests.Session()
  response = session.post(url, data=data)
  return response.cookies.get_dict()

cookies = login()
session = aiohttp.ClientSession(cookies=cookies)

async def fetch(url: str) -> str:
  async with session.get(url) as response:
    try:
      return await response.json()
    except:
      return {"error": "Ocorreu um erro ao processar a requisição."}

async def post(url: str, data: dict) -> str:
  async with session.post(url, data=data) as response:
    try:
      return await response.json()
    except:
      return {"error": "Ocorreu um erro ao processar a requisição."}

async def put(url: str, data: dict) -> str:
  async with session.put(url, data=data) as response:
    try:
      print(response.status)
      return await response.json()
    except:
      return {"error": "Ocorreu um erro ao processar a requisição."}

async def delete(url: str) -> str:
  async with session.delete(url) as response:
    try:
      return await response.json()
    except:
      return {"error": "Ocorreu um erro ao processar a requisição."}
        
async def get_user_data(chat_id: int) -> dict:
  # teste de cookies
  url = f"https://quizmy.site/api/v1/client/?chat_id={chat_id}"
  response = await fetch(url)
  return response

async def register_client(data: dict) -> dict:
  url = "https://quizmy.site/api/v1/client/"
  response = await post(url, data)
  return response

async def update_client(data: dict) -> dict:
  url = "https://quizmy.site/api/v1/client/"
  response = await put(url, data)
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

  return True

def validate_cnpj(cnpj: str) -> bool:
  # Remove any non-numeric characters
  cnpj = re.sub(r'\D', '', cnpj)
  
  # CNPJ must be 14 digits
  if len(cnpj) != 14:
      return False
  
  # Validate CNPJ format
  if not re.match(r'\d{14}', cnpj):
      return False
  
  return True

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
    user_data = await get_user_data(chat_id)
    print(chat_id)

    context.user_data["chat_id"] = chat_id
    context.user_data["first_name"] = first_name
    
    if not user_data or user_data.get("error"):
      context.user_data["registered"] = False
      await update.message.reply_text(
          f"Olá {first_name}! Bem vindo ao QuizzinBot! Vejo que é sua primeira vez aqui, poderia me informar seu email?"
      )
      return EMAIL
    
    else:
      context.user_data["registered"] = True
      context.user_data["email"] = user_data["email"]
      context.user_data["pix_type"] = user_data["pix_type"]
      context.user_data["pix"] = user_data["pix_key"]
      context.user_data["balance"] = user_data["balance"]

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
    
    context.user_data["email"] = email

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
        if not context.user_data["registered"]:
          # encerra a conversa pois o usuário não possui cadastro
          await query.edit_message_text(
              "Tudo bem! Quando estiver pronto, basta digitar /start novamente.",
          )
          return ConversationHandler.END
        
        await query.edit_message_text(
            "Tudo bem! Selecione uma opção no menu abaixo.",
            reply_markup=reply_keyboard_menu,
        )
        return OPTION

    context.user_data["pix_type"] = pix_type

    await query.edit_message_text(
        f"Ótimo! Você escolheu o tipo {pix_type}. Agora insira a chave abaixo, incluindo pontos.",
        reply_markup=reply_keyboard_change_pix_type,
    )
    return PIX

async def show_pix_type_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Selecione um tipo de chave PIX abaixo.",
        reply_markup=reply_keyboard_pix_type,
    )
    return PIX_TYPE

async def pix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pix = update.message.text.strip()
    valid = validate_pix(pix, context.user_data["pix_type"])
    if not valid:
      await update.message.reply_text(
          "Por favor, me informe uma chave PIX válida.",
          reply_markup=reply_keyboard_change_pix_type,
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
        if not context.user_data["registered"]:
          await query.edit_message_text(
              "Ótimo! Aguarde enquanto seu cadastro é feito...",
          )
          data = {
              "chat_id": context.user_data["chat_id"],
              "first_name": context.user_data["first_name"],
              "email": context.user_data["email"],
              "pix_type": context.user_data["pix_type"],
              "pix_key": context.user_data["pix"],
          }
          response = await register_client(data)
          if response.get("error"):
            await query.edit_message_text(
                "Ocorreu um erro ao registrar seu cadastro. Por favor, tente novamente mais tarde."
            )
            return ConversationHandler.END
          
          await query.edit_message_text(
              "Cadastro realizado com sucesso! Selecione uma opção no menu abaixo.",
              reply_markup=reply_keyboard_menu,
          )
          context.user_data["registered"] = True
          context.user_data["balance"] = 0
          return OPTION
        else:
          await query.edit_message_text(
              "Ótimo! Aguarde enquanto seu cadastro é atualizado...",
          )
          data = {
              "email": context.user_data["email"],
              "pix_type": context.user_data["pix_type"],
              "pix_key": context.user_data["pix"],
          }
          response = await update_client(data)
          if response.get("error"):
            await query.edit_message_text(
                "Ocorreu um erro ao atualizar seu cadastro. Por favor, tente novamente mais tarde.",
                reply_markup=reply_keyboard_return,
            )
            return SHOW_MENU
          
          await query.edit_message_text(
              "Sua chave PIX foi atualizada com sucesso!",
              reply_markup=reply_keyboard_return,
          )
          return SHOW_MENU
    else:
        await query.edit_message_text(
            "Por favor, me informe sua chave PIX novamente.",
            reply_markup=reply_keyboard_change_pix_type,
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
            f"Seu saldo é de {context.user_data['balance']}R$.",
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU
    
    elif selected_option == "Cancelar":
        await query.edit_message_text(
            "Até mais! basta digitar /start para iniciar novamente.",
        )
        return ConversationHandler.END
    
    elif selected_option == "Iniciar quiz":
      await query.edit_message_text(
          "Ótimo! Selecione um valor para apostar.",
          reply_markup=reply_keyboard_values,
      )
      return VALUE
    
    elif selected_option == "Mudar chave PIX":
      await query.edit_message_text(
          "Tudo bem! Selecione um novo tipo de chave PIX.",
          reply_markup=reply_keyboard_pix_type,
      )
      return PIX_TYPE
    
    elif selected_option == "Recarregar saldo":
      await query.edit_message_text(
          "Ótimo! Insira abaixo o valor que deseja adicionar ao seu saldo (apenas números inteiros).",
      )
      return ADD_BALANCE
  
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()

    if not value.isdigit():
        await update.message.reply_text(
            "Por favor, me informe um valor válido (apenas números inteiros)."
        )
        return ADD_BALANCE

    # TODO: sistema de pagamento
    data = {
      "email": context.user_data["email"],
      "balance": context.user_data["balance"]
    }
    response = await update_client(data)

    if response.get("error"):
      await update.message.reply_text(
          "Ocorreu um erro ao atualizar seu saldo. Por favor, tente novamente mais tarde."
      )
      return ConversationHandler.END

    context.user_data["balance"] += float(value)
    await update.message.reply_text(
        f"Saldo atualizado com sucesso! Seu novo saldo é de {context.user_data['balance']}R$.",
        reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU

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

    context.user_data["selected_value"] = float(selected_value.split("R$")[0])

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
        
        if context.user_data["balance"] > context.user_data["selected_value"]:
          for second in range(TIME_TO_START_QUIZ):
              await query.edit_message_text(
                  f"Você está pronto? O quiz iniciará em {TIME_TO_START_QUIZ - second} segundos."
              )
              await asyncio.sleep(1)
          return await start_quiz(update, context)
        
        else:
          await query.edit_message_text(
              "Você não possui saldo suficiente, recarregue no menu principal.",
              reply_markup=reply_keyboard_return,
          )
          return SHOW_MENU
    
    else:
        await query.edit_message_text(
            "Tudo certo! Basta escolher um novo valor para apostar.",
            reply_markup=reply_keyboard_values,
        )
        return VALUE
    
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  query = update.callback_query
  await query.answer()

  context.user_data["balance"] -= context.user_data["selected_value"]
  data = {
    "email": context.user_data["email"],
    "balance": context.user_data["balance"]
  }
  response = await update_client(data)
  
  if response.get("error"):
    await query.edit_message_text(
        "Ocorreu um erro ao atualizar seu saldo. Por favor, tente novamente mais tarde.",
        reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU

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
            PIX_TYPE: [CallbackQueryHandler(pix_type, pattern="^(CPF|CNPJ|Chave aleatória|Email|Telefone|Cancelar)$")],
            PIX: [CallbackQueryHandler(show_pix_type_menu, pattern="^(Mudar tipo de chave)$"), MessageHandler(filters.TEXT, pix)],
            CONFIRM_PIX: [CallbackQueryHandler(confirm_pix, pattern="^(Sim|Não)$")],
            OPTION: [CallbackQueryHandler(option, pattern="^(Verificar saldo|Recarregar saldo|Iniciar quiz|Cancelar|Retornar ao menu|Mudar chave PIX)$")],
            ADD_BALANCE: [MessageHandler(filters.TEXT, add_balance)],
            SHOW_MENU: [CallbackQueryHandler(show_menu, pattern="^(Retornar ao menu)$")],
            VALUE: [CallbackQueryHandler(value, pattern="^(1R\$|5R\$|10R\$|100R\$|1000R\$|Cancelar)$")],
            CONFIRM_VALUE: [CallbackQueryHandler(confirm_value, pattern="^(Sim|Não)$")],
            START_QUIZ: [CallbackQueryHandler(start_quiz, pattern="^(A|B|C|D)")],
            CHECK_ANSWER: [CallbackQueryHandler(check_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
  

if __name__ == "__main__":
    login()
    main()