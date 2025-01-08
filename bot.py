import os
import tweepy
import openai
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
        user = client.get_user(username=username)
        user_id = user.data.id

        # Fetch the most recent tweet
        tweets = client.get_users_tweets(id=user_id, max_results=1)
        if not tweets.data:
            print("No tweets found.")
            return

        tweet = tweets.data[0]
        tweet_id = tweet.id
        print(f"Processing comments for tweet ID: {tweet_id}")

        # Fetch recent replies to the tweet
        query = f"conversation_id:{tweet_id}"
        comments = client.search_recent_tweets(query=query, max_results=1)  # Only 1 comment

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
        print("Rate limit reached. Manual execution required later.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    username = "mikasa_model"  # Replace with your bot's username
    reply_to_comments(username)
