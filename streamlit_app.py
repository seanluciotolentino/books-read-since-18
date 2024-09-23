import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# Load CSV data
#@st.cache
def load_data():
    return pd.read_csv("books.csv")

# Function to add a new book
def add_book(title, author, genre, stars):
    # query the open library
    query = f"https://openlibrary.org/search.json?title={title}&author={author}"
    response = requests.get(query)
    
    if response.status_code == 200 and response.json()['numFound'] > 0:
        book_info = response.json()['docs'][0]
    else:
        book_info = {}
    pages = book_info.get('number_of_pages_median', 'N/A')
    published_date = book_info.get('first_publish_year', 'N/A')

    new_book = {
        "title": title,
        "author": author,
        "genre": genre,
        "pages": pages,
        "stars": stars,
        "published_date": published_date,
        "date read": datetime.today().year
    }
    return new_book

# Load the books data
st.set_page_config(layout="wide")
books_df = load_data()
books_df.genre.fillna('other', inplace=True)
print(books_df.genre.unique())

# App layout
st.title("Books I've Read Dashboard")

# Expander to add a new book
with st.expander("Add a Book"):
    title = st.text_input("Book Title")
    author = st.text_input("Author")
    genre = st.selectbox("Genre", books_df.genre.unique())
    stars = st.number_input("Stars?", min_value=0)
    
    if st.button("Add Book"):
        new_book = add_book(title, author, genre, stars)
        books_df = pd.concat([books_df, pd.DataFrame([new_book])], ignore_index=True)
        books_df.to_csv("books.csv", index=False)
        st.success("Book added!")

# Big Number Display Row
total_books = len(books_df)
books_this_year = len(books_df[books_df['date read'] == datetime.now().year])
total_pages = int(books_df['pages'].sum())
average_books_per_year = books_df[books_df['date read'] > 2011].groupby('date read').size().mean()
most_recent_book = books_df.sort_values('date read', ascending=False).iloc[0]['title']

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Books Read", total_books)
col2.metric("Books Read This Year", books_this_year)
col3.metric("Avg Books Per Year", f"{average_books_per_year:.2f}")
col4.metric("Total Pages Read", f"{total_pages:,}")
col5.metric("Most Recent Book", most_recent_book)



# Time Series of Genres Over Time (aggregated by year)
col1, col2 = st.columns([2, 1])

with col1: 
    st.subheader("Genres Over Time")
    books_df['Year Read'] = books_df['date read']  # Date Read is just the year
    genres_over_time = books_df.groupby(['Year Read', 'genre']).size().unstack(fill_value=0)

    # Plotly Time Series Plot
    time_series_fig = px.line(genres_over_time, 
                              x=genres_over_time.index, 
                              y=genres_over_time.columns, 
                              labels={'value': 'Books', 'Year Read': 'Year'})
    st.plotly_chart(time_series_fig)

with col2:
    # Genre Breakdown Pie Charts
    st.subheader("Genres Read This Year")

    # Genre Breakdown for this year
    genres_this_year = books_df[books_df['Year Read'] == datetime.now().year].groupby('genre').size()
    pie_chart_this_year = go.Figure(data=[go.Pie(labels=genres_this_year.index, values=genres_this_year.values)])
    st.plotly_chart(pie_chart_this_year)
