import logging
import aiohttp
import os
import asyncio
import threading
import time
import re
import requests
from datetime import datetime
import base64
from PIL import Image
from io import BytesIO
import mercadopago
import uuid
import random


from telegram.ext import JobQueue, CallbackContext
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    PicklePersistence,
    filters,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

(
    SHOW_MENU,
    EMAIL,
    CONFIRM_EMAIL,
    PIX_TYPE,
    PIX,
    CONFIRM_PIX,
    OPTION,
    GET_BALANCE,
    VALUE,
    CONFIRM_VALUE,
    PAYMENTS,
    PRIZES,
    START_QUIZ,
    CHECK_ANSWER,
    CHECK_PAYMENT,
) = range(15)
TIME_TO_START_QUIZ = 5
TIME_TO_ANSWER_QUIZ = 5
QUIZZES_TO_WIN = 5
ACCESS_TOKEN = 'APP_USR-1178900652572281-071222-08a5b1fae9bb4b16813e9d610564e1f5-248670826'
VALUES = [3.99, 5.99, 9.99, 99.99, 999.99]

reply_keyboard_menu = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('Iniciar quiz', callback_data='Iniciar quiz'),
            InlineKeyboardButton(
                'Recarregar saldo', callback_data='Recarregar saldo'
            ),
        ],
        [
            InlineKeyboardButton(
                'Verificar saldo', callback_data='Verificar saldo'
            ),
            InlineKeyboardButton(
                'Mudar chave PIX', callback_data='Mudar chave PIX'
            ),
        ],
        [
            InlineKeyboardButton(
                'Histórico de saldo', callback_data='Histórico de saldo'
            ),
            InlineKeyboardButton('Meus prêmios', callback_data='Meus prêmios'),
        ],
        [InlineKeyboardButton('Cancelar', callback_data='Cancelar')],
    ]
)

reply_keyboard_pix_type = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('CPF', callback_data='CPF'),
            InlineKeyboardButton('CNPJ', callback_data='CNPJ'),
        ],
        [
            InlineKeyboardButton(
                'Chave aleatória', callback_data='Chave aleatória'
            ),
            InlineKeyboardButton('Email', callback_data='Email'),
        ],
        [
            InlineKeyboardButton('Telefone', callback_data='Telefone'),
            InlineKeyboardButton('Cancelar', callback_data='Cancelar'),
        ],
    ]
)

reply_keyboard_values = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(f'{VALUES[0]}R$ ganha 100R$', callback_data=f'{VALUES[0]}R$'),
            InlineKeyboardButton(f'{VALUES[1]}R$ ganha 500R$ ', callback_data=f'{VALUES[1]}R$'),
        ],
        [
            InlineKeyboardButton(f'{VALUES[2]}R$ ganha 700R$', callback_data=f'{VALUES[2]}R$'),
            InlineKeyboardButton(f'{VALUES[3]}R$ 100R$', callback_data=f'{VALUES[3]}R$'),
        ],
        [
            InlineKeyboardButton(f'{VALUES[4]}R$ ganha 10000R$', callback_data=f'{VALUES[4]}R$'),
            InlineKeyboardButton('Cancelar', callback_data='Cancelar'),
        ],
    ]
)

reply_keyboard_confirm = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('Sim', callback_data='Sim'),
            InlineKeyboardButton('Não', callback_data='Não'),
        ],
    ]
)

reply_keyboard_return = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                'Retornar ao menu', callback_data='Retornar ao menu'
            )
        ],
    ]
)

reply_keyboard_change_pix_type = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                'Mudar tipo de chave', callback_data='Mudar tipo de chave'
            )
        ],
    ]
)

reply_keyboard_payment_done = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('Verificar', callback_data='Verificar'),
            InlineKeyboardButton('Cancelar', callback_data='Cancelar'),
        ],
    ]
)


def login():
    url = 'https://quizmy.site/api/v1/login/'
    data = {'email': 'casa11tv@hotmail.com', 'password': '99325120Aa@'}
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
            return {'error': 'Ocorreu um erro ao processar a requisição.'}


async def post(url: str, data: dict) -> str:
    async with session.post(url, data=data) as response:
        try:
            return await response.json()
        except:
            return {'error': 'Ocorreu um erro ao processar a requisição.'}


async def put(url: str, data: dict) -> str:
    async with session.put(url, data=data) as response:
        try:
            print(response.status)
            return await response.json()
        except:
            return {'error': 'Ocorreu um erro ao processar a requisição.'}


async def delete(url: str) -> str:
    async with session.delete(url) as response:
        try:
            return await response.json()
        except:
            return {'error': 'Ocorreu um erro ao processar a requisição.'}


async def get_user_data(chat_id: int) -> dict:
    # teste de cookies
    url = f'https://quizmy.site/api/v1/client/?chat_id={chat_id}'
    response = await fetch(url)
    return response


async def register_client(data: dict) -> dict:
    url = 'https://quizmy.site/api/v1/client/'
    response = await post(url, data)
    return response


async def update_client(data: dict) -> dict:
    url = 'https://quizmy.site/api/v1/client/'
    response = await put(url, data)
    return response


async def new_payment(data: dict) -> dict:
    url = 'https://quizmy.site/api/v1/payments/'
    response = await post(url, data)
    return response


async def get_payments(client_id: int) -> dict:
    url = f'https://quizmy.site/api/v1/payments/?client_id={client_id}'
    response = await fetch(url)
    return response


async def new_prize(data: dict) -> dict:
    url = 'https://quizmy.site/api/v1/prizes/'
    response = await post(url, data)
    return response


async def get_prizes(client_id: int) -> dict:
    url = f'https://quizmy.site/api/v1/prizes/?client_id={client_id}'
    response = await fetch(url)
    return response

async def get_quizzes(difficulty: int) -> dict:
    url = f'https://quizmy.site/api/v1/quizzes/?difficulty={difficulty}'
    response = await fetch(url)
    return response

async def generate_mp_payment(data: dict) -> dict:
    sdk = mercadopago.SDK(ACCESS_TOKEN)
    price = data['price']
    email = data['email']

    body = {
        'transaction_amount': float(price),
        'description': 'Adição de créditos',
        'payment_method_id': 'pix',
        'payer': {
            'email': email,
        },
    }
    
    idempotency_key = str(uuid.uuid4())
    request_options = mercadopago.config.RequestOptions()
    request_options.custom_headers = {
      'x-idempotency-key': idempotency_key
    }
    
    response = sdk.payment().create(body, request_options)
    payment = response['response']
    return {
        'id': payment['id'],
        'qr_code_base64': payment['point_of_interaction']['transaction_data'][
            'qr_code_base64'
        ],
        'qr_code': payment['point_of_interaction']['transaction_data'][
            'qr_code'
        ],
    }


async def get_mp_payment(payment_id: int) -> dict:
    sdk = mercadopago.SDK(ACCESS_TOKEN)
    response = sdk.payment().get(payment_id)
    payment = response['response']
    return {
        'status': payment['status'],
        'value': payment['transaction_amount'],
    }


async def decode_base64_image(base64_string: str) -> BytesIO:
    image = Image.open(BytesIO(base64.b64decode(base64_string)))
    image_io = BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0)
    return image_io


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
        'CPF': validate_cpf,
        'CNPJ': validate_cnpj,
        'Email': validate_email,
        'Telefone': validate_phone,
        'Chave aleatória': lambda x: True,
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

    context.user_data['chat_id'] = chat_id
    context.user_data['first_name'] = first_name
    context.user_data['correct_answers'] = 0
    context.user_data['answered'] = False 

    if not user_data or user_data.get('error'):
        context.user_data['registered'] = False
        await update.message.reply_text(
            f'Olá {first_name}! Bem vindo ao QuizzinBot! Vejo que é sua primeira vez aqui, poderia me informar seu email? Não se preocupe, não te enviaremos mensagem!'
        )
        return EMAIL

    else:
        context.user_data['registered'] = True
        context.user_data['client_id'] = user_data['id']
        context.user_data['email'] = user_data['email']
        context.user_data['pix_type'] = user_data['pix_type']
        context.user_data['pix'] = user_data['pix_key']
        context.user_data['balance'] = user_data['balance']

        await update.message.reply_text(
            f'Olá {first_name}! Bem vindo de volta ao QuizzinBot! Selecione uma opção no menu abaixo.',
            reply_markup=reply_keyboard_menu,
        )
        return OPTION


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o email do cliente"""
    email = update.message.text.strip()

    if not validate_email(email):
        await update.message.reply_text(
            'Por favor, me informe um email válido.'
        )
        return EMAIL

    context.user_data['email'] = email

    await update.message.reply_text(
        f'Obrigado! Seu email é {email}, está correto?',
        reply_markup=reply_keyboard_confirm,
    )
    return CONFIRM_EMAIL


async def confirm_email(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    answer = query.data

    if answer == 'Sim':
        if not context.user_data['registered']:
            await query.edit_message_text(
                'Ótimo! Aguarde enquanto seu cadastro é feito...',
            )
            data = {
                'chat_id': context.user_data['chat_id'],
                'first_name': context.user_data['first_name'],
                'email': context.user_data['email'],
                'pix_type': '',
                'pix_key': '',
            }
            response = await register_client(data)
            if response.get('error'):
                await query.edit_message_text(
                    'Ocorreu um erro ao registrar seu cadastro. Por favor, tente novamente mais tarde.'
                )
                return ConversationHandler.END

            await query.edit_message_text(
                'Cadastro realizado com sucesso! Lembre-se de cadastrar sua chave PIX mais tarde na opção "Mudar chave PIX". Vamos começar?',
                reply_markup=reply_keyboard_menu,
            )
            context.user_data['registered'] = True
            context.user_data['client_id'] = response['id']
            context.user_data['balance'] = 0
            return OPTION
        
      
    else:
        await query.edit_message_text(
            'Por favor, me informe seu email novamente.'
        )
        return EMAIL


async def pix_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    pix_type = query.data

    if pix_type == 'Cancelar':
        if not context.user_data['registered']:
            # encerra a conversa pois o usuário não possui cadastro
            await query.edit_message_text(
                'Tudo bem! Quando estiver pronto, basta digitar /start novamente.',
            )
            return ConversationHandler.END

        await query.edit_message_text(
            'Tudo bem! Selecione uma opção no menu abaixo.',
            reply_markup=reply_keyboard_menu,
        )
        return OPTION

    context.user_data['pix_type'] = pix_type

    await query.edit_message_text(
        f'Ótimo! Você escolheu o tipo {pix_type}. Agora insira a chave abaixo, incluindo pontos.',
        reply_markup=reply_keyboard_change_pix_type,
    )
    return PIX


async def show_pix_type_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Selecione um tipo de chave PIX abaixo.',
        reply_markup=reply_keyboard_pix_type,
    )
    return PIX_TYPE


async def pix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pix = update.message.text.strip()
    valid = validate_pix(pix, context.user_data['pix_type'])
    if not valid:
        await update.message.reply_text(
            'Por favor, me informe uma chave PIX válida.',
            reply_markup=reply_keyboard_change_pix_type,
        )
        return PIX

    context.user_data['pix'] = pix

    await update.message.reply_text(
        f'Você informou a chave PIX {pix}. Verifique se está correto para evitar problemas com pagamentos. Confirma?',
        reply_markup=reply_keyboard_confirm,
    )
    return CONFIRM_PIX


async def confirm_pix(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    answer = query.data

    if answer == 'Sim':
        if not context.user_data['registered']:
            await query.edit_message_text(
                'Ótimo! Aguarde enquanto seu cadastro é feito...',
            )
            data = {
                'chat_id': context.user_data['chat_id'],
                'first_name': context.user_data['first_name'],
                'email': context.user_data['email'],
                'pix_type': context.user_data['pix_type'],
                'pix_key': context.user_data['pix'],
            }
            response = await register_client(data)
            if response.get('error'):
                await query.edit_message_text(
                    'Ocorreu um erro ao registrar seu cadastro. Por favor, tente novamente mais tarde.'
                )
                return ConversationHandler.END

            await query.edit_message_text(
                'Cadastro realizado com sucesso! Selecione uma opção no menu abaixo.',
                reply_markup=reply_keyboard_menu,
            )
            context.user_data['registered'] = True
            context.user_data['client_id'] = response['id']
            context.user_data['balance'] = 0
            return OPTION
        else:
            await query.edit_message_text(
                'Ótimo! Aguarde enquanto seu cadastro é atualizado...',
            )
            data = {
                'email': context.user_data['email'],
                'pix_type': context.user_data['pix_type'],
                'pix_key': context.user_data['pix'],
            }
            response = await update_client(data)
            if response.get('error'):
                await query.edit_message_text(
                    'Ocorreu um erro ao atualizar seu cadastro. Por favor, tente novamente mais tarde.',
                    reply_markup=reply_keyboard_return,
                )
                return SHOW_MENU

            await query.edit_message_text(
                'Sua chave PIX foi atualizada com sucesso!',
                reply_markup=reply_keyboard_return,
            )
            return SHOW_MENU
    else:
        await query.edit_message_text(
            'Por favor, me informe sua chave PIX novamente.',
            reply_markup=reply_keyboard_change_pix_type,
        )
        return PIX


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['start_directly'] = False

    if context.user_data.get('photo_message_id', None):
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=context.user_data['photo_message_id'],
        )
        context.user_data['photo_message_id'] = None

    await query.edit_message_text(
        'Selecione uma opção no menu abaixo.',
        reply_markup=reply_keyboard_menu,
    )
    return OPTION


async def verify_balance_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Seu saldo é de {context.user_data['balance']}R$.",
        reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU


async def start_quiz_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Ótimo! Selecione um valor para investir.',
        reply_markup=reply_keyboard_values,
    )
    return VALUE


async def change_pix_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Tudo bem! Selecione um novo tipo de chave PIX.',
        reply_markup=reply_keyboard_pix_type,
    )
    return PIX_TYPE


async def add_balance_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Ótimo! Insira abaixo o valor que deseja adicionar ao seu saldo (apenas números inteiros).',
    )
    return GET_BALANCE


async def show_balance_history_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    client_id = context.user_data['client_id']
    response = await get_payments(client_id)

    if type(response) == dict and response.get('error'):
        await query.edit_message_text(
            'Ocorreu um erro ao buscar seus pagamentos. Por favor, tente novamente mais tarde.',
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU

    if not response:
        await query.edit_message_text(
            'Você não possui histórico registrado.',
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU

    payments = []
    for payment in response:
        value = f"{payment['price']}R$"
        date = datetime.strptime(
            payment['date'], '%Y-%m-%dT%H:%M:%S.%fZ'
        ).strftime('%d/%m/%Y %H:%M')
        payments.append(f'{value} - {date}')

    payments_string = '\n'.join(payments)

    await query.edit_message_text(
        f'Aqui estão os últimos registros do seu saldo:\n\n{payments_string}',
        reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU


async def show_prizes_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    client_id = context.user_data['client_id']
    response = await get_prizes(client_id)

    if type(response) == dict and response.get('error'):
        await query.edit_message_text(
            'Ocorreu um erro ao buscar seus prêmios. Por favor, tente novamente mais tarde.',
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU

    if not response:
        await query.edit_message_text(
            'Você não possui prêmios registrados.',
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU

    prizes = []
    for prize in response:
        value = f"{prize['price']}R$"
        date = datetime.strptime(
            prize['date'], '%Y-%m-%dT%H:%M:%S.%fZ'
        ).strftime('%d/%m/%Y %H:%M')
        paid = 'Sim' if prize['status'] == 1 else 'Não'
        prizes.append(f'{value} - {date} | Pago: {paid}')

    prizes_string = '\n'.join(prizes)

    await query.edit_message_text(
        f'Aqui estão seus prêmios:\n\n{prizes_string}',
        reply_markup=reply_keyboard_return,
    )
    return SHOW_MENU


async def get_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    value = update.message.text.strip()

    if not value.isdigit():
        await update.message.reply_text(
            'Por favor, me informe um valor válido (apenas números inteiros).'
        )
        return GET_BALANCE

    value = int(value)
    return await add_balance(update, context, value)

async def add_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, value: int
) -> int:
    
    data = {
        'price': value,
        'email': context.user_data['email'],
        'accessToken': ACCESS_TOKEN,
    }

    response = await generate_mp_payment(data)
    if response.get('error'):
        await update.message.reply_text(
            'Ocorreu um erro ao gerar o pagamento. Por favor, tente novamente mais tarde.',
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU

    qr_code_base64 = response['qr_code_base64']
    qr_code_image = await decode_base64_image(qr_code_base64)
    qr_code = response['qr_code']
    payment_id = response['id']

    context.user_data[
        'payment_id'
    ] = payment_id   # usado para verificar o pagamento posteriormente

    photo_message = await context.bot.send_photo(
        chat_id=context.user_data['chat_id'], photo=InputFile(qr_code_image, filename='qr_code.png'), caption=qr_code
    )

    context.user_data['photo_message_id'] = photo_message.message_id

    await context.bot.send_message(
        chat_id=context.user_data['chat_id'],
        text='Após efetuar o pagamento, clique no botão abaixo para verificar se o saldo foi atualizado.',
        reply_markup=reply_keyboard_payment_done,
    )

    return CHECK_PAYMENT

async def check_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    payment = await get_mp_payment(
        context.user_data['payment_id']
    )
    if payment.get('error'):
        await query.edit_message_text(
            'Ocorreu um erro ao verificar o pagamento, clique para tentar novamente.',
            reply_markup=reply_keyboard_payment_done,
        )
        return CHECK_PAYMENT

    if payment['status'] == 'approved':
        # deleta a mensagem com o QR code
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=context.user_data['photo_message_id'],
        )
        context.user_data['photo_message_id'] = None

        value = payment['value']
        data = {
            'email': context.user_data['email'],
            'balance': context.user_data['balance'] + float(value),
        }
        payment_data = {
            'client_id': context.user_data['client_id'],
            'price': value,
            'mercado_pago_id': context.user_data['payment_id'],
        }

        response_payment = await new_payment(payment_data)
        response_user = await update_client(data)

        if response_payment.get('error'):
            logging.error(response_payment.get('error'))

        if response_user.get('error'):
            await query.edit_message_text(
                'Ocorreu um erro ao atualizar seu saldo. Por favor, entre em contato com o suporte.'
            )
            return ConversationHandler.END

        context.user_data['balance'] += float(value)
        context.user_data['payment_id'] = None

        if context.user_data.get('start_directly'):
            context.user_data['start_directly'] = False
            for second in range(TIME_TO_START_QUIZ):
                await query.edit_message_text(
                    f'Você está pronto? O quiz iniciará em {TIME_TO_START_QUIZ - second} segundos.'
                )
                await asyncio.sleep(1)
            return await start_quiz(update, context)
        
        await query.edit_message_text(
            f"Saldo atualizado com sucesso! Seu novo saldo é de {context.user_data['balance']}R$.",
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU

    else:
        await query.edit_message_text(
            'Pagamento ainda não aprovado. Clique novamente para verificar.',
            reply_markup=reply_keyboard_payment_done,
        )
        return CHECK_PAYMENT


async def value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_value = query.data

    if selected_value == 'Cancelar':
        await query.edit_message_text(
            'Tudo bem! Você pode escolher uma nova opção no menu abaixo.',
            reply_markup=reply_keyboard_menu,
        )
        return OPTION

    context.user_data['selected_value'] = float(selected_value.split('R$')[0])

    await query.edit_message_text(
        f'Você escolheu investir {selected_value}. Está correto?',
        reply_markup=reply_keyboard_confirm,
    )
    return CONFIRM_VALUE


async def confirm_value(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    answer = query.data

    if answer == 'Sim':

        if context.user_data['balance'] > context.user_data['selected_value']:
            for second in range(TIME_TO_START_QUIZ):
                await query.edit_message_text(
                    f'Você está pronto? O quiz iniciará em {TIME_TO_START_QUIZ - second} segundos.'
                )
                await asyncio.sleep(1)
            return await start_quiz(update, context)

        else:
            await query.edit_message_text(
                'Você não possui saldo suficiente, faça o pagamento com o QR Code abaixo.',
            )
            context.user_data['start_directly'] = True
            return await add_balance(update, context, context.user_data['selected_value'])

    else:
        await query.edit_message_text(
            'Tudo certo! Basta escolher um novo valor para investir.',
            reply_markup=reply_keyboard_values,
        )
        return VALUE


async def start_quiz(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['balance'] -= context.user_data['selected_value']
    data_payment = {
        'client_id': context.user_data['client_id'],
        'price': context.user_data['selected_value'] * -1,
        'mercado_pago_id': 'none',
    }
    data = {
        'email': context.user_data['email'],
        'balance': context.user_data['balance'],
    }
    await new_payment(data_payment)
    response = await update_client(data)

    if response.get('error'):
        await query.edit_message_text(
            'Ocorreu um erro ao atualizar seu saldo. Por favor, tente novamente mais tarde.',
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU
    
    return await show_quiz(update, context)

async def choose_quiz(difficulty: int, context: ContextTypes.DEFAULT_TYPE) -> dict:
    quizzes = await get_quizzes(difficulty)
    not_played_quizzes = [quiz for quiz in quizzes if quiz['id'] not in context.user_data['played_quizzes']]

    if not not_played_quizzes:
        context.user_data['played_quizzes'] = []
        return random.choice(quizzes)
    return random.choice(not_played_quizzes)


async def show_quiz(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    if 'played_quizzes' not in context.user_data:
        context.user_data['played_quizzes'] = []

    price_to_diffilcuty_map = {
      VALUES[0]: 1, VALUES[1]: 2, VALUES[2]: 3, VALUES[3]: 3, VALUES[4]: 3,
    }
    difficulty = price_to_diffilcuty_map[context.user_data['selected_value']]
    chosen_quiz = await choose_quiz(difficulty, context)

    reply_keyboard_quiz = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(chosen_quiz["optionA"], callback_data='A'),
                InlineKeyboardButton(chosen_quiz["optionB"], callback_data='B'),
            ],
            [
                InlineKeyboardButton(chosen_quiz["optionC"], callback_data='C'),
                InlineKeyboardButton(chosen_quiz["optionD"], callback_data='D'),
            ],
        ]
    )

    context.user_data['correct_answer'] = chosen_quiz['correctOption']
    context.user_data['answered'] = False
    
    await query.edit_message_text(
        f"{chosen_quiz['question']} Você tem 5 segundos para responder.",
        reply_markup=reply_keyboard_quiz,
    )
    context.job_queue.run_once(
        timeout_callback, TIME_TO_ANSWER_QUIZ, data={'context': context, 'query': query}
    )

    context.user_data['played_quizzes'].append(chosen_quiz['id'])
    return CHECK_ANSWER

# TODO: ao clicar em cancelar na hora do pagamento, excluir o QR CODE
async def check_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:

    query = update.callback_query
    await query.answer()
    context.user_data['answered'] = True

    selected_answer = query.data

    if selected_answer not in ['A', 'B', 'C', 'D']:
        return await show_menu(update, context)

    if selected_answer == context.user_data['correct_answer']:
        context.user_data['correct_answers'] += 1
        if context.user_data['correct_answers'] == QUIZZES_TO_WIN:
          context.user_data['correct_answers'] = 0

          user_data = await get_user_data(context.user_data['chat_id'])
          prizes_map = {
            VALUES[0]: 100, VALUES[1]: 500, VALUES[2]: 700, VALUES[3]: 1000, VALUES[4]: 10000,
          }
          prize_value = prizes_map[context.user_data['selected_value']]

          if user_data.get('pix', '') == '':

              await query.edit_message_text(
                  f'Você ganhou {prize_value}! Seu prêmio será creditado em breve. Selecione o tipo de chave PIX que deseja cadastrar.',
                  reply_markup=reply_keyboard_pix_type,
              )
              
              prize_data = {
                  'client_id': context.user_data['client_id'],
                  'price': prize_value,
                  'status': 0,
              }
              await new_prize(prize_data)
              return PIX_TYPE
          else:
            await query.edit_message_text(
                f"Parabéns, você ganhou! Seu prêmio é de {prize_value}R$ e será creditado em breve.",
                reply_markup=reply_keyboard_return,
            )
            prize_data = {
                'client_id': context.user_data['client_id'],
                'price': prize_value,
                'status': 0,
            }
            await new_prize(prize_data)
            return SHOW_MENU
        else:
          for second in range(TIME_TO_START_QUIZ):
              await query.edit_message_text(
                  f"Parabéns! Você acertou a resposta. Próxima pergunta em {TIME_TO_START_QUIZ - second} segundos ({context.user_data['correct_answers']}/{QUIZZES_TO_WIN}).",
              )
              await asyncio.sleep(1)
          return await show_quiz(update, context)
    else:
        context.user_data['correct_answers'] = 0
        await query.edit_message_text(
            f"Que pena! Você errou a resposta. Seu saldo perdido foi de {context.user_data['selected_value']}R$.",
            reply_markup=reply_keyboard_return,
        )
        return SHOW_MENU


async def timeout_callback(context: CallbackContext):
    user_context: ContextTypes.DEFAULT_TYPE = context.job.data['context']
    query: Update = context.job.data['query']

    await asyncio.sleep(0.2)

    if user_context.user_data.get('answered') is False:
        user_context.user_data['correct_answers'] = 0
        await query.edit_message_text(
            f'Que pena! O tempo acabou. Seu saldo perdido foi de {user_context.user_data["selected_value"]}R$.',
            reply_markup=reply_keyboard_return,
        )


async def cancel_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    if context.user_data.get('photo_message_id', None):
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=context.user_data['photo_message_id'],
        )
        context.user_data['photo_message_id'] = None

    await query.edit_message_text('Até mais! Digite /start para reiniciar o bot.')
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a conversa e finaliza o bot"""
    await update.message.reply_text('Até mais!')
    return ConversationHandler.END


def main() -> None:
    token = (
        os.getenv('TELEGRAM_KEY')
        or '7164176762:AAHgcZ__UPWDC7xK5LrpbymUSvPFVe_edAg'
    )
    persistence = PicklePersistence(filepath='quizmybot')
    application = Application.builder().token(token).persistence(persistence).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT, email)],
            CONFIRM_EMAIL: [
                CallbackQueryHandler(confirm_email, pattern='^(Sim|Não)$')
            ],
            PIX_TYPE: [
                CallbackQueryHandler(
                    pix_type,
                    pattern='^(CPF|CNPJ|Chave aleatória|Email|Telefone|Cancelar)$',
                )
            ],
            PIX: [
                CallbackQueryHandler(
                    show_pix_type_menu, pattern='^(Mudar tipo de chave)$'
                ),
                MessageHandler(filters.TEXT, pix),
            ],
            CONFIRM_PIX: [
                CallbackQueryHandler(confirm_pix, pattern='^(Sim|Não)$')
            ],
            OPTION: [
                CallbackQueryHandler(
                    start_quiz_option, pattern='^(Iniciar quiz)$'
                ),
                CallbackQueryHandler(
                    add_balance_option, pattern='^(Recarregar saldo)$'
                ),
                CallbackQueryHandler(
                    verify_balance_option, pattern='^(Verificar saldo)$'
                ),
                CallbackQueryHandler(
                    change_pix_option, pattern='^(Mudar chave PIX)$'
                ),
                CallbackQueryHandler(
                    show_balance_history_option,
                    pattern='^(Histórico de saldo)$',
                ),
                CallbackQueryHandler(
                    show_prizes_option, pattern='^(Meus prêmios)$'
                ),
                CallbackQueryHandler(cancel_query, pattern='^(Cancelar)$'),
            ],
            GET_BALANCE: [MessageHandler(filters.TEXT, get_balance)],
            SHOW_MENU: [
                CallbackQueryHandler(show_menu, pattern='^(Retornar ao menu)$')
            ],
            VALUE: [
                CallbackQueryHandler(
                    value,
                    pattern=f'^({VALUES[0]}R\$|{VALUES[1]}R\$|{VALUES[2]}R\$|{VALUES[3]}R\$|{VALUES[4]}R\$|Cancelar)$',
                )
            ],
            CONFIRM_VALUE: [
                CallbackQueryHandler(confirm_value, pattern='^(Sim|Não)$')
            ],
            START_QUIZ: [
                CallbackQueryHandler(start_quiz, pattern='^(A|B|C|D)')
            ],
            CHECK_ANSWER: [CallbackQueryHandler(check_answer)],
            CHECK_PAYMENT: [
                CallbackQueryHandler(check_payment, pattern='^(Verificar)$'),
                CallbackQueryHandler(show_menu, pattern='^(Cancelar)$'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start),
        ],
        name='quizmybot',
        persistent=True,
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    login()
    main()
