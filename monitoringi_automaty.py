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
    ('Cykl Q1','Musy','Plastry','Alergia')
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




############################################################################### CYKL Q1  ##############################################################################################
if sekcja == 'Cykl Q1':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label = "Wrzuć plik Cykl - Cykl Q1"
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

    nazwa_pliku1 = f"CYKL_Q1_{dzisiejsza_data}.xlsx"
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

    nazwa_pliku = f"FM_CYKL_Q1_{dzisiejsza_data}.xlsx"
    # Umożliwienie pobrania pliku Excel
    st.download_button(
        label='Pobierz nowy plik FORMUŁA MAX',
        data=excel_file2,
        file_name = nazwa_pliku,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




############################################################################# MUSY #####################################################################################

if sekcja == 'Musy':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label="Wrzuć plik Cykl - Musy"
    )
    
    if df:
        # Pobieramy listę dostępnych arkuszy
        xls = pd.ExcelFile(df)
        
        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Rabat' in xls.sheet_names:
            Rabat = pd.read_excel(df, sheet_name='Rabat', skiprows=15, usecols=[1, 2, 13, 14, 15])
            st.write("Dane z arkusza Rabat:")
            st.write(Rabat.head())


        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Gratisy, rabat' in xls.sheet_names:
            Gratisy = pd.read_excel(df, sheet_name='Gratisy, rabat', skiprows=12, usecols=[1, 2, 8])
            st.write("Dane z arkusza Gratisy, rabat:")
            st.write(Gratisy.head())


        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Ekspozytor z gratisem, rabat' in xls.sheet_names:
            Eksp = pd.read_excel(df, sheet_name='Ekspozytor z gratisem, rabat', skiprows=12, usecols=[1, 2, 9, 10])
            st.write("Dane z arkusza Ekspozytor z gratisem, rabat:")
            st.write(Eksp.head())

        #usuń braki danych z Kod klienta
        Rabat = Rabat.dropna(subset=['KLIENT']) 
        Gratisy = Gratisy.dropna(subset=['KLIENT'])
        Eksp = Eksp.dropna(subset=['KLIENT'])

        # klient na całkowite
        Rabat['KLIENT'] = Rabat['KLIENT'].astype(int)
        Gratisy['KLIENT'] = Gratisy['KLIENT'].astype(int)
        Eksp['KLIENT'] = Eksp['KLIENT'].astype(int)


        Rabat.columns=['KLIENT','Kod klienta','12','16','18']
        Gratisy.columns=['KLIENT','Kod klienta','18']
        Eksp = Eksp.rename(columns={'0.13.1': '13', '0.16.1' : '16'})

        
        # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnach '12' lub '14' jest słowo 'powiązanie'
        Rabat['SIECIOWY'] = Rabat.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['12']).lower() or 'powiązanie' in str(row['16']).lower() or 'powiązanie' in str(row['18']).lower() else '', axis=1)
        Gratisy['SIECIOWY'] = Gratisy.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['18']).lower() else '', axis=1)
        Eksp['SIECIOWY'] = Eksp.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['13']).lower() or 'powiązanie' in str(row['16']).lower() else '', axis=1)

        Rabat['12_percent'] = Rabat['12'].apply(extract_percentage)
        Rabat['16_percent'] = Rabat['16'].apply(extract_percentage)
        Rabat['18_percent'] = Rabat['18'].apply(extract_percentage)
        Gratisy['18_percent'] = Gratisy['18'].apply(extract_percentage)
        Eksp['13_percent'] = Eksp['13'].apply(extract_percentage)
        Eksp['16_percent'] = Eksp['16'].apply(extract_percentage)

        # na zmiennoprzecinkowe
        Rabat['12_percent'] = Rabat['12_percent'].apply(percentage_to_float)
        Rabat['16_percent'] = Rabat['16_percent'].apply(percentage_to_float)
        Rabat['18_percent'] = Rabat['18_percent'].apply(percentage_to_float)
        Gratisy['18_percent'] = Gratisy['18_percent'].apply(percentage_to_float)
        Eksp['13_percent'] = Eksp['13_percent'].apply(percentage_to_float)
        Eksp['16_percent'] = Eksp['16_percent'].apply(percentage_to_float)
    
        # Dodaj nową kolumnę 'max_percent'
        Rabat1 = Rabat[Rabat['SIECIOWY'] == 'SIECIOWY']
        Rabat2 = Rabat[Rabat['SIECIOWY'] != 'SIECIOWY']
        Rabat1['max_percent'] = Rabat1[['12_percent', '16_percent', '18_percent']].max(axis=1)
        Rabat2['max_percent'] = Rabat2[['12_percent', '16_percent', '18_percent']].max(axis=1)

        Gratisy1 = Gratisy[Gratisy['SIECIOWY'] == 'SIECIOWY']
        Gratisy2 = Gratisy[Gratisy['SIECIOWY'] != 'SIECIOWY']
        Gratisy1['max_percent'] = Gratisy1[['18_percent']].max(axis=1)
        Gratisy2['max_percent'] = Gratisy2[['18_percent']].max(axis=1)

        Eksp1 = Eksp[Eksp['SIECIOWY'] == 'SIECIOWY']
        Eksp2 = Eksp[Eksp['SIECIOWY'] != 'SIECIOWY']
        Eksp1['max_percent'] = Eksp1[['13_percent', '16_percent']].max(axis=1)
        Eksp2['max_percent'] = Eksp2[['13_percent', '16_percent']].max(axis=1)

        ###### 1 to SIECIOWI, 2 to punkt dostaw
        Rabat1 = Rabat1[['KLIENT','Kod klienta','max_percent']]
        Gratisy1 = Gratisy1[['KLIENT','Kod klienta','max_percent']]
        Eksp1 = Eksp1[['KLIENT','Kod klienta','max_percent']]

        Rabat2 = Rabat2[['Kod klienta','max_percent']]
        Gratisy2 = Gratisy2[['Kod klienta','max_percent']]
        Eksp2 = Eksp2[['Kod klienta','max_percent']]
        
        stand = pd.concat([Rabat2, Gratisy2, Eksp2], ignore_index=True)
        pow = pd.concat([Rabat1, Gratisy1, Eksp1], ignore_index=True)


        #TERAZ IMS
        ims = st.file_uploader(
            label = "Wrzuć plik ims_nhd"
        )
    
        if ims:
            ims = pd.read_excel(ims, usecols=[0,2,19,21])
            st.write(ims.head())
    
        ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
        ims = ims[ims['APD_Rodzaj_farmaceutyczny'].isin(['AP - Apteka','ME - Sklep zielarsko - medyczny','PU - Punkt apteczny'])]
    
        wynik_df = pd.merge(pow, ims, left_on='KLIENT', right_on='Klient', how='left')
    
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
        polaczone = pd.concat([stand, wynik_df1, wynik_df2], axis = 0)
  
        posortowane = polaczone.sort_values(by='max_percent', ascending=False)

        ostatecznie = posortowane.drop_duplicates(subset='Kod klienta')
        ostatecznie = ostatecznie[ostatecznie['max_percent'] != 0]

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
    
        nazwa_pliku1 = f"MUSY_{dzisiejsza_data}.xlsx"
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
    
        nazwa_pliku = f"FM_MUSY_{dzisiejsza_data}.xlsx"
        # Umożliwienie pobrania pliku Excel
        st.download_button(
            label='Pobierz nowy plik FORMUŁA MAX',
            data=excel_file2,
            file_name = nazwa_pliku,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )



############################################################################# PLASTRY #####################################################################################

if sekcja == 'Plastry':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label="Wrzuć plik Cykl - Plastry"
    )
    
    if df:
        # Pobieramy listę dostępnych arkuszy
        xls = pd.ExcelFile(df)
        
        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Rabat' in xls.sheet_names:
            Rabat = pd.read_excel(df, sheet_name='Rabat', skiprows=18, usecols=[1, 2, 19, 20, 21, 22])
            st.write("Dane z arkusza Rabat:")
            st.write(Rabat.head())

        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Ekspozytor, rabat' in xls.sheet_names:
            Eksp = pd.read_excel(df, sheet_name='Ekspozytor, rabat', skiprows=15, usecols=[1, 2, 11])
            st.write("Dane z arkusza Ekspozytor, rabat:")
            st.write(Eksp.head())

        #usuń braki danych z Kod klienta
        Rabat = Rabat.dropna(subset=['KLIENT']) 
        Eksp = Eksp.dropna(subset=['KLIENT'])

        # klient na całkowite
        Rabat['KLIENT'] = Rabat['KLIENT'].astype(int)
        Eksp['KLIENT'] = Eksp['KLIENT'].astype(int)


        Rabat.columns=['KLIENT','Kod klienta','9','14','18','20']
        Eksp.columns=['KLIENT','Kod klienta','14']
 
        
        # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnach '12' lub '14' jest słowo 'powiązanie'
        Rabat['SIECIOWY'] = Rabat.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['9']).lower() or 'powiązanie' in str(row['14']).lower() 
                                        or 'powiązanie' in str(row['18']).lower() or 'powiązanie' in str(row['20']).lower() else '', axis=1)
        Eksp['SIECIOWY'] = Eksp.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['14']).lower() else '', axis=1)

        Rabat['9_percent'] = Rabat['9'].apply(extract_percentage)
        Rabat['14_percent'] = Rabat['14'].apply(extract_percentage)
        Rabat['18_percent'] = Rabat['18'].apply(extract_percentage)
        Rabat['20_percent'] = Rabat['20'].apply(extract_percentage)
        Eksp['14_percent'] = Eksp['14'].apply(extract_percentage)

        # na zmiennoprzecinkowe
        Rabat['9_percent'] = Rabat['9_percent'].apply(percentage_to_float)
        Rabat['14_percent'] = Rabat['14_percent'].apply(percentage_to_float)
        Rabat['18_percent'] = Rabat['18_percent'].apply(percentage_to_float)
        Rabat['20_percent'] = Rabat['20_percent'].apply(percentage_to_float)
        Eksp['14_percent'] = Eksp['14_percent'].apply(percentage_to_float)
    
        # Dodaj nową kolumnę 'max_percent'
        Rabat1 = Rabat[Rabat['SIECIOWY'] == 'SIECIOWY']
        Rabat2 = Rabat[Rabat['SIECIOWY'] != 'SIECIOWY']
        Rabat1['max_percent'] = Rabat1[['9_percent', '14_percent', '18_percent','20_percent']].max(axis=1)
        Rabat2['max_percent'] = Rabat2[['9_percent', '14_percent', '18_percent','20_percent']].max(axis=1)

        Eksp1 = Eksp[Eksp['SIECIOWY'] == 'SIECIOWY']
        Eksp2 = Eksp[Eksp['SIECIOWY'] != 'SIECIOWY']
        Eksp1['max_percent'] = Eksp1[['14_percent']].max(axis=1)
        Eksp2['max_percent'] = Eksp2[['14_percent']].max(axis=1)

        ###### 1 to SIECIOWI, 2 to punkt dostaw
        Rabat1 = Rabat1[['KLIENT','Kod klienta','max_percent']]
        Eksp1 = Eksp1[['KLIENT','Kod klienta','max_percent']]

        Rabat2 = Rabat2[['Kod klienta','max_percent']]
        Eksp2 = Eksp2[['Kod klienta','max_percent']]
        
        stand = pd.concat([Rabat2, Eksp2], ignore_index=True)
        pow = pd.concat([Rabat1, Eksp1], ignore_index=True)

        
        #TERAZ IMS
        ims = st.file_uploader(
            label = "Wrzuć plik ims_nhd"
        )
    
        if ims:
            ims = pd.read_excel(ims, usecols=[0,2,19,21])
            st.write(ims.head())
    
        ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
        ims = ims[ims['APD_Rodzaj_farmaceutyczny'].isin(['AP - Apteka','ME - Sklep zielarsko - medyczny','PU - Punkt apteczny'])]
    
        wynik_df = pd.merge(pow, ims, left_on='KLIENT', right_on='Klient', how='left')
    
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
        polaczone = pd.concat([stand, wynik_df1, wynik_df2], axis = 0)
  
        posortowane = polaczone.sort_values(by='max_percent', ascending=False)

        ostatecznie = posortowane.drop_duplicates(subset='Kod klienta')
        ostatecznie = ostatecznie[ostatecznie['max_percent'] != 0]

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
    
        nazwa_pliku1 = f"PLASTRY_{dzisiejsza_data}.xlsx"
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
    
        nazwa_pliku = f"FM_PLASTRY_{dzisiejsza_data}.xlsx"
        # Umożliwienie pobrania pliku Excel
        st.download_button(
            label='Pobierz nowy plik FORMUŁA MAX',
            data=excel_file2,
            file_name = nazwa_pliku,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


############################################################################# ALERGIA #####################################################################################

if sekcja == 'Alergia':
    st.write(tabs_font_css, unsafe_allow_html=True)

    df = st.file_uploader(
        label="Wrzuć plik Cykl - Alergia"
    )
    
    if df:
        # Pobieramy listę dostępnych arkuszy
        xls = pd.ExcelFile(df)
        
        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Levalergedd_rabat' in xls.sheet_names:
            Lr = pd.read_excel(df, sheet_name='Levalergedd_rabat', skiprows=15, usecols=[1, 2, 12, 13, 14, 15, 16])
            st.write("Dane z arkusza Levalergedd_rabat:")
            st.write(Lr.head())

        # Sprawdzamy, które arkusze są dostępne i wczytujemy odpowiednie dane
        if 'Cetalergedd_rabat' in xls.sheet_names:
            Cr = pd.read_excel(df, sheet_name='Cetalergedd_rabat', skiprows=15, usecols=[1, 2, 12, 13, 14, 15, 16])
            st.write("Dane z arkusza Cetalergedd_rabat")
            st.write(Cr.head())


        #usuń braki danych z Kod klienta
        Lr = Lr.dropna(subset=['KLIENT']) 
        Cr = Cr.dropna(subset=['KLIENT'])

        # klient na całkowite
        Lr['KLIENT'] = Lr['KLIENT'].astype(int)
        Cr['KLIENT'] = Cr['KLIENT'].astype(int)


        Lr.columns=['KLIENT','Kod klienta','15','18','20','22','25']
        Cr.columns=['KLIENT','Kod klienta','15','18','20','22','25']
 
        
        # Dodaj kolumnę 'SIECIOWY', która będzie zawierać 'SIECIOWY' jeśli w kolumnach '12' lub '14' jest słowo 'powiązanie'
        Lr['SIECIOWY'] = Lr.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['15']).lower() or 'powiązanie' in str(row['18']).lower() 
                                        or 'powiązanie' in str(row['20']).lower() or 'powiązanie' in str(row['22']).lower() or 'powiązanie' in str(row['25']).lower() else '', axis=1)
        Cr['SIECIOWY'] = Cr.apply(lambda row: 'SIECIOWY' if 'powiązanie' in str(row['15']).lower() or 'powiązanie' in str(row['18']).lower() 
                                        or 'powiązanie' in str(row['20']).lower() or 'powiązanie' in str(row['22']).lower() or 'powiązanie' in str(row['25']).lower() else '', axis=1)

        Lr['15_percent'] = Lr['15'].apply(extract_percentage)
        Lr['18_percent'] = Lr['18'].apply(extract_percentage)
        Lr['20_percent'] = Lr['20'].apply(extract_percentage)
        Lr['22_percent'] = Lr['22'].apply(extract_percentage)
        Lr['25_percent'] = Lr['25'].apply(extract_percentage)

        Cr['15_percent'] = Cr['15'].apply(extract_percentage)
        Cr['18_percent'] = Cr['18'].apply(extract_percentage)
        Cr['20_percent'] = Cr['20'].apply(extract_percentage)
        Cr['22_percent'] = Cr['22'].apply(extract_percentage)
        Cr['25_percent'] = Cr['25'].apply(extract_percentage)


        # na zmiennoprzecinkowe
        Lr['15_percent'] = Lr['15_percent'].apply(percentage_to_float)
        Lr['18_percent'] = Lr['18_percent'].apply(percentage_to_float)
        Lr['20_percent'] = Lr['20_percent'].apply(percentage_to_float)
        Lr['22_percent'] = Lr['22_percent'].apply(percentage_to_float)
        Lr['25_percent'] = Lr['25_percent'].apply(percentage_to_float)
        
        Cr['15_percent'] = Cr['15_percent'].apply(percentage_to_float)
        Cr['18_percent'] = Cr['18_percent'].apply(percentage_to_float)
        Cr['20_percent'] = Cr['20_percent'].apply(percentage_to_float)
        Cr['22_percent'] = Cr['22_percent'].apply(percentage_to_float)
        Cr['25_percent'] = Cr['25_percent'].apply(percentage_to_float)

    
        # Dodaj nową kolumnę 'max_percent'
        Lr1 = Lr[Lr['SIECIOWY'] == 'SIECIOWY']
        Lr2 = Lr[Lr['SIECIOWY'] != 'SIECIOWY']
        Lr1['max_percent'] = Lr1[['15_percent', '18_percent', '20_percent','22_percent','25_percent']].max(axis=1)
        Lr2['max_percent'] = Lr2[['15_percent', '18_percent', '20_percent','22_percent','25_percent']].max(axis=1)

        Cr1 = Cr[Cr['SIECIOWY'] == 'SIECIOWY']
        Cr2 = Cr[Cr['SIECIOWY'] != 'SIECIOWY']
        Cr1['max_percent'] = Cr1[['15_percent', '18_percent', '20_percent','22_percent','25_percent']].max(axis=1)
        Cr2['max_percent'] = Cr2[['15_percent', '18_percent', '20_percent','22_percent','25_percent']].max(axis=1)

        ###### 1 to SIECIOWI, 2 to punkt dostaw
        Lr1 = Lr1[['KLIENT','Kod klienta','max_percent']]
        Cr1 = Cr1[['KLIENT','Kod klienta','max_percent']]

        Lr2 = Lr2[['Kod klienta','max_percent']]
        Cr2 = Cr2[['Kod klienta','max_percent']]
        
        stand_lr = Lr2
        stand_cr= Cr2
        pow_lr = Lr1
        pow_cr = Cr1



        
        #TERAZ IMS
        ims = st.file_uploader(
            label = "Wrzuć plik ims_nhd"
        )
    
        if ims:
            ims = pd.read_excel(ims, usecols=[0,2,19,21])
            st.write(ims.head())
    
        ims = ims[ims['APD_Czy_istnieje_na_rynku']==1]
        ims = ims[ims['APD_Rodzaj_farmaceutyczny'].isin(['AP - Apteka','ME - Sklep zielarsko - medyczny','PU - Punkt apteczny'])]
    
        wynik_df_lr = pd.merge(pow_lr, ims, left_on='KLIENT', right_on='Klient', how='left')
        wynik_df_cr = pd.merge(pow_cr, ims, left_on='KLIENT', right_on='Klient', how='left')
    
        # Wybór potrzebnych kolumn: 'APD_kod_SAP_apteki' i 'max_percent'
        wynik_df_lr = wynik_df_lr[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
        wynik_df_cr = wynik_df_cr[['KLIENT','APD_kod_SAP_apteki', 'max_percent']]
    
        #to są kody SAP
        wynik_df1_lr = wynik_df_lr.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
        wynik_df1_lr = wynik_df1_lr[['Kod klienta','max_percent']]

        wynik_df1_cr = wynik_df_cr.rename(columns={'APD_kod_SAP_apteki': 'Kod klienta'})
        wynik_df1_cr = wynik_df1_cr[['Kod klienta','max_percent']]
        #wynik_df1
    
        #to są kody powiazan
        wynik_df2_lr = wynik_df_lr.rename(columns={'KLIENT': 'Kod klienta'})
        wynik_df2_lr = wynik_df2_lr[['Kod klienta','max_percent']]

        wynik_df2_cr = wynik_df_cr.rename(columns={'KLIENT': 'Kod klienta'})
        wynik_df2_cr = wynik_df2_cr[['Kod klienta','max_percent']]
        #wynik_df2

        #POŁĄCZYĆ wynik_df z standard_ost
        polaczone_lr = pd.concat([stand_lr, wynik_df1_lr, wynik_df2_lr], axis = 0)
        polaczone_cr = pd.concat([stand_cr, wynik_df1_cr, wynik_df2_cr], axis = 0)
  
        posortowane_lr = polaczone_lr.sort_values(by='max_percent', ascending=False)
        posortowane_cr = polaczone_cr.sort_values(by='max_percent', ascending=False)

        ostatecznie_lr = posortowane_lr.drop_duplicates(subset='Kod klienta')
        ostatecznie_lr = ostatecznie_lr[ostatecznie_lr['max_percent'] != 0]

        ostatecznie_cr = posortowane_cr.drop_duplicates(subset='Kod klienta')
        ostatecznie_cr = ostatecznie_cr[ostatecznie_cr['max_percent'] != 0]
        
        st.write('Jeśli to pierwszy monitoring, pobierz ten plik, jeśli nie, wrzuć plik z poprzedniego monitoringu i NIE POBIERAJ TEGO PLIKU')
        excel_file = io.BytesIO()

        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        # Jeśli dane BRAZOFLAMIN istnieją, zapisz je w odpowiednim arkuszu
            if 'ostatecznie_lr' in locals():
                ostatecznie_lr.to_excel(writer, index=False, sheet_name='Levalergedd_rabat')

        # Jeśli dane diazepam istnieją, zapisz je w odpowiednim arkuszu
            if 'ostatecznie_cr' in locals():
                ostatecznie_cr.to_excel(writer, index=False, sheet_name='Cetalergedd_rabat')

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
        if 'Levalergedd_rabat' in xls.sheet_names:
            poprzedni_lr = pd.read_excel(poprzedni, sheet_name='Levalergedd_rabat')
            st.write('Poprzedni monitoring - Levalergedd_rabat:')
            st.write(poprzedni_lr.head())
        
        if 'Cetalergedd_rabat' in xls.sheet_names:
            poprzedni_cr = pd.read_excel(poprzedni, sheet_name='Cetalergedd_rabat')
            st.write('Poprzedni monitoring - Cetalergedd_rabat:')
            st.write(poprzedni_cr.head())

        # Przetwarzanie 
        if 'ostatecznie_lr' in locals() and 'poprzedni_lr' in locals():
            poprzedni_lr = poprzedni_lr.rename(columns={'max_percent': 'old_percent'})
            result_lr = ostatecznie_lr.merge(poprzedni_lr[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
            result_lr['old_percent'] = result_lr['old_percent'].fillna(0)
            result_lr['Czy dodać'] = result_lr.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)
        
            # Przetwarzanie 
        if 'ostatecznie_cr' in locals() and 'poprzedni_cr' in locals():
            poprzedni_cr = poprzedni_cr.rename(columns={'max_percent': 'old_percent'})
            result_cr = ostatecznie_cr.merge(poprzedni_cr[['Kod klienta', 'old_percent']], on='Kod klienta', how='left')
            result_cr['old_percent'] = result_cr['old_percent'].fillna(0)
            result_cr['Czy dodać'] = result_cr.apply(lambda row: 'DODAJ' if row['max_percent'] > row['old_percent'] else '', axis=1)

        # Zapisywanie plików do Excela
        excel_file1 = io.BytesIO()
        with pd.ExcelWriter(excel_file1, engine='xlsxwriter') as writer:
            if 'result_lr' in locals():
                result_lr.to_excel(writer, index=False, sheet_name='Levalergedd_rabat')
            if 'result_cr' in locals():
                result_cr.to_excel(writer, index=False, sheet_name='Cetalergedd_rabat')


        excel_file1.seek(0)  # Resetowanie wskaźnika do początku pliku

        # Definiowanie nazwy pliku
        nazwa_pliku = f"ALERGIA_{dzisiejsza_data}.xlsx"
        # Umożliwienie pobrania pliku Excel
        st.download_button(
            label='Kliknij aby pobrać plik z kodami, które kody należy dodać',
            data=excel_file1,
            file_name=nazwa_pliku,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        result_lr = result_lr.drop(columns=['old_percent', 'Czy dodać'])
        result_cr = result_cr.drop(columns=['old_percent', 'Czy dodać'])

        st.write('Kliknij, aby pobrać plik z formułą max do następnego monitoringu')

        # Tworzenie pliku Excel w pamięci
        excel_file2 = io.BytesIO()
    
        # Zapis do pliku Excel w pamięci
        with pd.ExcelWriter(excel_file2, engine='xlsxwriter') as writer:
            result_lr.to_excel(writer, index=False, sheet_name='Levalergedd_rabat')
            result_cr.to_excel(writer, index=False, sheet_name='Cetalergedd_rabat')


        # Resetowanie wskaźnika do początku pliku
        excel_file2.seek(0) 
    
        # Definiowanie nazwy pliku
        nazwa_pliku = f"FM_ALERGIA_{dzisiejsza_data}.xlsx"
    
        # Umożliwienie pobrania pliku Excel
        st.download_button(
            label='Pobierz nowy plik FORMUŁA MAX',
            data=excel_file2,
            file_name=nazwa_pliku,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


              
                
                
            
    
    
            

    

        






    
    























    
