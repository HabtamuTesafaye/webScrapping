import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import telegram
from io import BytesIO

# Set up the Telegram bot using environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
bot = telegram.Bot(token=bot_token)

# Set up the set to store the URLs
posted_urls = set()
url = 'https://www.npr.org/sections/news/'

async def scrape_npr_news():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=60) as response:
                    soup = BeautifulSoup(await response.text(), 'html.parser')

                    articles = soup.find_all('article', class_='item')
                    for article in articles:
                        article_url = article.find('a')['href']
                        headline = article.find('h2', class_='title').text.strip()
                        image = article.find('img', class_='respArchListImg')
                        detail = article.find('p', class_='teaser').text.strip()
                        
                        photo = None
                        if image:
                            image_url = image['src']
                            if not image_url.startswith('http'):
                                image_url = f"{url}{image_url}"
                            async with session.get(image_url) as img_response:
                                photo = BytesIO(await img_response.read())

                        if article_url not in posted_urls:
                            caption = f"'{headline}'\n\n{detail}\n'Read more by the link below'\n{article_url}"
                            if photo:
                                await bot.send_photo(chat_id=chat_id, photo=photo.getvalue(), caption=caption)
                            else:
                                await bot.send_message(chat_id=chat_id, text=caption)
                            posted_urls.add(article_url)

            await asyncio.sleep(900)  # Sleep for 15 minutes
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"HTTP request error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute
        except telegram.error.TelegramError as e:
            print(f"Telegram API error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute
        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

if __name__ == '__main__':
    asyncio.run(scrape_npr_news())
