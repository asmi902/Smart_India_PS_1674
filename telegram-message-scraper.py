pip install pandas openpyxl
import csv
import asyncio
import nest_asyncio
import pandas as pd
from telethon import TelegramClient

api_id = '28214123'
api_hash = '0d8e7da7edbd6d72a622ea60dfe3ac18'
phone = '+918828000465'

client = TelegramClient('MyApp12345new1234567abcdef', api_id, api_hash)

async def main():
    await client.start(phone)

    group_name = 'https://t.me/maalbechenge'  # Replace with actual public group name or ID

    message_data = []

    async for message in client.iter_messages(group_name, limit=100):
        sender = await message.get_sender()
        sender_name = sender.username or sender.first_name or 'Unknown'
        sender_id = message.sender_id
        phone_number = getattr(sender, 'phone', 'Not available')

        message_data.append({
            'sender_name': sender_name,
            'sender_id': sender_id,
            'phone_number': phone_number,
            'message_text': message.text
        })

        print(f"Message from {sender_name} ({sender_id}, {phone_number}): {message.text}")

    with open('telegram_messages3.csv', 'w', newline='') as csvfile:
        fieldnames = ['sender_name', 'sender_id', 'phone_number', 'message_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # Write the header row
        writer.writerows(message_data)

    df = pd.DataFrame(message_data)
    df.to_excel('telegram_messages3.xlsx', index=False)

nest_asyncio.apply()
asyncio.run(main())
