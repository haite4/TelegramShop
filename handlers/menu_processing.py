from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
import os
import aiohttp
from data.orm_query import *
from kbds.inline import (
    get_products_btns,
    get_user_cart,
    get_user_catalog_btns,
    get_user_main_btns,
    get_payments_btn
)

from utils.paginator import Paginator
from aiogram import types
import config
from decimal import Decimal

async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=level)

    return image, kbds


async def catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    print(banner.image)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session)
    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def products(session, level, category, page):
    products = await orm_get_products(session, category_id=category)

    paginator = Paginator(products, page=page)
    product = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=product.image,
        caption=f"<strong>{product.name}\
                </strong>\n{product.description}\nСтоимость: {round(product.price)} Руб\n\
                <strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )

    return image, kbds


        

async def carts(session, level, menu_name, page, user_id, product_id):
    if menu_name == "delete":
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart:
            page -= 1
    elif menu_name == "increment":
        await orm_add_to_cart(session, user_id, product_id)

    carts = await orm_get_user_carts(session, user_id)

    if not carts:
        banner = await orm_get_banner(session, "cart")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>"
        )

        kbds = get_user_cart(
            level=level,
            page=None,
            pagination_btns=None,
            product_id=None,
        )

    else:
        paginator = Paginator(carts, page=page)

        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(
            sum(cart.quantity * cart.product.price for cart in carts), 2    
        )
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n{round(cart.product.price,2)} Руб x {cart.quantity} = {cart_price} Руб\
                    \nТовар {paginator.page} из {paginator.pages} в корзине.\nОбщая стоимость товаров в корзине {total_price} Руб",
        )

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=cart.product.id,
        )

    return image, kbds


    

async def order(session:AsyncSession, level, menu_name):
    if menu_name == "order":
            banner = await orm_get_banner(session, menu_name)
            image = InputMediaPhoto(media=banner.image, caption=banner.description)
            categories = await orm_get_categories(session)
            kbds = get_payments_btn(level=level)

            return image, kbds


async def qiwi_payment(session:AsyncSession,level,menu_name,user_id):
    if menu_name == "qiwi":
            banner = await orm_get_banner(session, menu_name)
            
            kbds = get_payments_btn(level=level)
            cart = await orm_get_user_carts(session,user_id)
            total_price = round(
                sum(item.quantity * item.product.price for item in cart), 2    
            )
            descriptions = []
            for item in cart:
                print(item.product.name)
                cart_price = round(item.quantity * item.product.price, 2)
                description = f"<strong>{item.product.name}</strong>\n{round(item.product.price,2)} Руб x {item.quantity} = {cart_price} Руб"
                descriptions.append(description)
            wallet_link = "https://qiwi.com/n/WHEYE116"
            caption = '\n'.join(descriptions) + f"\n------------------------------------------------\nСумма к оплате: {total_price} Руб \n------------------------------------------------\nДля оплаты переведите сумму на кошелек: <a href='{wallet_link}'>Кошелек Qiwi</a>"
            image = InputMediaPhoto(media=banner.image, caption=caption)
            return image, kbds


api_exchange = config.EXCHANGE_API
async def get_exchange_rate(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data =  await response.json()
            return data



async def crypto_payment(session:AsyncSession,level,menu_name,user_id):
    if menu_name == "crypto":
        banner = await orm_get_banner(session, menu_name)
        kbds = get_payments_btn(level=level)

        cart = await orm_get_user_carts(session,user_id)
        total_price = round(
                sum(item.quantity * item.product.price for item in cart), 2    
            )

        exchange_rate_data = await get_exchange_rate(f"https://v6.exchangerate-api.com/v6/{api_exchange}/pair/RUB/USD/{total_price}")
        result_exchange_price = exchange_rate_data["conversion_result"]
       
        descriptions = []
        for item in cart:
            print(item.product.name)
            cart_price = round(item.quantity * item.product.price, 2)
            description = f"<strong>{item.product.name}</strong>\n{round(item.product.price,2)} Руб x {item.quantity} = {cart_price} Руб"
            descriptions.append(description)
        caption = '\n'.join(descriptions) + f"\n------------------------------------------------\nСумма к оплате: {total_price} Руб  = {result_exchange_price} $\n------------------------------------------------\nКрипто кошельки для оплаты 👇 \n\nTether USDT  (ERC20)  <b>0x2329b90b45Ee543A43aE8b1E82067591533de08c</b>\n\nTether USDT (BEP20)  <b>0x2329b90b45Ee543A43aE8b1E82067591533de08c</b>"
        image = InputMediaPhoto(media=banner.image, caption=caption)
        return image, kbds



async def other_payment(session:AsyncSession,level,menu_name,user_id):
    if menu_name == "other":
        banner = await orm_get_banner(session, menu_name)
        kbds = get_payments_btn(level=level)
        
        cart = await orm_get_user_carts(session,user_id)
        total_price = round(
                sum(item.quantity * item.product.price for item in cart), 2    
            )

       
        descriptions = []
        for item in cart:
            print(item.product.name)
            cart_price = round(item.quantity * item.product.price, 2)
            description = f"<strong>{item.product.name}</strong>\n{round(item.product.price,2)} Руб x {item.quantity} = {cart_price} Руб"
            descriptions.append(description)
        caption = '\n'.join(descriptions) + f"\n------------------------------------------------\nСумма к оплате: {total_price} Руб \n------------------------------------------------\n Данний метод оплаты временно не доступен"
        image = InputMediaPhoto(media=banner.image, caption=caption)
        return image, kbds





async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    page: int | None = None,
    product_id: int | None = None,
    user_id: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await products(session, level, category, page)
    elif level == 3:
        return await carts(session, level, menu_name, page, user_id, product_id)
    elif level == 4:
        return await order(session,level,menu_name)
    elif level == 5:
        return await qiwi_payment(session,level,menu_name,user_id)
    elif level == 6:
        return await crypto_payment(session,level,menu_name,user_id)
    elif level == 7:
        return await other_payment(session,level,menu_name,user_id)
  

