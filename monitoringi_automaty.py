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
import datetime



st.set_page_config(page_title='Monitoringi AUTOMATY', layout='wide')


sekcja = st.sidebar.radio(
    'Wybierz monitoring:',
    ('Wsparcie z natury','Cykl Q4','Genoptim')
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
#POTRZEBNE FUNKCJE
#1 Funkcja do wyodrębnienia wartości procentowej
def extract_percentage(text):
    import re
    match = re.search(r'(\d+,\d+|\d+)%', text)
    return match.group(0) if match else ''

#2 Funkcja do konwersji wartości procentowej na float
def percentage_to_float(percentage_str):
    if pd.isna(percentage_str) or not percentage_str:
        return 0.0  # Zmieniono na 0.0, aby brakujące wartości były traktowane jako 0
    # Zamiana przecinka na kropkę, usunięcie znaku '%'
    return float(percentage_str.replace(',', '.').replace('%', ''))


dzisiejsza_data = datetime.datetime.now().strftime("%d.%m.%Y")


 


############################################################################### WSPARCIE Z NATURY  ##############################################################################################
if sekcja == 'Wsparcie z natury':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label = "Wrzuć plik Cykl - soczyste rabaty"
    )
    if df:
        df = pd.read_excel(df, sheet_name = 'Promocje na utrzymanie', skiprows = 19, usecols = [1, 9])
        st.write(df.head())


    #usuń braki danych z Kod klienta
    df = df.dropna(subset=['KLIENT'])

    # klient na całkowite
    df['KLIENT'] = df['KLIENT'].astype(int)

    
    # Zmiana nazw kolumn
    df = df.rename(columns={'0.15.1': '15'})

    # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnach '12' lub '14' jest słowo 'powiązanie'
    df['SIECIOWY'] = df.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['15']).lower() else '', axis=1)

    #SPRAWDZENIE CZY DZIAŁA
    #df[df['SIECIOWY'] == 'SIECIOWY']
    #DZIAŁA :)

    
    # Zastosowanie funkcji do kolumn '12' i '14'
    df['15_percent'] = df['15'].apply(extract_percentage)


    # Konwersja kolumn '12_percent' i '14_percent' na liczby zmiennoprzecinkowe
    df['15_percent'] = df['15_percent'].apply(percentage_to_float)
    df = df.rename(columns={'15_percent':'max_percent'})


    # Wybierz wiersze, gdzie 'max_percent' nie jest równa 0
    filtered_df = df[df['max_percent'] != 0]

    standard = filtered_df[filtered_df['SIECIOWY'] != 'SIECIOWY']
    
    powiazanie = filtered_df[filtered_df['SIECIOWY'] == 'SIECIOWY']
    #len(standard), len(powiazanie), len(filtered_df)

    # Dodanie kolumny "CZY_OK", sprawdzającej długość tekstu
    powiazanie['KLIENT_S'] = powiazanie['KLIENT'].apply(lambda x: x if len(str(x)) == 5 else '')
    #powiazanie

    dane1 = powiazanie[powiazanie['KLIENT_S'].notna() & (powiazanie['KLIENT_S'] != '')]
    #dane1
    dane2 = powiazanie[powiazanie['KLIENT_S'].isna() | (powiazanie['KLIENT_S'] == '')]
    dane2 = dane2.rename(columns={'KLIENT':'Kod klienta'})
    #dane2
    #dane2.shape


    ######################################################### TERAZ IMS
    ims = st.file_uploader(
        label = "Wrzuć plik ims_nhd"
    )

    if ims:
        ims = pd.read_excel(ims, usecols=[0,2,19,21])
        st.write(ims.head())

    ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
    ims = ims[ims['APD_Rodzaj_farmaceutyczny'].isin(['AP - Apteka','ME - Sklep zielarsko - medyczny','PU - Punkt apteczny'])]

    #dane1 czyli te co są tylko kody sieciowe
    wynik_df = pd.merge(dane1, ims, left_on='KLIENT', right_on='Klient', how='left')

    # Wybór potrzebnych kolumn: 'APD_kod_SAP_apteki' i 'max_percent'
    wynik_df = wynik_df[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]


    #to są kody SAP
    wynik_df1 = wynik_df.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_df1 = wynik_df1[['Kod klienta','max_percent']]
    #wynik_df1
    #wynik_df1.shape

    #to są kody powiazan
    wynik_df2 = wynik_df.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_df2 = wynik_df2[['Kod klienta','max_percent']]
    #wynik_df2
    #wynik_df2.shape

    #POŁĄCZYĆ wynik_df z standard_ost
    polaczone = pd.concat([wynik_df1, wynik_df2], axis = 0)
    posortowane = polaczone.sort_values(by='max_percent', ascending=False)
    ostatecznie1 = posortowane.drop_duplicates(subset='Kod klienta')
    #ostatecznie1

    dane2 = dane2[['Kod klienta','max_percent']]

    ostateczne = pd.concat([ostatecznie1, dane2], axis = 0)
    ostateczne = ostateczne.sort_values(by='max_percent', ascending=False)
    ostateczne = ostateczne.drop_duplicates(subset='Kod klienta')
    #ostateczne.shape

    

    st.write('Jeśli to pierwszy monitoring, pobierz ten plik, jeśli nie, wrzuć plik z poprzedniego monitoringu i NIE POBIERAJ TEGO PLIKU')
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        ostateczne.to_excel(writer, index=False, sheet_name='Sheet1')
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
    result = ostateczne.merge(poprzedni[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
    result['old_percent'] = result['old_percent'].fillna(0)
    result['Czy dodać'] = result.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)
    st.write('Kliknij aby pobrać plik z kodami, które kody należy dodać')

    excel_file1 = io.BytesIO()
    with pd.ExcelWriter(excel_file1, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

    nazwa_pliku1 = f"WSPARCIE_Z_NATURY_{dzisiejsza_data}.xlsx"
    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz',
        data=excel_file1,
        file_name=nazwa_pliku1,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    result = result.drop(columns=['old_percent', 'Czy dodać'])


    st.write('Kliknij, aby pobrać plik z formułą max do następnego monitoringu')
    excel_file2 = io.BytesIO()
    with pd.ExcelWriter(excel_file2, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

    nazwa_pliku = f"FM_WSPARCIE_Z_NATURY_{dzisiejsza_data}.xlsx"
    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz nowy plik FORMUŁA MAX',
        data=excel_file2,
        file_name = nazwa_pliku,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


############################################################################### CYKL 4Q  ##############################################################################################
if sekcja == 'Cykl Q4':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label = "Wrzuć plik Cykl - Cykl Q4"
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

    
    # Zastosowanie funkcji do kolumn '12' i '14'
    df['12_percent'] = df['12'].apply(extract_percentage)
    df['14_percent'] = df['14'].apply(extract_percentage)


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
    ims = ims[ims['APD_Rodzaj_farmaceutyczny'].isin(['AP - Apteka','ME - Sklep zielarsko - medyczny','PU - Punkt apteczny'])]

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

    nazwa_pliku1 = f"CYKL_Q4_{dzisiejsza_data}.xlsx"
    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz',
        data=excel_file1,
        file_name=nazwa_pliku1,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    result = result.drop(columns=['old_percent', 'Czy dodać'])


    st.write('Kliknij, aby pobrać plik z formułą max do następnego monitoringu')
    excel_file2 = io.BytesIO()
    with pd.ExcelWriter(excel_file2, engine='xlsxwriter') as writer:
        result.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

    nazwa_pliku = f"FM_CYKL_Q4_{dzisiejsza_data}.xlsx"
    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz nowy plik FORMUŁA MAX',
        data=excel_file2,
        file_name = nazwa_pliku,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



############################################################################ GENOPTIM #################################################################
if sekcja == 'Genoptim':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label="Wrzuć plik Cykl - Genoptim"
    )
    
    if df:
        # Pobieramy listę dostępnych arkuszy
        xls = pd.ExcelFile(df)
        
        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'BRAZOFLAMIN' in xls.sheet_names:
            BRAZOFLAMIN = pd.read_excel(df, sheet_name='BRAZOFLAMIN', skiprows=18, usecols=[1, 8])
            st.write("Dane z arkusza BRAZOFLAMIN:")
            st.write(BRAZOFLAMIN.head())

        if 'DIAZEPAM' in xls.sheet_names:
            DIAZEPAM = pd.read_excel(df, sheet_name='DIAZEPAM', skiprows=18, usecols=[1, 8])
            st.write("Dane z arkusza DIAZEPAM:")
            st.write(DIAZEPAM.head())

        if 'ESCITALOPRAM' in xls.sheet_names:
            ESCITALOPRAM = pd.read_excel(df, sheet_name='ESCITALOPRAM', skiprows=18, usecols=[1, 8])
            st.write("Dane z arkusza ESCITALOPRAM:")
            st.write(ESCITALOPRAM.head())

      #  if 'LEVOFLOXACIN' in xls.sheet_names:
       #     LEVOFLOXACIN = pd.read_excel(df, skiprows=18, usecols=[1, 8])
        #    st.write("Dane z arkusza LEVOFLOXACIN GENOPTIM 500MG:")
         #   st.write(LEVOFLOXACIN.head())

    #usuń braki danych z Kod klienta
    BRAZOFLAMIN = BRAZOFLAMIN.dropna(subset=['KLIENT']) 
    DIAZEPAM = DIAZEPAM.dropna(subset=['KLIENT'])
    ESCITALOPRAM = ESCITALOPRAM.dropna(subset=['KLIENT'])
    #LEVOFLOXACIN = LEVOFLOXACIN.dropna(subset=['KLIENT']) 

    # klient na całkowite
    BRAZOFLAMIN['KLIENT'] = BRAZOFLAMIN['KLIENT'].astype(int)
    DIAZEPAM['KLIENT'] = DIAZEPAM['KLIENT'].astype(int)
    ESCITALOPRAM['KLIENT'] = ESCITALOPRAM['KLIENT'].astype(int)
    #LEVOFLOXACIN['KLIENT'] = LEVOFLOXACIN['KLIENT'].astype(int)


    # Usuwanie wierszy, gdzie w kolumnie 'pakiet' znajduje się słowo 'brak'
    BRAZOFLAMIN = BRAZOFLAMIN[BRAZOFLAMIN['pakiet'] != 'brak']
    DIAZEPAM = DIAZEPAM[DIAZEPAM['pakiet'] != 'brak']
    ESCITALOPRAM = ESCITALOPRAM[ESCITALOPRAM['pakiet'] != 'brak']
    #LEVOFLOXACIN = LEVOFLOXACIN[LEVOFLOXACIN['pakiet'] != 'brak']

    
    # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY'
    BRAZOFLAMIN['SIECIOWY'] = 'SIECIOWY'
    DIAZEPAM['SIECIOWY'] = 'SIECIOWY'
    ESCITALOPRAM['SIECIOWY'] = 'SIECIOWY'
    #LEVOFLOXACIN['SIECIOWY'] = 'SIECIOWY'
 
    
    # Zastosowanie funkcji do kolumn '12' i '14'
    BRAZOFLAMIN['max_percent'] = BRAZOFLAMIN['pakiet'].apply(extract_percentage)
    DIAZEPAM['max_percent'] = DIAZEPAM['pakiet'].apply(extract_percentage)
    ESCITALOPRAM['max_percent'] = ESCITALOPRAM['pakiet'].apply(extract_percentage)
    #LEVOFLOXACIN['max_percent'] = LEVOFLOXACIN['pakiet'].apply(extract_percentage)


    # Konwersja kolumny percent na liczby zmiennoprzecinkowe
    BRAZOFLAMIN['max_percent'] = BRAZOFLAMIN['max_percent'].apply(percentage_to_float)
    DIAZEPAM['max_percent'] = DIAZEPAM['max_percent'].apply(percentage_to_float)
    ESCITALOPRAM['max_percent'] = ESCITALOPRAM['max_percent'].apply(percentage_to_float)
    #LEVOFLOXACIN['max_percent'] = LEVOFLOXACIN['max_percent'].apply(percentage_to_float)


    # Wybierz wiersze, gdzie 'max_percent' nie jest równa 0
    BRAZOFLAMIN = BRAZOFLAMIN[BRAZOFLAMIN['max_percent'] != 0]
    DIAZEPAM = DIAZEPAM[DIAZEPAM['max_percent'] != 0]
    ESCITALOPRAM = ESCITALOPRAM[ESCITALOPRAM['max_percent'] != 0]
    #LEVOFLOXACIN = LEVOFLOXACIN[LEVOFLOXACIN['max_percent'] != 0]

    BRAZOFLAMIN = BRAZOFLAMIN[BRAZOFLAMIN['SIECIOWY'] == 'SIECIOWY']
    DIAZEPAM = DIAZEPAM[DIAZEPAM['SIECIOWY'] == 'SIECIOWY']
    ESCITALOPRAM = ESCITALOPRAM[ESCITALOPRAM['SIECIOWY'] == 'SIECIOWY']
    #LEVOFLOXACIN = LEVOFLOXACIN[LEVOFLOXACIN['SIECIOWY'] == 'SIECIOWY']


    BRAZOFLAMIN = BRAZOFLAMIN[['KLIENT', 'max_percent']]
    DIAZEPAM = DIAZEPAM[['KLIENT', 'max_percent']]
    ESCITALOPRAM = ESCITALOPRAM[['KLIENT', 'max_percent']]
    #LEVOFLOXACIN = LEVOFLOXACIN[['KLIENT', 'max_percent']]


    #TERAZ IMS
    ims = st.file_uploader(
        label = "Wrzuć plik ims_nhd"
    )

    if ims:
        ims = pd.read_excel(ims, usecols=[0,2,19,21])
        st.write(ims.head())

    ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
    ims = ims[ims['APD_Rodzaj_farmaceutyczny'].isin(['AP - Apteka','ME - Sklep zielarsko - medyczny','PU - Punkt apteczny'])]


    wynik_B = pd.merge(BRAZOFLAMIN, ims, left_on='KLIENT', right_on='Klient', how='left')
    wynik_D = pd.merge(DIAZEPAM, ims, left_on='KLIENT', right_on='Klient', how='left')
    wynik_E = pd.merge(ESCITALOPRAM, ims, left_on='KLIENT', right_on='Klient', how='left')
    #wynik_L = pd.merge(LEVO, ims, left_on='KLIENT', right_on='Klient', how='left')


    # Wybór potrzebnych kolumn: 'APD_kod_SAP_apteki' i 'max_percent'
    wynik_B = wynik_B[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
    wynik_D = wynik_D[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
    wynik_E = wynik_E[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
    #wynik_L = wynik_L[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
    
    
    #to są kody SAP
    wynik_B = wynik_B.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_B = wynik_B[['Kod klienta','max_percent']]
    #wynik_df1

    wynik_D = wynik_D.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_D = wynik_D[['Kod klienta','max_percent']]

    wynik_E = wynik_E.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_E = wynik_E[['Kod klienta','max_percent']]

    #wynik_L = wynik_L.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    #wynik_L = wynik_L[['Kod klienta','max_percent']]

    #to są kody powiazan
    wynik_B1 = wynik_B.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_B1 = wynik_B1[['Kod klienta','max_percent']]
    #wynik_df2

    wynik_D1 = wynik_D.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_D1 = wynik_D1[['Kod klienta','max_percent']]

    wynik_E1 = wynik_E.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_E1 = wynik_E1[['Kod klienta','max_percent']]

    #wynik_L1 = wynik_L.rename(columns={'KLIENT': 'Kod klienta'})
    #wynik_L1 = wynik_L1[['Kod klienta','max_percent']]

    #POŁĄCZYĆ wynik_df z standard_ost
    BRAZOFLAMIN = pd.concat([wynik_B, wynik_B1], axis = 0)
  
    BRAZOFLAMIN = BRAZOFLAMIN.sort_values(by='max_percent', ascending=False)

    BRAZOFLAMIN = BRAZOFLAMIN.drop_duplicates(subset='Kod klienta')
    

    DIAZEPAM = pd.concat([wynik_D, wynik_D1], axis = 0)
  
    DIAZEPAM = DIAZEPAM.sort_values(by='max_percent', ascending=False)

    DIAZEPAM = DIAZEPAM.drop_duplicates(subset='Kod klienta')


    ESCITALOPRAM = pd.concat([wynik_E, wynik_E1], axis = 0)
  
    ESCITALOPRAM = ESCITALOPRAM.sort_values(by='max_percent', ascending=False)

    ESCITALOPRAM = ESCITALOPRAM.drop_duplicates(subset='Kod klienta')
    

    #LEVOFLOXACIN = pd.concat([wynik_L, wynik_L1], axis = 0)
  
    #LEVOFLOXACIN = LEVOFLOXACIN.sort_values(by='max_percent', ascending=False)

    #LEVOFLOXACIN = LEVOFLOXACIN.drop_duplicates(subset='Kod klienta')


    st.write('Jeśli to pierwszy monitoring, pobierz ten plik, jeśli nie, wrzuć plik z poprzedniego monitoringu i NIE POBIERAJ TEGO PLIKU')
    excel_file = io.BytesIO()

    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
    # Jeśli dane BRAZOFLAMIN istnieją, zapisz je w odpowiednim arkuszu
        if 'BRAZOFLAMIN' in locals():
            BRAZOFLAMIN.to_excel(writer, index=False, sheet_name='BRAZOFLAMIN')

        # Jeśli dane diazepam istnieją, zapisz je w odpowiednim arkuszu
        if 'DIAZEPAM' in locals():
            DIAZEPAM.to_excel(writer, index=False, sheet_name='DIAZEPAM')

        # Jeśli dane diazepam istnieją, zapisz je w odpowiednim arkuszu
        if 'ESCITALOPRAM' in locals():
            ESCITALOPRAM.to_excel(writer, index=False, sheet_name='ESCITALOPRAM')

       # if 'LEVOFLOXACIN' in locals():
        #    LEVO.to_excel(writer, index=False, sheet_name='LEVOFLOXACIN')

    
    

    excel_file.seek(0)  # Resetowanie wskaźnika do początku pliku

    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz, jeśli to pierwszy monitoring',
        data=excel_file,
        file_name='czy_dodac.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Plik z poprzedniego monitoringu
    poprzedni = st.file_uploader(
        label="Wrzuć plik z poprzedniego monitoringu"
    )

    if poprzedni:
        xls = pd.ExcelFile(poprzedni)  # Pobranie pliku z arkuszami

    # Wczytanie danych z odpowiednich arkuszy
    if 'BRAZOFLAMIN' in xls.sheet_names:
        poprzedni_brazoflamin = pd.read_excel(poprzedni, sheet_name='BRAZOFLAMIN')
        st.write('Poprzedni monitoring - BRAZOFLAMIN:')
        st.write(poprzedni_brazoflamin.head())
    
    if 'DIAZEPAM' in xls.sheet_names:
        poprzedni_diazepam = pd.read_excel(poprzedni, sheet_name='DIAZEPAM')
        st.write('Poprzedni monitoring - DIAZEPAM:')
        st.write(poprzedni_diazepam.head())

    if 'ESCITALOPRAM' in xls.sheet_names:
        poprzedni_escitalopram = pd.read_excel(poprzedni, sheet_name='ESCITALOPRAM')
        st.write('Poprzedni monitoring - ESCITALOPRAM:')
        st.write(poprzedni_escilopram.head())

   # if 'LEVOFLOXACIN' in xls.sheet_names:
    #    poprzedni_levofloxacin = pd.read_excel(poprzedni, sheet_name='LEVOFLOXACIN')
     #   st.write('Poprzedni monitoring - LEVOFLOXACIN:')
      #  st.write(poprzedni_levofloxacin.head())


    # Przetwarzanie dla BRAZOFLAMIN
    if 'BRAZOFLAMIN' in locals() and 'poprzedni_brazoflamin' in locals():
        poprzedni_brazoflamin = poprzedni_brazoflamin.rename(columns={'max_percent': 'old_percent'})
        result_brazoflamin = BRAZOFLAMIN.merge(poprzedni_brazoflamin[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
        result_brazoflamin['old_percent'] = result_brazoflamin['old_percent'].fillna(0)
        result_brazoflamin['Czy dodać'] = result_brazoflamin.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)
    
    # Przetwarzanie dla DIAZEPAM
    if 'DIAZEPAM' in locals() and 'poprzedni_diazepam' in locals():
        poprzedni_diazepam = poprzedni_diazepam.rename(columns={'max_percent': 'old_percent'})
        result_diazepam = DIAZEPAM.merge(poprzedni_diazepam[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
        result_diazepam['old_percent'] = result_diazepam['old_percent'].fillna(0)
        result_diazepam['Czy dodać'] = result_diazepam.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)

    # Przetwarzanie dla DIAZEPAM
    if 'ESCITALOPRAM' in locals() and 'poprzedni_escilopram' in locals():
        poprzedni_escitalopram = poprzedni_escitalopram.rename(columns={'max_percent': 'old_percent'})
        result_escitalopram = ESCITALOPRAM.merge(poprzedni_escitalopram[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
        result_escitalopram['old_percent'] = result_escitalopram['old_percent'].fillna(0)
        result_escitalopram['Czy dodać'] = result_escitalopram.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)

   # if 'LEVOFLOXACIN' in locals() and 'poprzedni_levofloxacin' in locals():
    #    poprzedni_levofloxacin = poprzedni_levofloxacin.rename(columns={'max_percent': 'old_percent'})
     #   result_levofloxacin = LEVOFLOXACIN.merge(poprzedni_levofloxacin[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
      #  result_levofloxacin['old_percent'] = result_levofloxacin['old_percent'].fillna(0)
       # result_levofloxacin['Czy dodać'] = result_levofloxacin.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)


    # Zapisywanie plików do Excela
    excel_file1 = io.BytesIO()
    with pd.ExcelWriter(excel_file1, engine='xlsxwriter') as writer:
        if 'result_brazoflamin' in locals():
            result_brazoflamin.to_excel(writer, index=False, sheet_name='BRAZOFLAMIN')
        if 'result_diazepam' in locals():
            result_diazepam.to_excel(writer, index=False, sheet_name='DIAZEPAM')
        if 'result_escitalopram' in locals():
            result_escitalopram.to_excel(writer, index=False, sheet_name='ESCITALOPRAM')
      #  if 'result_levofloxacin' in locals():
       #     result_levofloxacin.to_excel(writer, index=False, sheet_name='LEVOFLOXACIN')

    excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

    # Definiowanie nazwy pliku
    nazwa_pliku = f"GENOPTIM_{dzisiejsza_data}.xlsx"
    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Kliknij aby pobrać plik z kodami, które kody należy dodać',
        data=excel_file1,
        file_name=nazwa_pliku,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
   


    result_brazoflamin = result_brazoflamin.drop(columns=['old_percent', 'Czy dodać'])
    result_diazepam = result_diazepam.drop(columns=['old_percent', 'Czy dodać'])
    result_escitalopram = result_escitalopram.drop(columns=['old_percent', 'Czy dodać'])
   # result_levofloxacin = result_levofloxacin.drop(columns=['old_percent', 'Czy dodać'])



    st.write('Kliknij, aby pobrać plik z formułą max do następnego monitoringu')

    # Tworzenie pliku Excel w pamięci
    excel_file2 = io.BytesIO()

    # Zapis do pliku Excel w pamięci
    with pd.ExcelWriter(excel_file2, engine='xlsxwriter') as writer:
        result_brazoflamin.to_excel(writer, index=False, sheet_name='BRAZOFLAMIN')
        result_diazepam.to_excel(writer, index=False, sheet_name='DIAZEPAM')
        result_escitalopram.to_excel(writer, index=False, sheet_name='ESCITALOPRAM')
        #result_levofloxacin.to_excel(writer, index=False, sheet_name='LEVOFLOXACIN')

    # Resetowanie wskaźnika do początku pliku
    excel_file2.seek(0) 

    # Definiowanie nazwy pliku
    nazwa_pliku = f"FM_GENOPTIM_{dzisiejsza_data}.xlsx"

    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz nowy plik FORMUŁA MAX',
        data=excel_file2,
        file_name=nazwa_pliku,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )





    
    























    
