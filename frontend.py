import streamlit as st
import pandas as pd
from backend import fetch_latest_questions, most_frequent_queries, generate_word_cloud, create_download_link


def update_dfs(custom_stopwords, num_top_queries):
    """
    Update the dataframes stored in session state based on custom stopwords.
    """
    st.session_state.dfs = {}
    for n_words in [1, 2, 3]:
        frequent_queries = most_frequent_queries(st.session_state.results, n_words, custom_stopwords)
        df = pd.DataFrame(frequent_queries, columns=['Query', 'Count'])
        df.index += 1  # Adjust index
        st.session_state.dfs[f'{n_words}-Word Queries'] = df.head(100)  # Save top 100 queries for each type


def main():
    st.title("Reddit Latest Questions and Top Answers Fetcher & Frequency Analysis")

    # Taking input from the user for Reddit API credentials
    client_id = st.text_input("Client ID", value='', type="password",
                              help="Obtain from Reddit. For instructions, visit: https://moz.com/blog/build-reddit-keyword-research-tool")
    secret_key = st.text_input("Secret Key", value='', type="password",
                               help="Obtain from Reddit. For instructions, visit: https://moz.com/blog/build-reddit-keyword-research-tool")

    # Taking subreddit name from the user
    subreddit_name = st.text_input("Subreddit Name", value='AskReddit',
                                   help="Enter the name of the subreddit you want to analyze.")

    # Radio button to let the user decide between newest and hottest questions
    question_type = st.radio("Select Type of Questions", ('Newest', 'Hottest'),
                             help="Select 'Newest' for recent questions or 'Hottest' for trending ones.")

    # Slider to let the user decide the number of questions to fetch
    num_questions = st.slider("Number of Questions", 1, 900, 10,
                              help="Choose how many questions to analyze. More questions increase processing time.")
    # Slider to let the user decide the number of top upvoted answers to display
    num_answers = st.slider("Number of Top Upvoted Answers", 0, 5, 1,
                            help="Select the number of top upvoted answers to include for each question.")
    # Slider to let the user decide how many of the top queries they want to see
    num_top_queries = st.slider("Number of Top Queries", 1, 100, 5,
                                help="Set the number of rows to display in the result tables.")

    # Initialize session state for results
    if "results" not in st.session_state:
        st.session_state.results = None
    if "dfs" not in st.session_state:
        st.session_state.dfs = None
    if "custom_stopwords" not in st.session_state:
        st.session_state.custom_stopwords = ''

    # Input field for custom stopwords
    custom_stopwords = st.text_input("Custom Stopwords", value=st.session_state.custom_stopwords,
                                     help="Enter a list of comma-separated keywords to be added to the stopwords.")

    # Update the stopwords in session state
    st.session_state.custom_stopwords = custom_stopwords

    # Buttons for fetching and updating
    fetch_button, update_button = st.columns(2)
    with fetch_button:
        if st.button("Fetch and Analyze"):
            with st.spinner('Loading data...'):
                try:
                    latest_questions = fetch_latest_questions(client_id, secret_key, subreddit_name, num_questions,
                                                              question_type, num_answers)

                    st.session_state.results = latest_questions
                    update_dfs(st.session_state.custom_stopwords, num_top_queries)
                    st.success("Data fetched and analyzed successfully.")

                except Exception as e:
                    st.write(f"Error: {str(e)}")

    with update_button:
        if st.button("Update"):
            if st.session_state.results is not None:
                update_dfs(st.session_state.custom_stopwords, num_top_queries)
                st.success("Tables and word cloud updated successfully based on new stopwords.")
            else:
                st.warning("No data to update. Please fetch data first.")

    # Display the results if available
    if st.session_state.results is not None:
        st.write("## Most Frequent Queries:")

        for n_words in [1, 2, 3]:
            st.write(f"### {n_words}-Word Queries:")
            df = st.session_state.dfs.get(f'{n_words}-Word Queries', pd.DataFrame(columns=['Query', 'Count']))
            st.table(df.head(num_top_queries))

        # Combine all the text from titles, bodies, and answers for word cloud generation
        combined_text = " ".join(
            [
                q['title'] + " " + (q['body'] if q['body'] != "No body content" else "") +
                " ".join([answer for answer in q['top_answers']])
                for q in st.session_state.results
            ]
        )
        generate_word_cloud(combined_text)

        # Expander for questions
        with st.expander(f"{num_questions} {question_type} Questions from r/{subreddit_name}"):
            for idx, question in enumerate(st.session_state.results, 1):
                st.write(f"### {idx}. {question['title']}")
                st.write(question['body'])
                if num_answers > 0:
                    st.write(f"#### Top Upvoted Answers:")
                    for ans_idx, answer in enumerate(question['top_answers'], 1):
                        st.write(f"{ans_idx}- {answer}")
                st.write("---")  # A horizontal line for better separation

        # Create and provide download link for Excel file
        excel_data = create_download_link(st.session_state.dfs)
        st.download_button(label='Download Excel file', data=excel_data, file_name='reddit_queries_analysis.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == "__main__":
    main()
