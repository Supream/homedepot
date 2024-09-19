import requests
import json
from dhooks import Webhook, Embed
import time
from datetime import datetime
import discord
from discord.ext import commands
from threading import Thread
# https://www.homedepot.com/mcc-cart/v2/info/storefulfillment?itemId=307244559&keyword=628
# Item 307244559
# Store 628

def monitor(product, store_num):
    link = 'https://www.homedepot.com/p/{}'.format(product)

    headers = {
        'authority': 'www.homedepot.com',
        'cache-control': 'max-age=0',
        'accept': 'application/json;charset=utf-8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        'content-type': 'text/plain',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'en-US,en;q=0.9',
        }
    page = requests.get('https://www.homedepot.com/mcc-cart/v2/info/storefulfillment?itemId={}&keyword={}'.format(product, store_num), headers=headers)
    res = page.json()

    #print(res)

    product_info = res['storeFulfillment']['storeFulfillmentDetails']
    title = product_info['sku']['title']
    image = product_info['sku']['media']['mediaEntry']['location']

    #Create dict of stores w/ on-hand qty
    inventory = {}

    #Add the primary store manually
    primary = product_info['primaryStore']
    primary_name = primary['name'] + ' #' + primary['storeId']
    inventory[primary_name] = primary['fulfillmentOptions']['buyOnlinePickupInStore']['inventory']['onHandQuantity']

    #Loop through the rest of the stores within 100mi
    for store in product_info['alternateStores']['store']:
        inventory[store['name'] + ' #' + store['storeId']] = store['fulfillmentOptions']['buyOnlinePickupInStore']['inventory']['onHandQuantity']
    

    return inventory, title, image, link, store_num

def webhook_main(result):
    inventory = result[0]
    title = result[1]
    image = result[2]
    link = result[3]
    store_num = result[4]

    hook = Webhook('https://discord.com/api/webhooks/738868466345443392/ZpfkRsInSOOXbIuIZWqsBPgahrz5eYlXvHVDJKdA-kpub-4_hIRfFOqvo5YnUtWStQ3S')
    embed = Embed(
        description = '**Nearby Store #{}**'.format(store_num),
        color = 0xff6600,
        timestamp = 'now'
    )
    embed.set_author(name=title, icon_url=image, url=link)
    for key in inventory:
        embed.add_field(name='{}'.format(key), value='On Hand: ```py\n{}\n```'.format(inventory[key]), inline=True)
        #embed.add_field(name='On Hand:', value=inventory[key], inline=False)

    embed.set_footer(text='created by enrique#2519', icon_url='https://cdn.discordapp.com/avatars/267782036893204481/58904351e4e12eec9302b22cd6b209d9.webp?size=256')

    hook.send(embed=embed)

    return inventory

def webhook_update(change, store, qty):
    hook = Webhook('https://discord.com/api/webhooks/738868466345443392/ZpfkRsInSOOXbIuIZWqsBPgahrz5eYlXvHVDJKdA-kpub-4_hIRfFOqvo5YnUtWStQ3S')
    embed = Embed(
        description = '{}\n{}\n{}'.format(change, store, qty)
    )
    hook.send(embed=embed)


def check_for_updates(status):
    update = monitor('307244559', '628')[0]

    if status == update:
        print('[{}]\t NO CHANGES MADE'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return update
    else:
        #If the store list hasn't changed, the quantity must have changed
        if list(status.keys()) == list(update.keys()):
            for store in status:
                if status[store] != update[store]:
                    webhook_update('**Quantity Change:**', store, update[store])
                    print('[{}]\tQUANTITY CHANGE: {}\nNEW QUANTITY: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), store, update[store]))
                    return update
        else:
            #Check for stores that are no longer in the list
            for store in status:
                if store not in update:
                    webhook_update('**Cleaned Out:**', store, '-')
                    print('[{}]\tCLEANED OUT: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), store))
                    return update
            #Check for stores that have been added to the list
            for u_store in update:
                if u_store not in status:
                    webhook_update('**Store Added:**', store, '-')
                    print('[{}]\tSTORE ADDED: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), u_store))
                    return update
    return update

def run():
    status = monitor('307244559', '628')[0]
    while True:
        status = check_for_updates(status)
        time.sleep(60)

def discord_bot():
    bot = discord.Client()
    @bot.event
    async def on_ready():
        print('Bot is ready.')
    @bot.event
    async def on_message(message):
        if message.content.startswith('-stock'):
            webhook_main(monitor('307244559', '628'))
    bot.run('NzM4ODkxODMzNTgwNDUzOTE4.XySgpQ.l_02x2FeL3RPrKXk8uGb5Cx7D5w')

    
if __name__ == '__main__':
    #bot = commands.Bot(command_prefix='-')
    t = Thread(target=run)
    t.start()

    bot = discord.Client()

    @bot.event
    async def on_ready():
        print('Bot is ready.')


    @bot.event
    async def on_message(message):
        if message.content.startswith('-stock'):
            if message.content == '-stock':
                webhook_main(monitor('307244559', '628'))
            else:
                m = message.content.split(' ')[1]
                try:
                    webhook_main(monitor('307244559', m))
                except:
                    await message.channel.send('Error locating stock for Store # {}'.format(m))
    bot.run('NzM4ODkxODMzNTgwNDUzOTE4.XySgpQ.l_02x2FeL3RPrKXk8uGb5Cx7D5w')


#webhook(monitor('307244559', '628'))