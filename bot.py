import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Substitua pelo token do seu bot
TOKEN = "7842548013:AAEu-fDDiVPWj2xZBmkn6PHnEe2j0nE-WC4"

# Cardápio do restaurante
MENU = {
    "1": {"name": "Tacos", "price": 10.00},
    "2": {"name": "Burritos", "price": 15.00},
    "3": {"name": "Nachos", "price": 12.00},
    "4": {"name": "Quesadilla", "price": 14.00},
}

# Configurações da chave PIX
PIX_KEY = "450.352.438-00"

# Conexão com o banco de dados SQLite
def init_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      customer_name TEXT, 
                      address TEXT, 
                      item_name TEXT, 
                      payment_method TEXT)''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia a conversa com o usuário."""
    await update.message.reply_text(
        "Bem-vindo ao Las Noches! Digite /menu para ver nosso cardápio."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra o cardápio."""
    text = "Cardápio:\n"
    for key, item in MENU.items():
        text += f"{key}. {item['name']} - R$ {item['price']:.2f}\n"
    text += "\nEscolha um item digitando o número correspondente."
    await update.message.reply_text(text)

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe o pedido do cliente."""
    item = MENU.get(update.message.text)
    if item:
        context.user_data['order'] = item
        await update.message.reply_text(
            f"Você escolheu {item['name']}. Por favor, envie seu nome para prosseguir."
        )
        context.user_data['step'] = 'name'
    else:
        await update.message.reply_text("Opção inválida. Tente novamente.")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe o nome do cliente."""
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("Obrigado! Agora, por favor, envie seu endereço para entrega.")
    context.user_data['step'] = 'address'

async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe o endereço do cliente."""
    context.user_data['address'] = update.message.text
    await update.message.reply_text(
        "Obrigado! Qual a forma de pagamento que você prefere?\nDigite:\n1. Dinheiro\n2. Cartão\n3. PIX"
    )
    context.user_data['step'] = 'payment'

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe a forma de pagamento do cliente e finaliza o pedido."""
    payment_methods = {'1': 'Dinheiro', '2': 'Cartão', '3': 'PIX'}
    payment_method = payment_methods.get(update.message.text)
    
    if payment_method:
        order = context.user_data.get('order')
        customer_name = context.user_data.get('customer_name')
        address = context.user_data.get('address')
        
        # Salva o pedido no banco de dados
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (customer_name, address, item_name, payment_method) VALUES (?, ?, ?, ?)",
                       (customer_name, address, order['name'], payment_method))
        conn.commit()
        conn.close()
        
        if payment_method == 'PIX':
            await update.message.reply_text(
                f"Seu pedido de {order['name']} será entregue em breve no endereço: {address}. "
                f"Por favor, faça o pagamento de R$ {order['price']:.2f} usando a chave PIX: {PIX_KEY}. Obrigado, {customer_name}!"
            )
        else:
            await update.message.reply_text(
                f"Seu pedido de {order['name']} será entregue em breve no endereço: {address}. "
                f"Você escolheu pagar com {payment_method}. Obrigado, {customer_name}!"
            )
    else:
        await update.message.reply_text("Opção de pagamento inválida. Tente novamente.")

def main() -> None:
    """Inicia o bot."""
    init_db()  # Inicializa o banco de dados
    
    # Cria a aplicação do bot
    application = Application.builder().token(TOKEN).build()

    # Configura comandos e respostas
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(MessageHandler(filters.Regex('^(1|2|3|4)$'), handle_order))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name, pass_user_data=True))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address, pass_user_data=True))
    application.add_handler(MessageHandler(filters.Regex('^(1|2|3)$'), handle_payment, pass_user_data=True))

    # Inicia o bot
    application.run_polling()

if __name__ == "__main__":
    main()
