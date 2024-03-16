from string import punctuation
from aiogram import Router,F
from filters.chat_types import ChatTypeFilter
from aiogram import types,Bot
from aiogram.filters import Command




user_group = Router()

user_group.message.filter(ChatTypeFilter(["group"]))



restricted_words = {"пидор","пидорас","тварь",
                    "хохол","уебище","скам","кидок",
                    "гандон","животное","пидрила",
                    "хуйня","шлюха","блядуха","выебал",
                    "ничтожество","пидорасина",
                    "уебище","шлюхи","пидор","пидар"
                    }



@user_group.message(Command("admin"))
async def get_admins(message:types.Message, bot:Bot):
        chat_id = message.chat.id
        admins_list = await bot.get_chat_administrators(chat_id=chat_id)
        
        admins_list = [
                member.user.id
                for member in admins_list
                if member.status == "creator" or member.status == "administrator"
        ]
        

        bot.my_admins_list = admins_list
        if message.from_user.id in admins_list:
                await message.delete()



def clean_text(text:str):
        return text.translate(str.maketrans('', '', punctuation))



@user_group.message()
async def cleaner(message:types.Message):
    
        if restricted_words.intersection(clean_text(message.text.lower()).split()):
                await message.answer(f"{message.from_user.username}, соблюдайте правила в чате!")
                await message.delete()