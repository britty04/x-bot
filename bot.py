import os
import tweepy
import openai
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check for missing environment variables
if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN, OPENAI_API_KEY]):
    raise ValueError("One or more environment variables are missing. Please check your .env file or Railway environment settings.")

# Initialize Twitter client
print("Initializing Twitter client...")
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Persistent storage for processed IDs
PROCESSED_IDS_FILE = "processed_ids.txt"

def load_processed_ids():
    """Load processed comment IDs from file."""
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

        # Fetch recent tweets (at least 5 required by Twitter API)
        tweets = client.get_users_tweets(id=user_id, max_results=5)
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
            save_processed_id(comment.id)

    except tweepy.errors.TooManyRequests:
        print("Rate limit reached. Sleeping for 15 minutes...")
        time.sleep(900)  # Wait for 15 minutes
    except Exception as e:
        print(f"Unexpected error: {e}")

def start_bot():
    """Run the bot continuously with extended intervals."""
    username = "mikasa_model"  # Replace with your bot's username
    while True:
        try:
            reply_to_comments(username)
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
        print("Sleeping for 60 minutes...")
        time.sleep(3600)  # Wait 60 minutes before polling again

if __name__ == "__main__":
    print("Starting bot...")
    start_bot()
