import os
import tweepy
import openai
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Twitter API credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Authenticate with Twitter
client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Get your Twitter user ID
def get_user_id(username):
    user = client.get_user(username=username)
    return user.data.id

# Generate funny/sarcastic replies using OpenAI
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

# Fetch and reply to comments
def reply_to_comments():
    print("Fetching your tweets...")

    # Get your user ID
    username = "your_twitter_username"  # Replace with your username
    user_id = get_user_id(username)

    # Fetch your tweets
    tweets = client.get_users_tweets(id=user_id, max_results=10)  # Get last 10 tweets
    if not tweets.data:
        print("No tweets found.")
        return

    for tweet in tweets.data:
        tweet_id = tweet.id
        print(f"Checking comments for tweet ID: {tweet_id}")

        # Search for comments (replies to the tweet)
        query = f"to:{username}"
        comments = client.search_recent_tweets(query=query, since_id=tweet_id, max_results=10)
        if not comments.data:
            print("No comments found.")
            continue

        for comment in comments.data:
            if "referenced_tweets" in comment.data and comment.data["referenced_tweets"][0]["id"] == tweet_id:  # Ensure it's a reply
                user = comment.author_id
                text = comment.text
                print(f"Found comment from user ID {user}: {text}")

                # Generate a reply
                reply_text = generate_reply(text)
                print(f"Generated reply: {reply_text}")

                # Post the reply
                try:
                    client.create_tweet(text=f"@{user} {reply_text}", in_reply_to_tweet_id=comment.id)
                    print(f"Replied to user ID {user}")
                except tweepy.TweepyException as e:
                    print(f"Error replying to user ID {user}: {e}")
    print("Finished checking comments.")

# Main loop
if __name__ == "__main__":
    while True:
        reply_to_comments()
        time.sleep(60)  # Wait 1 minute before checking again
