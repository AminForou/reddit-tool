import praw
from collections import Counter
import nltk
from nltk.corpus import stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# Ensure the stopwords set is downloaded
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

default_stop_words = set(stopwords.words('english'))

def connect_to_reddit(client_id, secret_key):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=secret_key,
        user_agent="streamlit_app"
    )
    return reddit

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

def most_frequent_queries(questions, n_words, custom_stopwords):
    """
    Analyze the most frequent queries in the questions and their top answers.

    Args:
    - questions (list): List of dictionaries with question details.
    - n_words (int): Number of words in the queries (1, 2, or 3).
    - custom_stopwords (str): Comma-separated string of custom stopwords.

    Returns:
    - list: Most frequent queries.
    """
    # Add custom stopwords to the default set
    custom_stopwords_set = set(custom_stopwords.split(','))
    all_stop_words = default_stop_words.union(custom_stopwords_set)

    # First, we identify and remove globally repeated answers
    all_answers = [answer for q in questions for answer in q['top_answers']]
    repeated_answers = [item for item, count in Counter(all_answers).items() if count > 1]

    # Collect unique queries from each question
    unique_queries = []

    for q in questions:
        combined_text = q['title'] + " " + (q['body'] if q['body'] != "No body content" else "") + " ".join(
            [answer for answer in q['top_answers'] if answer not in repeated_answers])

        # Tokenize the text and filter out stop words
        tokens = [word for word in combined_text.split() if word.lower() not in all_stop_words]

        # Generate n-word queries and collect unique queries
        queries = set([" ".join(tokens[i:i + n_words]) for i in range(len(tokens) - n_words + 1)])
        unique_queries.extend(queries)

    # Using Counter to get most frequent queries
    counter = Counter(unique_queries)
    return counter.most_common()

def generate_word_cloud(text):
    """Generate and display a word cloud from the provided text."""
    wordcloud = WordCloud(width=800, height=600, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)
    plt.close(fig)

def create_download_link(df_dict):
    """
    Create a download link for the dataframe dictionary with each dataframe as a sheet in an Excel file.

    Args:
    - df_dict (dict): Dictionary where keys are sheet names and values are dataframes.

    Returns:
    - bytes: Byte stream of the Excel file.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    processed_data = output.getvalue()
    return processed_data
