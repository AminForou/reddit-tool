import streamlit as st
import pandas as pd
from backend import fetch_latest_questions, most_frequent_queries,generate_word_cloud

def main():
    st.title("Reddit Latest Questions and Top Answers Fetcher & Frequency Analysis")

    # Taking input from the user for Reddit API credentials
    client_id = st.text_input("Client ID", value='', type="password")
    secret_key = st.text_input("Secret Key", value='', type="password")

    # Taking subreddit name from the user
    subreddit_name = st.text_input("Subreddit Name", value='AskReddit')

    # Radio button to let the user decide between newest and hottest questions
    question_type = st.radio("Select Type of Questions", ('Newest', 'Hottest'))

    # Slider to let the user decide the number of questions to fetch
    num_questions = st.slider("Number of Questions", 1, 900, 10)
    # Slider to let the user decide the number of top upvoted answers to display
    num_answers = st.slider("Number of Top Upvoted Answers", 0, 5, 1)
    # Slider to let the user decide how many of the top queries they want to see
    num_top_queries = st.slider("Number of Top Queries", 1, 100, 5)
    # Button to fetch the selected type and number of latest questions and perform analysis
    if st.button("Fetch and Analyze"):
        with st.spinner('Loading data...'):
            try:
                latest_questions = fetch_latest_questions(client_id, secret_key, subreddit_name, num_questions, question_type, num_answers)
                # Create columns to put tables side by side
                col1, col2, col3 = st.columns(3)
                st.write("## Most Frequent Queries:")
                for n_words in [1, 2, 3]:
                    st.write(f"### {n_words}-Word Queries:")
                    frequent_queries = most_frequent_queries(latest_questions, n_words)
                    df = pd.DataFrame(frequent_queries, columns=['Query', 'Count'])
                    df.index += 1  # Adjust index
                    st.table(df.head(num_top_queries))

                # Combine all the text from titles, bodies, and answers for word cloud generation
                combined_text = " ".join(
                    [
                        q['title'] + " " + (q['body'] if q['body'] != "No body content" else "") +
                        " ".join([answer for answer in q['top_answers']])
                        for q in latest_questions
                    ]
                )
                generate_word_cloud(combined_text)


                # Expander for questions
                with st.expander(f"{num_questions} {question_type} Questions from r/{subreddit_name}"):
                    for idx, question in enumerate(latest_questions, 1):
                        st.write(f"### {idx}. {question['title']}")
                        st.write(question['body'])
                        if num_answers > 0:
                            st.write(f"#### Top Upvoted Answers:")
                            for ans_idx, answer in enumerate(question['top_answers'], 1):
                                st.write(f"{ans_idx}- {answer}")
                        st.write("---")  # A horizontal line for better separation
                        # Adjusting the table index to start from 1

            except Exception as e:
                st.write(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
