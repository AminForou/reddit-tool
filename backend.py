import praw
from collections import Counter
import nltk
from nltk.corpus import stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st

# Download the stopwords set
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def connect_to_reddit(client_id, secret_key):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=secret_key,
        user_agent="streamlit_app"
    )
    return reddit

# ... [other parts of the code remain unchanged]

def fetch_latest_questions(client_id, secret_key, subreddit_name, num_questions, question_type, num_answers):
    reddit = connect_to_reddit(client_id, secret_key)
    questions = []
    if question_type == "Newest":
        fetch_method = reddit.subreddit(subreddit_name).new
    else:  # Hottest
        fetch_method = reddit.subreddit(subreddit_name).hot
    for submission in fetch_method(limit=num_questions):
        # Fetch the specified number of top upvoted answers
        submission.comment_sort = 'best'
        top_comments = []
        for comment in submission.comments:
            if len(top_comments) >= num_answers:
                break
            if not isinstance(comment, praw.models.MoreComments):
                top_comments.append(comment.body)

        questions.append({
            'title': submission.title,
            'body': submission.selftext if submission.selftext else "No body content",
            'top_answers': top_comments
        })
    return questions




from collections import Counter

# Assuming stop_words has already been defined or imported. If not, you'll need to define it.

def most_frequent_queries(questions, n_words):
    """
    Analyze the most frequent queries in the questions and their top answers.

    Args:
    - questions (list): List of dictionaries with question details.
    - n_words (int): Number of words in the queries (1, 2, or 3).

    Returns:
    - list: Most frequent queries.
    """

    # First, we identify and remove globally repeated answers
    all_answers = [answer for q in questions for answer in q['top_answers']]
    repeated_answers = [item for item, count in Counter(all_answers).items() if count > 1]

    # Combining the question titles, bodies (excluding "No body content"), and filtered top answers
    combined_text = " ".join(
        [
            q['title'] + " " + (q['body'] if q['body'] != "No body content" else "") +
            " ".join([answer for answer in q['top_answers'] if answer not in repeated_answers])
            for q in questions
        ]
    )

    # Tokenize the text and filter out stop words
    tokens = [word for word in combined_text.split() if word.lower() not in stop_words]

    # Generate n-word queries
    queries = [" ".join(tokens[i:i+n_words]) for i in range(len(tokens) - n_words + 1)]

    # Using Counter to get most frequent queries
    counter = Counter(queries)
    return counter.most_common()


def generate_word_cloud(text):
    """Generate and display a word cloud from the provided text."""
    wordcloud = WordCloud(width=800, height=600, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot(plt)
