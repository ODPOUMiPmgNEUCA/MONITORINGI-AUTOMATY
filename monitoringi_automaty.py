# -*- coding: utf-8 -*-
"""Soczyste rabaty.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1bfU5lwdNa2GOPWmQ9-URaf30VnlBzQC0
"""

#importowanie potrzebnych bibliotek
import os
import openpyxl
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
import io



st.set_page_config(page_title='Monitoringi AUTOMATY', layout='wide')


sekcja = st.sidebar.radio(
    'Wybierz monitoring:',
    ('Soczyste rabaty','Slideros')
 )

tabs_font_css = """
<style>
div[class*="stTextInput"] label {
  font-size: 26px;
  color: black;
}
div[class*="stSelectbox"] label {
  font-size: 26px;
  color: black;
}
</style>
"""


#SOCZYSTE RABATY
if sekcja == 'Soczyste rabaty':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label = "Wrzuć plik Cykl - soczyste rabaty"
    )
    if df:
        df = pd.read_excel(df, sheet_name = 'Promocje na utrzymanie i FUS', skiprows = 15, usecols = [1,2,9,10])
        st.write(df.head())


    #usuń braki danych z Kod klienta
    df = df.dropna(subset=['Kod klienta'])

    # klient na całkowite
    df['KLIENT'] = df['KLIENT'].astype(int)
    df['Kod klienta'] = df['Kod klienta'].astype(int)

    # Zmiana nazw kolumn
    df = df.rename(columns={'0.12.1': '12', '0.14.1': '14'})

    # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnach '12' lub '14' jest słowo 'powiązanie'
    df['SIECIOWY'] = df.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['12']).lower() or 'powiązanie' in str(row['14']).lower() else '', axis=1)

    #SPRAWDZENIE CZY DZIAŁA
    #df[df['SIECIOWY'] == 'SIECIOWY']
    #DZIAŁA :)

    #Funkcja do wyodrębnienia wartości procentowej
    def extract_percentage(text):
        import re
        match = re.search(r'(\d+,\d+|\d+)%', text)
        return match.group(0) if match else ''

    # Zastosowanie funkcji do kolumn '12' i '14'
    df['12_percent'] = df['12'].apply(extract_percentage)
    df['14_percent'] = df['14'].apply(extract_percentage)

    # Funkcja do konwersji wartości procentowej na float
    def percentage_to_float(percentage_str):
        if pd.isna(percentage_str) or not percentage_str:
            return 0.0  # Zmieniono na 0.0, aby brakujące wartości były traktowane jako 0
        # Zamiana przecinka na kropkę, usunięcie znaku '%'
        return float(percentage_str.replace(',', '.').replace('%', ''))

    # Konwersja kolumn '12_percent' i '14_percent' na liczby zmiennoprzecinkowe
    df['12_percent'] = df['12_percent'].apply(percentage_to_float)
    df['14_percent'] = df['14_percent'].apply(percentage_to_float)

    # Dodaj nową kolumnę 'max_percent' z maksymalnymi wartościami z kolumn '12_percent' i '14_percent'
    df['max_percent'] = df[['12_percent', '14_percent']].max(axis=1)

    # Wybierz wiersze, gdzie 'max_percent' nie jest równa 0
    filtered_df = df[df['max_percent'] != 0]

    standard = filtered_df[filtered_df['SIECIOWY'] != 'SIECIOWY']
    powiazanie = filtered_df[filtered_df['SIECIOWY'] == 'SIECIOWY']

    #len(standard), len(powiazanie), len(filtered_df)

    standard_ost = standard[['Kod klienta', 'max_percent']]

    powiazanie = powiazanie[['KLIENT','Kod klienta','max_percent']]



    #TERAZ IMS
    ims = st.file_uploader(
        label = "Wrzuć plik ims_nhd"
    )

    if ims:
        ims = pd.read_excel(ims, usecols=[0,2,19,21])
        st.write(ims.head())

    ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
    ims = ims[~ims['APD_Rodzaj_farmaceutyczny'].isin(['DR - drogeria hurt', 'SZ - Szpital', 'IN - Inni', 'ZO - ZOZ', 'HA - Hurtownia farmaceutyczna apteczna'])]


    wynik_df = pd.merge(powiazanie, ims, left_on='KLIENT', right_on='Klient', how='left')

    # Wybór potrzebnych kolumn: 'APD_kod_SAP_apteki' i 'max_percent'
    wynik_df = wynik_df[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]


    #to są kody SAP
    wynik_df1 = wynik_df.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_df1 = wynik_df1[['Kod klienta','max_percent']]
    #wynik_df1

    #to są kody powiazan
    wynik_df2 = wynik_df.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_df2 = wynik_df2[['Kod klienta','max_percent']]
    #wynik_df2

    #POŁĄCZYĆ wynik_df z standard_ost
    polaczone = pd.concat([standard_ost, wynik_df1, wynik_df2], axis = 0)
  
    posortowane = polaczone.sort_values(by='max_percent', ascending=False)

    ostatecznie = posortowane.drop_duplicates(subset='Kod klienta')


    st.write('Jeśli to pierwszy monitoring, pobierz ten plik, jeśli nie, wrzuć plik z poprzedniego monitoringu i NIE POBIERAJ TEGO PLIKU')
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        ostatecznie.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_file.seek(0)  # Resetowanie wskaźnika do początku pliku

    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz, jeśli to pierwszy monitoring',
        data=excel_file,
        file_name='czy_dodac.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    #plik z poprzedniego monitoringu
    poprzedni = st.file_uploader(
        label = "Wrzuć plik z poprzedniego monitoringu"
    )

    if poprzedni:
        poprzedni = pd.read_excel(poprzedni)
        st.write(poprzedni.head())

    poprzedni = poprzedni.rename(columns={'max_percent': 'old_percent'})
    # Wykonanie left join, dodanie 'old_percent' do pliku 'ostatecznie'
    result = ostatecznie.merge(poprzedni[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
    result['old_percent'] = result['old_percent'].fillna(0)
    result['Czy dodać'] = result.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)
    st.write('Kliknij aby pobrać plik z kodami, które kody należy dodać')

    excel_file1 = io.BytesIO()
    with pd.ExcelWriter(excel_file1, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz',
        data=excel_file1,
        file_name='czy_dodac.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    result = result.drop(columns=['old_percent', 'Czy dodać'])


    st.write('Kliknij, aby pobrać plik z formułą max do następnego monitoringu')
    excel_file2 = io.BytesIO()
    with pd.ExcelWriter(excel_file2, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz nowy plik FORMUŁA MAX',
        data=excel_file2,
        file_name='formula_max.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )





#SLIDEROS
if sekcja == 'Slideros':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label = "Wrzuć plik Slideros max formuły"
    )
    if df:
        df = pd.read_excel(df, sheet_name = 'Promocje_rabat', skiprows = 17, usecols = [1,2,9,15,16,17,18,19,20,21,22])
        st.write(df.head())

    
