import os
import tweepy
import openai
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Twitter API credentials
client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    wait_on_rate_limit=True
)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Persistent storage for processed IDs
PROCESSED_IDS_FILE = "processed_ids.txt"

def load_processed_ids():
    """Load processed IDs from file."""
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_processed_id(comment_id):
    """Save a processed comment ID to file."""
    with open(PROCESSED_IDS_FILE, "a") as f:
        f.write(f"{comment_id}\n")

processed_comment_ids = load_processed_ids()

def get_user_id(username):
    """Fetch the user ID for the given username."""
    try:
        user = client.get_user(username=username)
        return user.data.id
    except Exception as e:
        print(f"Error fetching user ID for {username}: {e}")
        raise

def generate_reply(comment_text):
    """Generate a funny and sarcastic reply using OpenAI."""
    try:
        prompt = f"Reply with a funny and sarcastic comment to: '{comment_text}'"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50,
            temperature=0.8,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating reply: {e}")
        return "Oops! My sarcasm circuits are overloaded! 😂"

def reply_to_comments(username):
    """Fetch and reply to new comments."""
    try:
        print(f"Fetching tweets for {username}...")
        user_id = get_user_id(username)

        # Fetch the most recent tweet
        tweets = client.get_users_tweets(id=user_id, max_results=1)  # Only process the latest tweet
        if not tweets.data:
            print("No tweets found.")
            return

        tweet = tweets.data[0]
        tweet_id = tweet.id
        print(f"Processing comments for tweet ID: {tweet_id}")

        # Fetch recent replies to the tweet
        query = f"conversation_id:{tweet_id}"
        comments = client.search_recent_tweets(query=query, max_results=3)  # Limit to 3 comments per tweet

        if not comments.data:
            print(f"No comments found for tweet ID: {tweet_id}")
            return

        for comment in comments.data:
            if comment.id in processed_comment_ids:
                continue  # Skip already processed comments

            text = comment.text
            author_id = comment.author_id
            print(f"Found comment from user ID {author_id}: {text}")

            # Generate a reply
            reply_text = generate_reply(text)
            print(f"Replying with: {reply_text}")

            # Post the reply
            client.create_tweet(
                text=f"@{author_id} {reply_text}",
                in_reply_to_tweet_id=comment.id
            )
            print(f"Replied to comment ID: {comment.id}")

            # Track processed comment
            processed_comment_ids.add(comment.id)
            save_processed_id(comment.id)

    except tweepy.errors.TooManyRequests as e:
        reset_time = int(e.response.headers.get("x-rate-limit-reset", time.time() + 900))
        sleep_time = reset_time - int(time.time())
        print(f"Rate limit reached. Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
    except Exception as e:
        print(f"Unexpected error: {e}")

def start_bot():
    """Run the bot continuously with extended intervals."""
    username = "mikasa_model"  # Target account username
    while True:
        reply_to_comments(username)
        time.sleep(3600)  # Wait 60 minutes before polling again

if __name__ == "__main__":
    start_bot()
