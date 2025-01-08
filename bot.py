import os
import tweepy
import openai
import time
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

# Track the last processed comment ID
last_processed_comment_id = None

# Fetch the user ID of the account
def get_user_id(username):
    try:
        user = client.get_user(username=username)
        return user.data.id
    except Exception as e:
        print(f"Error fetching user ID for {username}: {e}")
        raise

# Generate a funny/sarcastic reply using OpenAI
def generate_reply(comment_text):
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

# Process and reply to comments
def reply_to_comments():
    global last_processed_comment_id
    try:
        print("Fetching tweets...")
        username = "mikasa_model"  # Target username
        user_id = get_user_id(username)

        # Fetch recent tweets
        tweets = client.get_users_tweets(id=user_id, max_results=10)
        if not tweets.data:
            print("No tweets found.")
            return

        for tweet in tweets.data:
            tweet_id = tweet.id
            print(f"Checking comments for tweet ID: {tweet_id}")

            # Search for comments (replies to the tweet)
            query = f"conversation_id:{tweet_id}"
            comments = client.search_recent_tweets(query=query, max_results=10)

            if not comments.data:
                print("No comments found for tweet ID:", tweet_id)
                continue

            for comment in comments.data:
                # Skip already processed comments
                if last_processed_comment_id and comment.id <= last_processed_comment_id:
                    continue

                text = comment.text
                author_id = comment.author_id
                print(f"Found comment from user ID {author_id}: {text}")

                # Generate and post the reply
                reply_text = generate_reply(text)
                print(f"Replying with: {reply_text}")

                client.create_tweet(
                    text=f"@{author_id} {reply_text}",
                    in_reply_to_tweet_id=comment.id
                )
                print(f"Replied to comment ID: {comment.id}")
                last_processed_comment_id = comment.id

    except tweepy.errors.TooManyRequests:
        print("Rate limit reached. Waiting...")
        time.sleep(900)  # Wait for 15 minutes
    except Exception as e:
        print(f"Unexpected error: {e}")

# Main loop
def start_bot():
    while True:
        reply_to_comments()
        time.sleep(60)  # Run every 1 minute

if __name__ == "__main__":
    start_bot()
