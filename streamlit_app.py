import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import requests
from datetime import datetime
from google.oauth2 import service_account
import gspread
import json

import math
def load_data():
    data = sheet.get_all_values()
    books_df = pd.DataFrame(data[1:], columns=data[0]) 
    books_df.genre.fillna('other', inplace=True) 
    books_df['date read'] = pd.to_datetime(books_df['date read'])
    books_df['stars'] = pd.to_numeric(books_df.stars)
    books_df['pages'] = pd.to_numeric(books_df.pages)
    books_df['Year Read'] = books_df['date read'].dt.year 
    
    # Filter for books read since 2012
    books_df = books_df[books_df['Year Read'] >= 2012]

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
    try:
        pages = int(book_info.get('number_of_pages_median', 0))
    except (ValueError, TypeError):
        pages = 0
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

# setup connection to google sheets
secrets = json.loads(st.secrets['google_cloud']["credentials"].replace('\n', ''))
secrets['private_key'] = st.secrets['private_key']
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_info(secrets, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open('emmas books').sheet1 
books_df = load_data()

# --- ICONS (Noun Project Style) ---
ICONS = {
    "book": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="24" height="24" fill="currentColor"><path d="M80,10H30c-5.5,0-10,4.5-10,10v60c0,5.5,4.5,10,10,10h50V10z M30,85c-2.8,0-5-2.2-5-5s2.2-5,5-5h45v10H30z M75,70H30 c-2.8,0-5-2.2-5-5V20c0-2.8,2.2-5,5-5h45V70z"/></svg>',
    "pages": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="24" height="24" fill="currentColor"><path d="M75,10H25C19.5,10,15,14.5,15,20v60c0,5.5,4.5,10,10,10h50c5.5,0,10-4.5,10-10V20C85,14.5,80.5,10,75,10z M25,85 c-2.8,0-5-2.2-5-5V20c0-2.8,2.2-5,5-5h50c2.8,0,5,2.2,5,5v60c0,2.8-2.2,5-5,5H25z M30,30h40v5H30V30z M30,45h40v5H30V45z M30,60h40v5 H30V60z"/></svg>',
    "calendar": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="24" height="24" fill="currentColor"><path d="M80,15h-5v-5h-5v5H30v-5h-5v5h-5c-5.5,0-10,4.5-10,10v55c0,5.5,4.5,10,10,10h60c5.5,0,10-4.5,10-10V25 C90,19.5,85.5,15,80,15z M20,85V40h60v45H20z M80,30H20V25c0-2.8,2.2-5,5-5h5v5h5v-5h40v5h5v-5h5c2.8,0,5,2.2,5,5V30z"/></svg>',
    "trending": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="24" height="24" fill="currentColor"><path d="M90,75l-35-35l-15,15L10,25V15h10v5.9l25,25l15-15l35,35V75z M90,55l-5-5l5-5V55z"/></svg>',
    "stars": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="24" height="24" fill="currentColor"><path d="M50,10l12,25l28,4l-20,20l5,28l-25-13l-25,13l5-28l-20-20l28-4L50,10z"/></svg>'
}

def metric_with_icon(label, value, icon_key, font_size=1.8):
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
        <span style="color: #FF4B4B;">{ICONS.get(icon_key, '')}</span>
        <span style="font-size: 0.9rem; font-weight: 600; color: #9B9C9E;">{label}</span>
    </div>
    <div style="font-size: {font_size}rem; font-weight: 700;">{value}</div>
    """, unsafe_allow_html=True)

# set up the data
st.set_page_config(layout="wide", page_title="Books Dashboard", page_icon="📚")

def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #262730; /* Dark card background */
            border: 1px solid #3d3d3d;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        /* Custom header style */
        .custom-header {
            font-weight: 700;
            font-size: 2.5rem;
            background: -webkit-linear-gradient(45deg, #FF4B4B, #FF9100);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()



# =========================
# ===== SIDEBAR: ADD BOOK =
# =========================
with st.sidebar:
    st.markdown(f'<div style="display:flex; align-items:center; gap:10px;">{ICONS["book"]} <h2 style="margin:0;">Add a New Book</h2></div>', unsafe_allow_html=True)
    with st.form("add_book_form", clear_on_submit=True):
        st.markdown("[View GSheet Source](https://docs.google.com/spreadsheets/d/1A534GEJJ9oWsNyHGKcUZPVPoEwfqSxez1ICupdqLWRI/edit?usp=sharing)")
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        genre = st.selectbox("Genre", books_df.genre.unique())
        stars = st.radio("Rating", options=[0, 1, 2], format_func=lambda x: ["0 (Unrated)", "1 (Good)", "2 (Loved)"][x], horizontal=True)
        
        submitted = st.form_submit_button("Add Book", use_container_width=True)


        if submitted:
            if title and author:
                new_book = add_book(title, author, genre, stars)
                # Google Sheets update
                current_data = sheet.get_all_values()
                df = pd.DataFrame(current_data[1:], columns=current_data[0])
                df = pd.concat([df, pd.DataFrame([new_book])], ignore_index=True)
                sheet.clear()
                sheet.update([df.columns.tolist()] + df.values.tolist())
                st.success("✨ Book added successfully!")
                st.balloons()
            else:
                st.error("Please enter both Title and Author.")

st.title("Books Read Since 18")

# =========================
# ===== BIG NUMBERS ========
# =========================
total_books = len(books_df)
books_this_year = len(books_df[books_df['Year Read'] == datetime.now().year])
total_pages = int(books_df['pages'].sum())
pages_this_year = int(books_df[books_df['Year Read'] == datetime.now().year]['pages'].sum())
average_books_per_year = books_df[books_df['date read'].dt.year > 2011].groupby('date read').size().mean()
average_pages_per_year = books_df[books_df['date read'].dt.year > 2011]['pages'].mean()
most_recent_book = books_df.sort_values('date read', ascending=False).iloc[0]['title']

# Most Recent Book - Full Width
with st.container():
    metric_with_icon("Most Recent Book", most_recent_book, "book", font_size=2.5)

st.write("") # Spacer

# Metrics Grid
col1, col2 = st.columns(2)

with col1:
    with st.container():
        metric_with_icon("Total Books", total_books, "book")
    with st.container():
        metric_with_icon("Avg Books/Year", f"{average_books_per_year:.1f}", "trending")
    with st.container():
        metric_with_icon("Books This Year", books_this_year, "calendar")

with col2:
    with st.container():
        metric_with_icon("Total Pages", f"{total_pages:,}", "pages")
    with st.container():
        metric_with_icon("Avg Pages/Year", f"{average_pages_per_year:.0f}", "trending")
    with st.container():
        metric_with_icon("Pages This Year", f"{pages_this_year:,}", "calendar")



st.markdown("---")


# =========================
# ===== LINE CHART ========
# =========================

# =========================
# ===== CHARTS ============
# =========================

st.subheader("Books Read by Genre per Year")

# Prepare data for Stacked Bar Chart
df_chart = books_df.groupby(['Year Read', 'genre']).size().reset_index(name='Count')
df_chart = df_chart.sort_values('Year Read')
# Ensure x-axis is treated as strings for stable categorical plotting
df_chart['Year'] = df_chart['Year Read'].astype(str)

# Calculate yearly totals for the labels
yearly_totals = df_chart.groupby('Year Read')['Count'].sum().reset_index(name='Total')
yearly_totals = yearly_totals.sort_values('Year Read')
yearly_totals['Year'] = yearly_totals['Year Read'].astype(str)

# Create the stacked bar chart
fig_bar = px.bar(df_chart, 
                 x="Year", 
                 y="Count", 
                 color="genre", 
                 category_orders={"Year": df_chart['Year'].unique().tolist()},
                 color_discrete_sequence=px.colors.qualitative.Prism)

# Add totals as text labels using a separate scatter trace
fig_bar.add_trace(go.Scatter(
    x=yearly_totals['Year'],
    y=yearly_totals['Total'],
    mode='text',
    text=yearly_totals['Total'].astype(str),
    textposition='top center',
    showlegend=False,
    cliponaxis=False,
    textfont=dict(color='#FF4B4B', size=14, family='Outfit') # Matching theme color
))

fig_bar.update_layout(
    barmode='stack', 
    template="plotly_dark",
    xaxis_title="Year",
    yaxis_title="Books Read",
    legend_title="Genre",
    yaxis=dict(range=[0, yearly_totals['Total'].max() * 1.2]) # More headroom for labels
)
st.plotly_chart(fig_bar, use_container_width=True)





col_charts_1, col_charts_2 = st.columns(2)


# DONUT: Genres All Time
with col_charts_1:
    st.subheader("Genres (All Time)")
    genre_counts = books_df['genre'].value_counts().reset_index()
    genre_counts.columns = ['genre', 'count']
    
    fig_donut = px.pie(genre_counts, values='count', names='genre', hole=0.5,
                       color_discrete_sequence=px.colors.qualitative.Prism)
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    fig_donut.update_layout(showlegend=False, template="plotly_dark")
    st.plotly_chart(fig_donut, use_container_width=True)

# DONUT: Fiction vs Non-Fiction
with col_charts_2:
    st.subheader("Fiction vs Non-Fiction")
    books_df['Category'] = classify_fiction_nonfiction(books_df)
    cat_counts = books_df['Category'].value_counts().reset_index()
    cat_counts.columns = ['Category', 'count']
    
    fig_cat = px.pie(cat_counts, values='count', names='Category', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)  
    fig_cat.update_traces(textposition='inside', textinfo='percent+label')
    fig_cat.update_layout(showlegend=False, template="plotly_dark")
    st.plotly_chart(fig_cat, use_container_width=True)



# ===================================
# ===== STARRED BOOKS ==========
# ===================================
# =========================
# ===== STARRED BOOKS =
# =========================
st.subheader("Book Ratings & Search")

# Search and Filter
search_query = st.text_input("Search by Title, Author, or Genre", placeholder="Type to filter...")

# Helper to render stars (0-2 scale)
def get_star_string(rating):
    if rating >= 2: return "⭐⭐ (Loved)"
    if rating == 1: return "⭐ (Liked)"
    return "0 (Unrated)"

# Filter books based on search
if search_query:
    filtered_df = books_df[
        books_df['title'].str.contains(search_query, case=False, na=False) |
        books_df['author'].str.contains(search_query, case=False, na=False) |
        books_df['genre'].str.contains(search_query, case=False, na=False)
    ].copy()
else:
    filtered_df = books_df.copy()

# Sort by Year Read Descending
filtered_df = filtered_df.sort_values('Year Read', ascending=False)

filtered_df['Star Rating'] = filtered_df['stars'].apply(get_star_string)
display_cols = ['title', 'author', 'genre', 'Star Rating', 'Year Read']

tab1, tab2, tab3, tab4 = st.tabs(["All Books", "⭐⭐ Loved", "⭐ Liked", "Unrated/Neutral"])

# Column configuration to remove commas from years
column_config = {
    "Year Read": st.column_config.NumberColumn("Year Read", format="%d")
}

with tab1:
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True, column_config=column_config)

with tab2:
    st.dataframe(filtered_df[filtered_df['stars'] == 2][display_cols], use_container_width=True, hide_index=True, column_config=column_config)

with tab3:
    st.dataframe(filtered_df[filtered_df['stars'] == 1][display_cols], use_container_width=True, hide_index=True, column_config=column_config)

with tab4:
    st.dataframe(filtered_df[filtered_df['stars'] == 0][display_cols], use_container_width=True, hide_index=True, column_config=column_config)



