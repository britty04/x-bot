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

# Track processed comment IDs
processed_comment_ids = set()

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

        # Fetch up to 5 recent tweets
        tweets = client.get_users_tweets(id=user_id, max_results=5)  # Fetch at least 5 tweets
        if not tweets.data:
            print("No tweets found.")
            return

        # Process only the most recent tweet
        tweet = tweets.data[0]
        tweet_id = tweet.id
        print(f"Processing comments for tweet ID: {tweet_id}")

        # Fetch recent replies to the tweet
        query = f"conversation_id:{tweet_id}"
        comments = client.search_recent_tweets(query=query, max_results=5)  # Limit to 5 comments

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

    except tweepy.errors.TooManyRequests:
        print("Rate limit reached. Sleeping for 15 minutes...")
        time.sleep(900)  # Wait for 15 minutes
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
