import csv
import asyncio
import nest_asyncio
from telethon import TelegramClient

api_id = '28214123'
api_hash = '0d8e7da7edbd6d72a622ea60dfe3ac18'
phone = '+918828000465'

# Create a client
client = TelegramClient('MyApp12345new1234567ab', api_id, api_hash)

async def main():
    # Start the client and log in
    await client.start(phone)

    # Access messages from a public group or channel
    group_name = '@TechCrunch1'  # Replace with actual public group name or ID

    # Create a new CSV file for each message
    async for i, message in enumerate(client.iter_messages(group_name, limit=100)):
        filename = f'telegram_message_{i+1}.csv'  # Unique filename for each message
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['sender_id', 'message_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()  # Write the header row

            writer.writerow({
                'sender_id': message.sender_id,
                'message_text': message.text
            })

            print(f"Message from {message.sender_id} saved to {filename}: {message.text}")

# Run the program
nest_asyncio.apply()
asyncio.run(main())
