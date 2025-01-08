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
    wait_on_rate_limit=True  # Automatically handle rate limits
)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Track last processed comment timestamp
last_processed_time = datetime.utcnow() - timedelta(minutes=5)  # Start 5 minutes in the past
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

def reply_to_new_comments(username):
    """Fetch and reply to new comments on tweets."""
    global last_processed_time, processed_comment_ids
    try:
        print(f"Fetching tweets for {username}...")
        user_id = get_user_id(username)

        # Fetch recent tweets
        tweets = client.get_users_tweets(id=user_id, max_results=5)  # Only process 5 most recent tweets
        if not tweets.data:
            print("No tweets found.")
            return

        for tweet in tweets.data:
            tweet_id = tweet.id
            print(f"Checking comments for tweet ID: {tweet_id}")

            # Fetch recent replies to the tweet
            query = f"conversation_id:{tweet_id}"
            comments = client.search_recent_tweets(query=query, max_results=10)

            if not comments.data:
                print(f"No comments found for tweet ID: {tweet_id}")
                continue

            for comment in comments.data:
                if comment.id in processed_comment_ids:
                    continue  # Skip already processed comments

                # Skip comments older than the last processed time
                comment_time = comment.created_at
                if comment_time <= last_processed_time:
                    continue

                # Process the new comment
                text = comment.text
                author_id = comment.author_id
                print(f"Found new comment from user ID {author_id}: {text}")

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

        # Update last processed time
        last_processed_time = datetime.utcnow()

    except tweepy.errors.TooManyRequests:
        print("Rate limit reached. Sleeping for 15 minutes...")
        time.sleep(900)  # Wait for 15 minutes
    except Exception as e:
        print(f"Unexpected error: {e}")

def start_bot():
    """Start the bot and run continuously."""
    username = "mikasa_model"  # Target account username
    while True:
        reply_to_new_comments(username)
        time.sleep(300)  # Wait 5 minutes before polling again

if __name__ == "__main__":
    start_bot()
