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
    wait_on_rate_limit=True  # Automatically handle rate limits
)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set to store processed comment IDs
processed_comment_ids = set()

# Get the user ID for the bot account
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

# Process replies to a specific tweet
def process_replies(tweet_id):
    try:
        print(f"Fetching replies for tweet ID: {tweet_id}")

        # Fetch replies using conversation_id
        query = f"conversation_id:{tweet_id}"
        comments = client.search_recent_tweets(query=query, max_results=100)

        if not comments.data:
            print(f"No comments found for tweet ID: {tweet_id}")
            return

        for comment in comments.data:
            if comment.id in processed_comment_ids:
                continue  # Skip already processed comments

            text = comment.text
            author_id = comment.author_id
            print(f"Found comment from user ID {author_id}: {text}")

            # Generate a reply and post it
            reply_text = generate_reply(text)
            print(f"Replying with: {reply_text}")

            client.create_tweet(
                text=f"@{author_id} {reply_text}",
                in_reply_to_tweet_id=comment.id
            )
            print(f"Replied to comment ID: {comment.id}")

            # Add comment ID to processed set
            processed_comment_ids.add(comment.id)

    except Exception as e:
        print(f"Error processing replies for tweet ID {tweet_id}: {e}")

# Fetch tweets and process their comments
def reply_to_comments(username):
    try:
        print(f"Fetching tweets for {username}...")
        user_id = get_user_id(username)

        # Fetch recent tweets
        tweets = client.get_users_tweets(id=user_id, max_results=10)
        if not tweets.data:
            print("No tweets found.")
            return

        for tweet in tweets.data:
            process_replies(tweet.id)

    except tweepy.errors.TooManyRequests:
        print("Rate limit reached. Waiting...")
        time.sleep(300)  # Wait 15 minutes
    except Exception as e:
        print(f"Unexpected error: {e}")

# Main loop to run the bot
def start_bot():
    username = "mikasa_model"  # Target account username
    while True:
        reply_to_comments(username)
        time.sleep(150)  # Wait 5 minutes before polling again

if __name__ == "__main__":
    start_bot()
