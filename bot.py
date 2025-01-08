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
auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

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
    tweets = api.user_timeline(count=10, tweet_mode="extended")  # Get last 10 tweets
    for tweet in tweets:
        tweet_id = tweet.id
        print(f"Checking comments for tweet ID: {tweet_id}")

        # Get replies to the tweet
        comments = api.search_tweets(q=f'to:{tweet.user.screen_name}', since_id=tweet_id, tweet_mode="extended")
        for comment in comments:
            if comment.in_reply_to_status_id == tweet_id:  # Ensure it's a reply
                user = comment.user.screen_name
                text = comment.full_text
                print(f"Found comment from @{user}: {text}")

                # Generate a reply
                reply_text = generate_reply(text)
                print(f"Generated reply: {reply_text}")

                # Post the reply
                try:
                    api.update_status(
                        status=f"@{user} {reply_text}",
                        in_reply_to_status_id=comment.id
                    )
                    print(f"Replied to @{user}")
                except tweepy.TweepError as e:
                    print(f"Error replying to @{user}: {e}")
    print("Finished checking comments.")

# Main loop
if __name__ == "__main__":
    while True:
        reply_to_comments()
        time.sleep(60)  # Wait 1 minute before checking again
