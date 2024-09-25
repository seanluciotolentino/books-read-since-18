import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import requests
from datetime import datetime

# Load CSV data
def load_data():
    books_df = pd.read_csv("books.csv")
    books_df.genre.fillna('other', inplace=True)
    books_df['Year Read'] = books_df['date read']  # Date Read is just the year
    return books_df

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

def classify_fiction_nonfiction(df):
    return df['genre'].apply(lambda g: 'Non-Fiction' if g.lower() in ['nonfiction', 'memoir'] else 'Fiction')


# Load the books data
st.set_page_config(layout="wide")
books_df = load_data()

print(books_df.genre.unique())

# App layout
st.title("Books I've Read Dashboard")

# =========================
# ===== ADD A BOOK ========
# =========================
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

# =========================
# ===== BIG NUMBERS ========
# =========================
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

# =========================
# ===== LINE CHART ========
# =========================

st.subheader("Genres Over Time")
books_df['Year Read'] = books_df['date read']  # Date Read is just the year
genres_over_time = books_df.groupby(['Year Read', 'genre']).size().unstack(fill_value=0)

# Plotly Time Series Plot
time_series_fig = px.line(genres_over_time, 
                          x=genres_over_time.index, 
                          y=genres_over_time.columns, 
                          labels={'value': 'Books', 'Year Read': 'Year'})
st.plotly_chart(time_series_fig)



# ===================================
# ===== GENRE PIE CHARTS ============
# ===================================
genre_all_time = books_df.groupby('genre').size().reset_index(name="Count")


# List of unique years
years = books_df['Year Read'].unique()
years.sort()

# First column: Pie chart for all-time genres
all_time_labels = genre_all_time['genre']
all_time_values = genre_all_time['Count']

fig_all_time = go.Figure(data=[go.Pie(labels=all_time_labels, values=all_time_values, 
                    hoverinfo='label+percent', textinfo='text', 
                    title='Genre of all Books')])

# Second column: Grid of pie charts (5 columns x 3 rows) for genres by year

fig_grid = sp.make_subplots(rows=3, cols=5, subplot_titles=[str(year) for year in years],
                            specs=[[{'type': 'domain'}]*5]*3)

# Add pie charts for each year
row, col = 1, 1
for year in years:
    # Get genre counts for the specific year
    genre_this_year = books_df[books_df['Year Read'] == year].groupby('genre').size().reset_index(name="Count")
    
    # Apply percentage threshold for textinfo
    labels = genre_this_year['genre']
    values = genre_this_year['Count']
    
    # Add the pie chart for the year to the grid
    fig_grid.add_trace(
        go.Pie(labels=labels, values=values, hoverinfo='label+percent', textinfo='text'),
        row=row, col=col
    )
    
    # Update column and row positions for the grid layout
    col += 1
    if col > 5:
        col = 1
        row += 1

# Update layout for the grid of pie charts
fig_grid.update_layout(showlegend=False)

# Display the new row with two columns
with st.expander("Genre Pie Charts"):
    col1, col2 = st.columns([2, 4])
    # First column: all-time pie chart
    col1.subheader('All Time')
    col1.plotly_chart(fig_all_time)

    # Second column: grid of pie charts by year
    col2.subheader('By Year')
    col2.plotly_chart(fig_grid)

# ===================================
# ===== FICTION PIE CHARTS ==========
# ===================================

# Apply classification to the entire dataframe
books_df['Category'] = classify_fiction_nonfiction(books_df)

# Prepare data for the pie charts
fiction_vs_nonfiction_all_time = books_df.groupby('Category').size().reset_index(name="Count")

# List of unique years
years = books_df['Year Read'].unique()
years.sort()

# First column: Pie chart for all-time fiction vs non-fiction
labels_all_time = fiction_vs_nonfiction_all_time['Category']
values_all_time = fiction_vs_nonfiction_all_time['Count']

fig_all_time = go.Figure(data=[go.Pie(labels=labels_all_time, values=values_all_time, text=labels_all_time, hoverinfo='label+percent', textinfo='text')])

# Second column: Grid of pie charts (5 columns x 3 rows) for fiction vs non-fiction by year
fig_grid = sp.make_subplots(rows=3, cols=5, subplot_titles=[str(year) for year in years],
                            specs=[[{'type': 'domain'}]*5]*3)

# Add pie charts for each year
row, col = 1, 1
for year in years:
    # Get fiction vs non-fiction counts for the specific year
    fiction_vs_nonfiction_this_year = books_df[books_df['Year Read'] == year].groupby('Category').size().reset_index(name="Count")
    
    # Apply percentage threshold for textinfo
    labels = fiction_vs_nonfiction_this_year['Category']
    values = fiction_vs_nonfiction_this_year['Count']
    
    # Add the pie chart for the year to the grid
    fig_grid.add_trace(
        go.Pie(labels=labels, values=values, hoverinfo='label+percent', textinfo='text'),
        row=row, col=col
    )
    
    # Update column and row positions for the grid layout
    col += 1
    if col > 5:
        col = 1
        row += 1

# Update layout for the grid of pie charts
fig_grid.update_layout(showlegend=False)


# Display the new row with two columns
with st.expander("Fiction vs Non-Fiction"):
    col1, col2 = st.columns([2, 4])
    # First column: all-time pie chart
    col1.subheader('All Time')
    col1.plotly_chart(fig_all_time)

    # Second column: grid of pie charts by year
    col2.subheader('By Year')
    col2.plotly_chart(fig_grid)

# ===================================
# ===== STARRED BOOKS ==========
# ===================================
columns = ['title', 'author', 'Year Read']
with st.expander("Starred Books"):
    col1, col2, col3 = st.columns([1, 1, 1])
    col1.subheader('Zero Star Books')
    col1.dataframe(books_df.loc[books_df['stars'] <= 0, columns])
    col2.subheader('One Star Books')
    col2.dataframe(books_df.loc[books_df['stars'] == 1, columns])
    col3.subheader('Two Star Books')
    col3.dataframe(books_df.loc[books_df['stars'] >= 2, columns])
