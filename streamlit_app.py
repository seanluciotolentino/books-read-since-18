import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Load CSV data
#@st.cache
def load_data():
    return pd.read_csv("books.csv")

# Function to add a new book
def add_book(title, author, genre, stars):
    new_book = {
        "Title": title,
        "Author": author,
        "Genre": genre,
        "Pages": pages,
        "Date Read": datetime.today().year  # Automatically get today's year
    }
    return new_book

# Load the books data
st.set_page_config(layout="wide")
books_df = load_data()
print(books_df.columns)

# App layout
st.title("Books I've Read Since 18 Dashboard")

# Expander to add a new book
with st.expander("Add a Book"):
    title = st.text_input("Book Title")
    author = st.text_input("Author")
    genre = st.text_input("Genre")
    stars = st.number_input("Stars?", min_value=1)
    
    if st.button("Add Book"):
        new_book = add_book(title, author, genre, stars)
        books_df = books_df.append(new_book, ignore_index=True)
        books_df.to_csv("books.csv", index=False)
        st.success("Book added!")

# Big Number Display Row
total_books = len(books_df)
books_this_year = len(books_df[books_df['Date Read'] == datetime.now().year])
total_pages = int(books_df['Pages'].sum())
average_books_per_year = books_df[books_df['Date Read'] > 2011].groupby('Date Read').size().mean()
most_recent_book = books_df.sort_values('Date Read', ascending=False).iloc[0]['Title']

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
    books_df['Year Read'] = books_df['Date Read']  # Date Read is just the year
    genres_over_time = books_df.groupby(['Year Read', 'Genre']).size().unstack(fill_value=0)

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
    genres_this_year = books_df[books_df['Year Read'] == datetime.now().year].groupby('Genre').size()
    pie_chart_this_year = go.Figure(data=[go.Pie(labels=genres_this_year.index, values=genres_this_year.values)])
    st.plotly_chart(pie_chart_this_year)

