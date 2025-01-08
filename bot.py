import os
import tweepy
import openai
import time
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    wait_on_rate_limit=True
)

openai.api_key = os.getenv("OPENAI_API_KEY")

last_processed_comment_id = None

def get_user_id(username):
    if not hasattr(get_user_id, "cached_id"):
        user = client.get_user(username=username)
        get_user_id.cached_id = user.data.id
    return get_user_id.cached_id

def generate_reply(comment_text):
    try:
        prompt = f"Reply with a funny and sarcastic comment to: '{comment_text}'"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=30,
            temperature=0.8,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating reply: {e}")
        return "Oops! My sarcasm circuits are overloaded! 😂"

def reply_to_comments():
    global last_processed_comment_id
    try:
        print("Fetching your tweets...")
        username = "your_twitter_username"  # Replace with your username
        user_id = get_user_id(username)

        tweets = client.get_users_tweets(id=user_id, max_results=5)
        if not tweets.data:
            print("No tweets found.")
            return

        for tweet in tweets.data:
            tweet_id = tweet.id
            print(f"Checking comments for tweet ID: {tweet_id}")

            query = f"to:{username}"
            comments = client.search_recent_tweets(query=query, since_id=tweet_id, max_results=10)

            if not comments.data:
                print("No comments found.")
                continue

            for comment in comments.data:
                if last_processed_comment_id and comment.id <= last_processed_comment_id:
                    continue

                if "referenced_tweets" in comment.data and comment.data["referenced_tweets"][0]["id"] == tweet_id:
                    text = comment.text
                    print(f"Found comment: {text}")
                    reply_text = generate_reply(text)
                    print(f"Replying: {reply_text}")
                    client.create_tweet(text=reply_text, in_reply_to_tweet_id=comment.id)
                    last_processed_comment_id = comment.id
    except tweepy.errors.TooManyRequests as e:
        print("Rate limit hit, waiting...")
        time.sleep(900)  # Wait 15 minutes
    except Exception as e:
        print(f"Unexpected error: {e}")

def start_bot():
    while True:
        reply_to_comments()
        time.sleep(60)  # Check every 1 minute

thread = Thread(target=start_bot)
thread.start()
