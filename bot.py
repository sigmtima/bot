import disnake
from disnake.ext import commands
import os

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True # ОБЯЗАТЕЛЬНО для работы выдачи ролей по реакциям

bot = commands.Bot(command_prefix="!", intents=intents)

TICKET_FILE = "ticket_number.txt"

# ================= КОНФИГУРАЦИЯ БОТА =================
STAFF_ROLE_ID = 1554819278732009513  # ID роли ▷Staff◁

# ID трех определенных людей, которые будут пинговаться и видеть тикеты по донату
DONATE_ADMIN_IDS = [
    1123241329250541679,  # Админ 1
    1127828224953552917,  # Админ 2
    1313309595535413309   # Админ 3
]

# Настройка ролей по реакциям: "Эмодзи": ID_роли
REACTION_ROLES = {
    "📢": 1558461101723885679,  # Например, Оповещение
    "🎮": 1558461166374879232,  # Например, Геймер
    "🎁": 1558461205184651344   # Еще какая-то роль
}
# ======================================================

def get_next_ticket_number():
    if not os.path.exists(TICKET_FILE):
        with open(TICKET_FILE, "w") as f:
            f.write("1")
        return 1
    try:
        with open(TICKET_FILE, "r") as f:
            number = int(f.read().strip())
    except:
        number = 1
    
    with open(TICKET_FILE, "w") as f:
        f.write(str(number + 1))
    return number

# ================= ОКНО 1: ЖАЛОБЫ И ОБРАЩЕНИЯ =================
class TicketDropdown(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label="Жалоба на игрока", value="player_report", description="Подать жалобу на нарушителя", emoji="😈"),
            disnake.SelectOption(label="Разбан / апелляция", value="unban_appeal", description="Запрос на снятие наказания", emoji="❤️"),
            disnake.SelectOption(label="Превышение полномочий", value="abuse_report", description="Жалоба на админ-права", emoji="⚔️"),
            disnake.SelectOption(label="Вопрос администрации", value="admin_question", description="Задать вопрос по проекту", emoji="❓"),
        ]
        super().__init__(placeholder="Выберите тип обращения", options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: disnake.MessageInteraction):
        selected = interaction.values[0]
        guild = interaction.guild
        member = interaction.user

        titles = {
            "player_report": "Жалоба на игрока",
            "unban_appeal": "Разбан / апелляция",
            "abuse_report": "Превышение полномочий",
            "admin_question": "Вопрос администрации"
        }
        topic_title = titles.get(selected, "Обращение")

        await interaction.response.send_message("Создаю канал для обращения...", ephemeral=True)
        ticket_num = get_next_ticket_number()

        # Права: Скрыто от всех, видно автору и роли Staff
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            member: disnake.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        staff_role = guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = disnake.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await guild.create_text_channel(name=f"жалоба-{ticket_num}", overwrites=overwrites)

        embed = disnake.Embed(
            title=f"📋 {topic_title} от {member.display_name}",
            description=f"Здравствуйте, {member.mention}. Спасибо за обращение в службу поддержки.\nПеред написанием обращения ознакомьтесь с нашими правилами.\n\n"
                        f"**Пожалуйста, подробно опишите свою жалобу:**\n```* Ник потерпевшего\n* Ник или Steam нарушителя\n* Опишите суть вашей жалобы```\n"
                        f"Наша команда Staff ответит вам в ближайшее время.",
            color=disnake.Color.blue()
        )
        embed.set_footer(text="TRH Bot • Сегодня", icon_url=bot.user.display_avatar.url)

        # Отправляем эмбед и ПИНГУЕМ роль Staff через специальный синтаксис <@&ID>
        await channel.send(content=f"<@&{STAFF_ROLE_ID}> | 🎄 Тема обращения: **{topic_title}**", embed=embed)

class DropdownView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


# ================= ОКНО 2: ПОКУПКА ДОНАТА (ОТДЕЛЬНОЕ) =================
class DonateDropdown(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label="Купить донат", value="donate_shop", description="Открыть тикет для покупки доната", emoji="💎"),
        ]
        super().__init__(placeholder="Нажмите, чтобы купить донат", options=options, custom_id="donate_select_menu")

    async def callback(self, interaction: disnake.MessageInteraction):
        guild = interaction.guild
        member = interaction.user

        await interaction.response.send_message("Создаю секретный канал для доната...", ephemeral=True)
        ticket_num = get_next_ticket_number()

        # Права: Закрыто для всех, открыто автору
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            member: disnake.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        # Открываем доступ ТОЛЬКО для 3-х админов из списка
        for admin_id in DONATE_ADMIN_IDS:
            admin_member = guild.get_member(admin_id)
            if admin_member:
                overwrites[admin_member] = disnake.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await guild.create_text_channel(name=f"донат-{ticket_num}", overwrites=overwrites)

        embed = disnake.Embed(
            title=f"📋 Покупка доната от {member.display_name}",
            description=f"Здравствуйте, {member.mention}. Вы открыли тикет для покупки доната.\n\n"
                        f"Данный канал видите **только вы и руководство проекта**. Персонал сервера сюда доступа не имеет.\n\n"
                        f"Пожалуйста, напишите, какой товар или услугу вы хотите приобрести, и ожидайте ответа.",
            color=disnake.Color.gold()
        )
        embed.set_footer(text="TRH Bot • Сегодня", icon_url=bot.user.display_avatar.url)

        # Собираем строчку из пингов всех трех админов <@ID>
        admin_pings = " ".join([f"<@{admin_id}>" for admin_id in DONATE_ADMIN_IDS])

        # Отправляем эмбед и ПИНГУЕМ 3-х админов
        await channel.send(content=f"{admin_pings} | 💎 Новый тикет на покупку доната!", embed=embed)

class DonateView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DonateDropdown())


# ================= ТЕКСТОВЫЕ КОМАНДЫ ДЛЯ ВЫЗОВА ОКН =================

# Команда для вызова Жалоб
@bot.command()
async def setup_tickets(ctx):
    await ctx.send("Добро пожаловать в систему поддержки!\nВыберите тип обращения ниже:", view=DropdownView())

# Команда для вызова Доната (ТЕПЕРЬ ОТДЕЛЬНО!)
@bot.command()
async def setup_donate(ctx):
    await ctx.send("Желаете приобрести донат и поддержать проект?\nИспользуйте меню ниже для связи с руководством:", view=DonateView())

# Команда создания выбора ролей по реакциям
@bot.command()
async def setup_roles(ctx):
    embed = disnake.Embed(
        title="🎭 Получение ролей",
        description="Нажмите на соответствующие реакции под этим сообщением, чтобы получить нужные роли:\n\n"
                    "📢 — **Оповещения** (новости проекта)\n"
                    "🎮 — **Геймер** (поиск напарников)\n"
                    "🎁 — **Ивенты / Раздачи**",
        color=disnake.Color.purple()
    )
    message = await ctx.send(embed=embed)
    for emoji in REACTION_ROLES.keys():
        await message.add_reaction(emoji)


# ================= ОБРАБОТКА РЕАКЦИЙ (ВЫДАЧА РОЛЕЙ) =================
@bot.event
async def on_raw_reaction_add(payload: disnake.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    emoji_name = str(payload.emoji)
    if emoji_name in REACTION_ROLES:
        guild = bot.get_guild(payload.guild_id)
        if not guild: return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(REACTION_ROLES[emoji_name])
        if member and role:
            await member.add_roles(role)
            try:
                await member.send(f"✅ Вы успешно получили роль **{role.name}** на сервере **{guild.name}**!")
            except disnake.Forbidden: pass

@bot.event
async def on_raw_reaction_remove(payload: disnake.RawReactionActionEvent):
    emoji_name = str(payload.emoji)
    if emoji_name in REACTION_ROLES:
        guild = bot.get_guild(payload.guild_id)
        if not guild: return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(REACTION_ROLES[emoji_name])
        if member and role:
            await member.remove_roles(role)
            try:
                await member.send(f"❌ У вас была забрана роль **{role.name}** на сервере **{guild.name}**.")
            except disnake.Forbidden: pass


@bot.event
async def on_ready():
    # Регистрируем оба окна, чтобы кнопки не ломались после перезапуска бота
    bot.add_view(DropdownView())
    bot.add_view(DonateView())
    print(f"Бот {bot.user} успешно запущен и готов к работе!")

# Запуск бота из переменной окружения
bot.run(os.getenv("BOT_TOKEN")) 

