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
    ('Soczyste rabaty','Paramig Fast Junior 250MG','Slideros','jakiś tam kolejny')
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



############################################################################### SOCZYSTE RABATY  ##############################################################################################
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
    ims = ims[~ims['APD_Rodzaj_farmaceutyczny'].isin(['DR - drogeria hurt', 'SZ - Szpital', 'IN - Inni', 'ZO - ZOZ', 'HA - Hurtownia farmaceutyczna apteczna', 'ZA - Apteka zakładowa', 'KI - Ogólnodostępna sieć handlowa', 
                                                     'GA Gabinet lekarski', 'HB - Hurtownia farmaceutyczna bez psychotropów', 'HU - Hurtownia farmaceutyczna z psychotropami', 'GW - Gabinet weterynaryjny', 'HP - Hurtownia farmaceutyczna apteczna - psychotropy',
                                                      'GP - Gabinet pielęgniarski','UC - Uczelnia','HK - Hurtownia farmaceutyczna apteczna kontrolowane','HO - Hurtownia z ograniczonym asortymentem','DP - Dom pomocy społ.','DR - drogeria hurt',
                                                      'HN - Hurtownia farmaceutyczna apteczna - narkotyki','BK - Badanie kliniczne','ZB - Typ ZOZ bez REGON14','IW - Izba wytrzeźwień','EX - Odbiorca zagraniczny','RA - Ratownictwo med.'])]


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




#############################################################        PARAMIG FAST JUNIOR 250                    ############################################################################


if sekcja == 'Paramig Fast Junior 250MG':
    st.write(tabs_font_css, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label = "Wrzuć plik Cykl Paramig"
    )
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name = 'PARAMIG FAST JUN 250MG od 20.08', skiprows = 16, usecols = [1,2,16,17,18,19,20,21,22])
        df1 = pd.read_excel(uploaded_file, sheet_name = 'MIX od 20.08', skiprows = 16, usecols = [1,2,13,14,15,16])
        st.write(df.head())
        st.write(df1.head())

    #usuń braki danych z Kod klienta
    df = df.dropna(subset=['Kod klienta'])
    df1 = df1.dropna(subset=['Kod klienta'])

    # klient na całkowite
    df['KLIENT'] = df['KLIENT'].astype(int)
    df1['KLIENT'] = df1['KLIENT'].astype(int)
    
    df['Kod klienta'] = df['Kod klienta'].astype(int)
    df1['Kod klienta'] = df1['Kod klienta'].astype(int)
    

    #Zmiana nazw kolumn
    df = df.rename(columns={'0.08.3': '8', '0.1.3': '10', '0.13.3': '13', '0.08.4': '8_1', '0.1.4': '10_1', '0.13.4': '13_1', '0.13.5':'13_2'})
    df1 = df1.rename(columns={'0.1.3': '10', '0.13.3': '13', '0.1.4': '10_1', '0.13.4': '13_1'})
    

    # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnachjest słowo 'powiązanie'
    df['SIECIOWY'] = df.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['8']).lower() or 'powiązanie' in str(row['10']).lower() or 'powiązanie' in str(row['13']).lower()
                              or 'powiązanie' in str(row['8_1']).lower() or 'powiązanie' in str(row['10_1']).lower() or 'powiązanie' in str(row['13_1']).lower()
                              or 'powiązanie' in str(row['13_2']).lower() else '', axis=1)

    
    
    

    def classify_row(row):
        if 'powiązanie' in str(row['10']).lower() or \
           'powiązanie' in str(row['13']).lower() or \
           'powiązanie' in str(row['10_1']).lower() or \
           'powiązanie' in str(row['13_1']).lower():
            return 'SIECIOWY'
        else:
            return ''

    df1['SIECIOWY'] = df1.apply(classify_row, axis=1)


    # Zastosowanie funkcji do kolumn
    df['8_percent'] = df['8'].apply(extract_percentage)
    df['10_percent'] = df['10'].apply(extract_percentage)
    df['13_percent'] = df['13'].apply(extract_percentage)
    df['8_1_percent'] = df['8_1'].apply(extract_percentage)
    df['10_1_percent'] = df['10_1'].apply(extract_percentage)
    df['13_1_percent'] = df['13_1'].apply(extract_percentage)
    df['13_2_percent'] = df['13_2'].apply(extract_percentage)

    df1['10_percent'] = df1['10'].apply(extract_percentage)
    df1['13_percent'] = df1['13'].apply(extract_percentage)
    df1['10_1_percent'] = df1['10_1'].apply(extract_percentage)
    df1['13_1_percent'] = df1['13_1'].apply(extract_percentage)


    
    # Konwersja kolumn na liczby zmiennoprzecinkowe
    df['8_percent'] = df['8_percent'].apply(percentage_to_float)
    df['10_percent'] = df['10_percent'].apply(percentage_to_float)
    df['13_percent'] = df['13_percent'].apply(percentage_to_float)
    df['8_1_percent'] = df['8_1_percent'].apply(percentage_to_float)
    df['10_1_percent'] = df['10_1_percent'].apply(percentage_to_float)
    df['13_1_percent'] = df['13_1_percent'].apply(percentage_to_float)
    df['13_2_percent'] = df['13_2_percent'].apply(percentage_to_float)

    df1['10_percent'] = df1['10_percent'].apply(percentage_to_float)
    df1['13_percent'] = df1['13_percent'].apply(percentage_to_float)
    df1['10_1_percent'] = df1['10_1_percent'].apply(percentage_to_float)
    df1['13_1_percent'] = df1['13_1_percent'].apply(percentage_to_float)
    

    # Dodaj nową kolumnę 'max_percent' z maksymalnymi wartościami z kolumn 
    df['max_percent'] = df[['8_percent', '10_percent', '13_percent', '8_1_percent', '10_1_percent', '13_1_percent', '13_2_percent']].max(axis=1)
    df1['max_percent'] = df1[['10_percent', '13_percent', '10_1_percent', '13_1_percent']].max(axis=1)

    # Wybierz wiersze, gdzie 'max_percent' nie jest równa 0
    filtered_df = df[df['max_percent'] != 0]
    filtered_df1 = df1[df1['max_percent'] != 0]

    standard = filtered_df[filtered_df['SIECIOWY'] != 'SIECIOWY']
    powiazanie = filtered_df[filtered_df['SIECIOWY'] == 'SIECIOWY']

    standard1 = filtered_df1[filtered_df1['SIECIOWY'] != 'SIECIOWY']
    powiazanie1 = filtered_df1[filtered_df1['SIECIOWY'] == 'SIECIOWY']

    #len(standard), len(powiazanie), len(filtered_df)

    standard_ost = standard[['Kod klienta', 'max_percent']]

    powiazanie = powiazanie[['KLIENT','Kod klienta','max_percent']]

    standard_ost1 = standard1[['Kod klienta', 'max_percent']]

    powiazanie1 = powiazanie1[['KLIENT','Kod klienta','max_percent']]




    #########################################         TERAZ IMS
    ims = st.file_uploader(
        label = "Wrzuć plik ims_nhd"
    )

    if ims:
        ims = pd.read_excel(ims, usecols=[0,2,19,21])
        st.write(ims.head())

    ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
    ims = ims[~ims['APD_Rodzaj_farmaceutyczny'].isin(['DR - drogeria hurt', 'SZ - Szpital', 'IN - Inni', 'ZO - ZOZ', 'HA - Hurtownia farmaceutyczna apteczna', 'ZA - Apteka zakładowa', 'KI - Ogólnodostępna sieć handlowa', 
                                                     'GA Gabinet lekarski', 'HB - Hurtownia farmaceutyczna bez psychotropów', 'HU - Hurtownia farmaceutyczna z psychotropami', 'GW - Gabinet weterynaryjny', 'HP - Hurtownia farmaceutyczna apteczna - psychotropy',
                                                      'GP - Gabinet pielęgniarski','UC - Uczelnia','HK - Hurtownia farmaceutyczna apteczna kontrolowane','HO - Hurtownia z ograniczonym asortymentem','DP - Dom pomocy społ.','DR - drogeria hurt',
                                                      'HN - Hurtownia farmaceutyczna apteczna - narkotyki','BK - Badanie kliniczne','ZB - Typ ZOZ bez REGON14','IW - Izba wytrzeźwień','EX - Odbiorca zagraniczny','RA - Ratownictwo med.'])]


    wynik_df = pd.merge(powiazanie, ims, left_on='KLIENT', right_on='Klient', how='left')
    wynik_df1 = pd.merge(powiazanie1, ims, left_on='KLIENT', right_on='Klient', how='left')

    # Wybór potrzebnych kolumn: 'APD_kod_SAP_apteki' i 'max_percent'
    wynik_df = wynik_df[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
    wynik_df1 = wynik_df1[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]

    #### do tego pierwszego
    #to są kody SAP
    wynik_df_1 = wynik_df.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_df_1 = wynik_df_1[['Kod klienta','max_percent']]
    #wynik_df1

    #to są kody powiazan
    wynik_df_2 = wynik_df.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_df_2 = wynik_df_2[['Kod klienta','max_percent']]
    #wynik_df2

    #POŁĄCZYĆ wynik_df z standard_ost
    polaczone = pd.concat([standard_ost, wynik_df_1, wynik_df_2], axis = 0)
  
    posortowane = polaczone.sort_values(by='max_percent', ascending=False)

    ostatecznie = posortowane.drop_duplicates(subset='Kod klienta')



    
    ### do tego drugiego
    wynik_df_11 = wynik_df1.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
    wynik_df_11 = wynik_df_11[['Kod klienta','max_percent']]
    #wynik_df1

    #to są kody powiazan
    wynik_df_21 = wynik_df1.rename(columns={'KLIENT': 'Kod klienta'})
    wynik_df_21 = wynik_df_21[['Kod klienta','max_percent']]
    #wynik_df2

    #POŁĄCZYĆ wynik_df z standard_ost
    polaczone1 = pd.concat([standard_ost1, wynik_df_11, wynik_df_21], axis = 0)
  
    posortowane1 = polaczone1.sort_values(by='max_percent', ascending=False)

    ostatecznie1 = posortowane.drop_duplicates(subset='Kod klienta')


    combined_df = pd.concat([ostatecznie, ostatecznie1], ignore_index=True)
    max_rabaty = combined_df.groupby('Kod klienta')['max_percent'].max().reset_index()
    max_rabaty

    
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
        label = "Wrzuć plik Slideros"
    )
    if df:
        df = pd.read_excel(df, sheet_name = 'Promocje_rabat', skiprows = 17, usecols = [1,2,25,26,27,28,29,30,31,32])
        st.write(df.head())

    #usuń braki danych z Kod klienta
    df = df.dropna(subset=['Kod klienta'])
    # klient na całkowite
    df['KLIENT'] = df['KLIENT'].astype(int)
    df['Kod klienta'] = df['Kod klienta'].astype(int)
    # Zmiana nazw kolumn
    df = df.rename(columns={'0.08.3': '8', '0.1.3': '10', '0.12.3':'12.1' , '0.12.4':'12.2' , '0.14.3':'14' , '0.15.3': '15', '0.17.3':'17.1', '0.17.4':'17.2'})

    # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnach '12' lub '14' jest słowo 'powiązanie'
    df['SIECIOWY'] = df.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['8']).lower() or 'powiązanie' in str(row['10']).lower() 
                              or 'powiązanie' in str(row['12.1']).lower() or 'powiązanie' in str(row['12.2']).lower() 
                              or 'powiązanie' in str(row['14']).lower() or 'powiązanie' in str(row['15']).lower() 
                              or 'powiązanie' in str(row['17.1']).lower() or 'powiązanie' in str(row['17.2']).lower() else '', axis=1)
    df['8_percent'] = df['8'].apply(extract_percentage)
    df['10_percent'] = df['10'].apply(extract_percentage)
    df['12.1_percent'] = df['12.1'].apply(extract_percentage)
    df['12.2_percent'] = df['12.2'].apply(extract_percentage)
    df['14_percent'] = df['14'].apply(extract_percentage)
    df['15_percent'] = df['15'].apply(extract_percentage)
    df['17.1_percent'] = df['17.1'].apply(extract_percentage)
    df['17.2_percent'] = df['17.2'].apply(extract_percentage)

    df['8_percent'] = df['8_percent'].apply(percentage_to_float)
    df['10_percent'] = df['10_percent'].apply(percentage_to_float)
    df['12.1_percent'] = df['12.1_percent'].apply(percentage_to_float)
    df['12.2_percent'] = df['12.2_percent'].apply(percentage_to_float)
    df['14_percent'] = df['14_percent'].apply(percentage_to_float)
    df['15_percent'] = df['15_percent'].apply(percentage_to_float)
    df['17.1_percent'] = df['17.1_percent'].apply(percentage_to_float)
    df['17.2_percent'] = df['17.2_percent'].apply(percentage_to_float)

    # Dodaj nową kolumnę 'max_percent' z maksymalnymi wartościami z kolumn '12_percent' i '14_percent'
    df['max_percent'] = df[['8_percent', '10_percent', '12.1_percent', '12.2_percent', '14_percent', '15_percent', 
                            '17.1_percent', '17.2_percent']].max(axis=1)

    # Wybierz wiersze, gdzie 'max_percent' nie jest równa 0
    filtered_df = df[df['max_percent'] != 0]

    standard = filtered_df[filtered_df['SIECIOWY'] != 'SIECIOWY']
    powiazanie = filtered_df[filtered_df['SIECIOWY'] == 'SIECIOWY']

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





    
