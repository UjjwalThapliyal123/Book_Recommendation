import streamlit as st
import pickle
import pandas as pd
import ast
import difflib

# ---------- Load Functions ----------
def pickle_file(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def df_file(filename):
    df = pd.read_csv(filename)
    # Convert 'Genres' from string to list
    if isinstance(df['Genres'].iloc[0], str):
        df['Genres'] = df['Genres'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])
    return df

# ---------- Load Data ----------
datas = df_file("ready_book.csv")
similarity_matrix = pickle_file("similarity_matrix")  # use .pkl extension

# ---------- Recommendation Logic ----------
def recommend_by_genre(genre_name, top_n=10, base_title=None):
    genre_books = datas[datas['Genres'].apply(lambda genres: genre_name in genres)]

    if genre_books.empty:
        return f"Not Found '{genre_name}'."

    if base_title:
        if base_title not in genre_books['Book_Name'].values:
            return f"Book '{base_title}' not found in the Given Genre '{genre_name}'."

        idx = genre_books[genre_books['Book_Name'] == base_title].index[0]
        sim_score = list(enumerate(similarity_matrix[idx]))

        # Filter similarity scores to only those in the selected genre
        validate_indices = genre_books.index.tolist()
        sim_score = [(i, score) for i, score in sim_score if i in validate_indices]
        sim_score = sorted(sim_score, key=lambda x: x[1], reverse=True)
        top_indicies = [i for i, _ in sim_score[1:top_n+1]]

        return datas.loc[top_indicies][['Book_Name', 'Author', 'Rating']]
    
    else:
        return genre_books.sort_values(by='Rating', ascending=False).head(top_n)[
            ['Book_Name', 'Author', 'Rating']
        ]
        
        
        
st.set_page_config(page_title=" Book  Recommender", layout="wide")
st.title("Book Recommendation System")
st.markdown("Find great books by genre and explore similar titles.")

# Sidebar Inputs
with st.sidebar:
    st.header("🔍 Choose Genre & Book")
    
    # All unique genres
    all_genres = sorted(set(g for sublist in datas['Genres'] for g in sublist))
    
    genre_query = st.text_input("Type a genre")
    matched_genres = difflib.get_close_matches(genre_query, all_genres, n=10, cutoff=0.3)
    
    if matched_genres:
        selected_genre = st.selectbox("Select a genre match", matched_genres)
    else:
        selected_genre = None
        if genre_query:
            st.warning("No matching genres found.")
    
    if selected_genre:
        filtered_books = datas[datas['Genres'].apply(lambda g: selected_genre in g)]
        book_titles = filtered_books['Book_Name'].tolist()
        selected_title = st.selectbox("Optional: Select a base book", [""] + book_titles)
    else:
        selected_title = ""
    
    top_n = st.slider("Number of Recommendations", 1, 20, 10)
    recommend_button = st.button("📖 Get Recommendations")

# Display Results
if recommend_button and selected_genre:
    with st.spinner("Finding your recommendations..."):
        if selected_title:
            result = recommend_by_genre(selected_genre, top_n, selected_title)
        else:
            result = recommend_by_genre(selected_genre, top_n)

    if isinstance(result, str):
        st.warning(result)
    else:
        st.subheader("📘 Recommended Books")
        for i, row in result.reset_index(drop=True).iterrows():
            with st.container():
                cols = st.columns([3, 2, 1])
                cols[0].markdown(f"**{row['Book_Name']}**")
                cols[1].markdown(f"👤 {row['Author']}")
                cols[2].markdown(f"⭐ {row['Rating']}")
                st.markdown("---")
                