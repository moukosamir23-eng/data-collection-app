import base64
from pathlib import Path

import streamlit as st
import pandas as pd
import sqlite3
from requests import get
from bs4 import BeautifulSoup as bs

st.set_page_config(page_title="My Best Data App", layout="wide")
HEADERS = {'User-Agent': 'Mozilla/5.0'}
BASE_DIR = Path(__file__).parent

# ---------- textes de l'interface (modifiables ici) ----------
OPT_SCRAPE = "Scrape data using beautifulSoup"
OPT_DOWNLOAD = "Download scraped data"
OPT_DASH = "Dashbord of the data"
OPT_EVAL = "Evaluate the App"

# ---------- style de l'app ----------
ACCENT = "#1e3a8a"        # boutons, listes déroulantes, en-tête (remplace le gris)
ACCENT_HOVER = "#14275e"  # survol
ACCENT_LIGHT = "#3d5fc4"  # option sélectionnée dans les listes
LIENS = "#ffd166"         # couleur des liens

def charger_style():
    bg = BASE_DIR / "assets" / "bg.jpg"
    fond = ""
    if bg.exists():
        b64 = base64.b64encode(bg.read_bytes()).decode()
        fond = f"background-image: url('data:image/jpeg;base64,{b64}'); background-size: cover; background-attachment: fixed;"
    st.markdown(f"""
    <style>
    /* fond de la page */
    [data-testid="stAppViewContainer"] {{ {fond} background-color: #46576b; }}
    [data-testid="stHeader"] {{ background: {ACCENT}; }}
    [data-testid="stHeader"] * {{ color: #ffffff !important; }}
    .block-container, [data-testid="stMainBlockContainer"] {{ max-width: 980px; padding-top: 4rem; }}

    /* textes de la zone principale */
    [data-testid="stMain"], [data-testid="stMain"] p, [data-testid="stMain"] li,
    [data-testid="stMain"] label, [data-testid="stMain"] span {{ color: #ffffff; }}
    [data-testid="stMain"] a {{ color: {LIENS} !important; font-weight: 600; }}
    [data-testid="stMain"] h1.app-title {{ text-align: center; color: #ffffff !important; -webkit-text-fill-color: #ffffff; font-weight: 800;
                    font-size: 2.6rem; margin-bottom: 1.2rem; padding: 0; }}
    [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{ color: #ffffff; }}

    /* sidebar bleue */
    [data-testid="stSidebar"] {{ background: #74b3ea; }}
    [data-testid="stSidebar"] h2.side-title {{ color: #ffffff !important; font-size: 1.15rem;
                    font-weight: 700; margin-bottom: 1rem; }}
    [data-testid="stSidebar"] label p {{ color: #ffffff !important; font-weight: 700; font-size: 0.8rem; }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] [data-baseweb="select"] > div > div {{ background: {ACCENT} !important; background-color: {ACCENT} !important; border: none !important; }}
    [data-testid="stSidebar"] [data-baseweb="select"] * {{ color: #ffffff !important; font-size: 0.85rem; }}
    [data-testid="stSidebar"] svg {{ fill: #ffffff; }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"], [data-testid="stSidebar"] [data-testid="stSelectbox"] input {{
        background: {ACCENT} !important; background-color: {ACCENT} !important; color: #ffffff !important;
        -webkit-text-fill-color: #ffffff; border: none !important; }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] input::placeholder {{ color: #ffffff; }}

    /* menus déroulants */
    [data-baseweb="popover"] ul {{ background: {ACCENT} !important; }}
    [data-baseweb="popover"] li {{ background: {ACCENT} !important; }}
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {{ background: {ACCENT_LIGHT} !important; }}
    [data-baseweb="popover"] li * {{ color: #ffffff !important; }}
    [data-testid="stSelectboxVirtualDropdown"] {{ background: {ACCENT} !important; }}
    [data-testid="stSelectboxVirtualDropdown"] [role="option"] {{ background: {ACCENT} !important; color: #ffffff !important; }}
    [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
    [data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] {{ background: {ACCENT_LIGHT} !important; }}
    [data-testid="stSelectboxVirtualDropdown"] [role="option"] * {{ color: #ffffff !important; }}

    /* boutons gris centrés */
    [data-testid="stMain"] [data-testid="stElementContainer"]:has(button), [data-testid="stMain"] [data-testid="stElementContainer"]:has(a[kind]) {{
        display: flex; justify-content: center; width: 100%; }}
    [data-testid="stMain"] .stButton > button, [data-testid="stMain"] .stDownloadButton > button,
    [data-testid="stMain"] .stLinkButton > a {{
        background: {ACCENT}; color: #ffffff; border: none; border-radius: 6px;
        min-width: 300px; font-weight: 600; }}
    [data-testid="stMain"] .stButton > button:hover, [data-testid="stMain"] .stDownloadButton > button:hover {{
        background: {ACCENT_HOVER}; color: #ffffff; }}
    [data-testid="stMain"] .stDownloadButton, [data-testid="stMain"] .stLinkButton {{ display: flex; justify-content: center; }}
    [data-testid="stMain"] .stLinkButton > a p, [data-testid="stMain"] .stButton > button p,
    [data-testid="stMain"] .stDownloadButton > button p {{ color: #ffffff !important; }}

    [data-testid="stMain"] [data-testid="stButton"] {{ width: 50%; min-width: 260px; }}
    [data-testid="stMain"] [data-testid="stButton"] > button {{ width: 100%; }}

    /* cartes de contenu lisibles sur le fond */
    [data-testid="stMetric"] {{ background: rgba(0,0,0,0.28); padding: 12px 16px; border-radius: 8px; }}
    [data-testid="stExpander"] {{ background: rgba(0,0,0,0.28); border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

charger_style()

# ---------- sidebar : User Input Features ----------
st.sidebar.markdown("<h2 class='side-title'>User Input Features</h2>", unsafe_allow_html=True)
pages = st.sidebar.selectbox("Pages indices", list(range(1, 101)), index=1)
menu = st.sidebar.selectbox("Options", [OPT_SCRAPE, OPT_DOWNLOAD, OPT_DASH, OPT_EVAL])

st.markdown("<h1 class='app-title'>MY BEST DATA APP</h1>", unsafe_allow_html=True)

# ---------- fonctions de scraping (BeautifulSoup) ----------
def scraper_gaaraas(nb_pages):
    data = []
    for p in range(1, nb_pages + 1):
        soup = bs(get(f'https://www.gaaraas.com/fr/users/dakar-auto?page={p}', headers=HEADERS, timeout=15).content, 'html.parser')
        for c in soup.find_all('div', 'ad-specification'):
            try:
                data.append({
                    'titre': c.find('h4').text.strip(),
                    'prix': c.find('span', 'price').text.strip(),
                    'km': c.find('div', 'ad-vehicle-mileage').find('div', 'value').text.strip(),
                    'boite': c.find('div', 'transmission').find('span').text.strip(),
                    'region': c.find('div', 'location').text.strip()
                })
            except:
                pass
    return pd.DataFrame(data)

def scraper_motos(nb_pages):
    data = []
    for p in range(1, nb_pages + 1):
        soup = bs(get(f'https://dakar-auto.com/senegal/motos-and-scooters-3?&page={p}', headers=HEADERS, timeout=15).content, 'html.parser')
        for c in soup.find_all('div', 'listing-card'):
            try:
                etat = c.find('small', 'badge').text.strip()
                km = None
                for li in c.find_all('li', 'listing-card__attribute'):
                    if 'km' in li.text:
                        km = li.text.strip()
                data.append({
                    'titre': c.find('h2', 'listing-card__header__title').a['title'],
                    'prix': c.find('h3', 'listing-card__header__price').text.strip(),
                    'km': km,
                    'region': c.find('span', 'province').text.strip(),
                    'type': c.find('h4', 'listing-card__header__category').text.replace(etat, '').strip(),
                    'etat': etat
                })
            except:
                pass
    return pd.DataFrame(data)

def scraper_books(nb_pages):
    data = []
    for p in range(1, nb_pages + 1):
        soup = bs(get(f'https://books.toscrape.com/catalogue/page-{p}.html', timeout=15).content, 'html.parser')
        containers = soup.find_all('article', 'product_pod')
        for c in containers:
            try:
                lien = 'https://books.toscrape.com/catalogue/' + c.h3.a['href']
                s = bs(get(lien, timeout=15).content, 'html.parser')
                tds = s.find('table', 'table-striped').find_all('td')
                desc = s.find('div', id='product_description')
                data.append({
                    'title': c.h3.a['title'],
                    'price': c.find('p', 'price_color').text,
                    'instock': c.find('p', 'instock availability').text.strip(),
                    'nb_produits': len(containers),
                    'rating': s.find('p', 'star-rating')['class'][1],
                    'nb_reviews': tds[6].text,
                    'description': desc.find_next_sibling('p').text if desc else None,
                    'category': s.find('ul', 'breadcrumb').find_all('li')[2].text.strip(),
                    'tax': tds[4].text
                })
            except:
                pass
    return pd.DataFrame(data)

def charger(table):
    conn = sqlite3.connect('data_collection.db')
    df = pd.read_sql(f'SELECT * FROM {table}', conn)
    conn.close()
    return df


# ---------- 1. Scraper ----------
if menu == OPT_SCRAPE:
    st.markdown("""
This app performs webscraping of data from dakar-auto over multiples pages. And we can also download scraped data from the app directly without scraping them.

- **Python libraries:** base64, pandas, streamlit, requests, bs4
- **Data source:** [Gaaraas](https://www.gaaraas.com/fr/users/dakar-auto) – [Dakar Auto](https://dakar-auto.com/senegal/motos-and-scooters-3)
""")
    st.write("")

    sources = {
        "Vehicles data": ("Gaaraas (voitures)", scraper_gaaraas, 100),
        "Motocycle data": ("Dakar-auto (motos)", scraper_motos, 55),
        "Books data": ("Books to Scrape", scraper_books, 5),
    }
    clic = None
    for bouton in sources:
        if st.button(bouton, key=bouton):
            clic = bouton

    if clic:
        nom, fonction, max_pages = sources[clic]
        nb_pages = min(pages, max_pages)
        if pages > max_pages:
            st.info(f"{nom} : limité à {max_pages} pages, scraping de {nb_pages} pages.")
        if clic == "Books data":
            st.caption("Chaque livre ouvre sa propre page, donc c'est plus lent.")
        with st.spinner("Scraping en cours..."):
            try:
                st.session_state["resultat"] = (nom, nb_pages, fonction(nb_pages))
            except Exception:
                st.session_state.pop("resultat", None)
                st.error("Le site ne répond pas. Vérifie ta connexion et réessaie.")
                st.stop()

    if "resultat" in st.session_state:
        nom, nb_pages, df = st.session_state["resultat"]
        st.success(f"{nom} : {len(df)} lignes récupérées sur {nb_pages} page(s)")
        st.dataframe(df)
        st.download_button("Télécharger en CSV", df.to_csv(index=False).encode('utf-8'), "scraping.csv", "text/csv")

# ---------- 2. Télécharger les données brutes (non nettoyées) ----------
elif menu == OPT_DOWNLOAD:
    st.header("Données brutes (non nettoyées)")
    fichiers = {
        "Books to Scrape": "data/books_web_scraper_brut.csv",
        "Gaaraas (voitures)": "data/gaaraas_web_scraper_brut.csv",
        "Dakar-auto (motos)": "data/motos_web_scraper_brut.csv",
        "Bulletins météo": "data/bulletins_brut.csv",
    }
    for nom, chemin in fichiers.items():
        df = pd.read_csv(chemin)
        st.subheader(nom)
        st.write(f"{df.shape[0]} lignes, {df.shape[1]} colonnes")
        st.dataframe(df.head(10))
        with open(chemin, 'rb') as f:
            st.download_button(f"Télécharger {nom}", f.read(), file_name=chemin.split('/')[-1], mime="text/csv")

# ---------- 3. Dashboard (données nettoyées, lues dans la base SQL) ----------
elif menu == OPT_DASH:
    st.header("Dashboard des données nettoyées")
    source = st.selectbox("Source", ["Books to Scrape", "Gaaraas (voitures)", "Dakar-auto (motos)", "Bulletins météo"])

    if source == "Books to Scrape":
        df = charger('books')
        c1, c2, c3 = st.columns(3)
        c1.metric("Livres", len(df))
        c2.metric("Prix médian (£)", round(df['price'].median(), 2))
        c3.metric("Note moyenne", round(df['rating'].mean(), 2))
        st.subheader("Prix médian par catégorie (15 premières)")
        st.bar_chart(df.groupby('category')['price'].median().sort_values(ascending=False).head(15))
        st.subheader("Répartition des notes")
        st.bar_chart(df['rating'].value_counts().sort_index())

    elif source == "Gaaraas (voitures)":
        df = charger('voitures_gaaraas')
        c1, c2, c3 = st.columns(3)
        c1.metric("Annonces", len(df))
        c2.metric("Prix médian (CFA)", int(df['prix'].median()))
        if 'km' in df.columns:
            c3.metric("Kilométrage médian", int(df['km'].median()))
        else:
            c3.metric("Régions", df['region'].nunique())
        top = df['marque'].value_counts().head(10).index
        st.subheader("Prix médian par marque (10 marques les plus fréquentes)")
        st.bar_chart(df[df['marque'].isin(top)].groupby('marque')['prix'].median())
        st.subheader("Nombre d'annonces par année")
        st.bar_chart(df['annee'].value_counts().sort_index())

    elif source == "Dakar-auto (motos)":
        df = charger('motos_dakar_auto')
        c1, c2, c3 = st.columns(3)
        c1.metric("Annonces", len(df))
        c2.metric("Prix médian (CFA)", int(df['prix'].median()))
        if 'km' in df.columns:
            c3.metric("Kilométrage médian", int(df['km'].median()))
        else:
            c3.metric("Régions", df['region'].nunique())
        top = df['marque'].value_counts().head(10).index
        st.subheader("Prix médian par marque (10 marques les plus fréquentes)")
        st.bar_chart(df[df['marque'].isin(top)].groupby('marque')['prix'].median())
        st.subheader("Neuf ou occasion")
        st.bar_chart(df['etat'].value_counts())

    else:
        df = charger('bulletins_meteo')
        c1, c2, c3 = st.columns(3)
        c1.metric("Relevés", len(df))
        c2.metric("Stations", df['station'].nunique())
        c3.metric("Record Tmax (°C)", df['maxmax'].max())
        st.subheader("Température maximale moyenne par station")
        st.bar_chart(df.groupby('station')['maxmax'].mean().sort_values(ascending=False))
        st.subheader("Température maximale moyenne par mois")
        ordre = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        par_mois = df.groupby('mois')['maxmax'].mean()
        par_mois = par_mois.reindex([m for m in ordre if m in par_mois.index])
        par_mois.index = [f"{ordre.index(m) + 1:02d} {m}" for m in par_mois.index]
        st.bar_chart(par_mois)

    with st.expander("Voir les données nettoyées"):
        st.dataframe(df)

# ---------- 4. Formulaires d'évaluation ----------
else:
    st.header("Évaluer l'application")
    st.link_button("Formulaire Kobo", "https://ee.kobotoolbox.org/x/J8hXYOS7")
    st.link_button("Formulaire Google Forms", "https://docs.google.com/forms/d/e/1FAIpQLSdqQsywxywfhWpfKhkF31Sa6w2iKHnc_sIziS03_roEeZAKoQ/viewform?usp=publish-editor")
